package main

import (
	"bytes"
	"flag"
	"fmt"
	"io"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"text/template"

	"google.golang.org/protobuf/compiler/protogen"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
	"google.golang.org/protobuf/types/pluginpb"
)

var (
	Version = "(unknown)"

	SupportedFeatures = uint64(pluginpb.CodeGeneratorResponse_FEATURE_PROTO3_OPTIONAL)
	matchFirstCap     = regexp.MustCompile("([a-z0-9])([A-Z])")
	matchAllCap       = regexp.MustCompile("([A-Z])([A-Z][a-z])")

	tmpl *template.Template
)

// pyQuote produces a Python string literal for s. It uses single-quote
// delimiters when s contains double quotes but no single quotes, to avoid
// unnecessary backslash escaping (matches ruff's preferred style).
func pyQuote(s string) string {
	q := fmt.Sprintf("%q", s)
	if strings.Contains(s, `"`) && !strings.Contains(s, "'") {
		inner := q[1 : len(q)-1]
		inner = strings.ReplaceAll(inner, `\"`, `"`)
		return "'" + inner + "'"
	}
	return q
}

// pyQuoteSingle produces a single-quoted Python string literal for s.
// Needed to embed string values inside double-quoted type annotation strings
// (e.g. inside Literal[...]) without breaking the outer delimiter.
func pyQuoteSingle(s string) string {
	q := fmt.Sprintf("%q", s)                    // double-quoted Go literal, e.g. "fixed"
	inner := q[1 : len(q)-1]                     // strip outer double-quotes: fixed
	inner = strings.ReplaceAll(inner, `\"`, `"`) // unescape \"
	inner = strings.ReplaceAll(inner, `'`, `\'`) // escape any single quotes
	return "'" + inner + "'"
}

// formatScalarLiteral formats a scalar protoreflect.Value as a Python literal
// suitable for embedding in type annotations (single-quoted strings for strings).
// Returns "" for unsupported kinds (bytes, float, double, messages, enums) so
// callers fall through to dropped-constraint comments. Float/double are excluded
// because Python's Literal[] type does not accept float values (PEP 586).
func formatScalarLiteral(fd protoreflect.FieldDescriptor, v protoreflect.Value) string {
	switch fd.Kind() {
	case protoreflect.StringKind:
		return pyQuoteSingle(v.String())
	case protoreflect.BoolKind:
		if v.Bool() {
			return "True"
		}
		return "False"
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		return fmt.Sprintf("%d", v.Int())
	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return fmt.Sprintf("%d", v.Uint())
	default:
		return "" // float, double, bytes, messages, enums — unsupported
	}
}

func init() {
	tmpl = template.Must(template.New("pydantic").Funcs(template.FuncMap{
		"pyQuote": pyQuote,
	}).Parse(modelTemplate))
}

func main() {
	var flags flag.FlagSet
	preservingProtoFieldName := flags.Bool("preserving_proto_field_name", true, "")
	autoTrimEnumPrefix := flags.Bool("auto_trim_enum_prefix", true, "")
	useIntegersForEnums := flags.Bool("use_integers_for_enums", false, "")
	disableFieldDescription := flags.Bool("disable_field_description", false, "")
	useNoneUnionSyntaxInsteadOfOptional := flags.Bool("use_none_union_syntax_instead_of_optional", true, "")

	opts := protogen.Options{
		ParamFunc: flags.Set,
	}
	opts.Run(func(gen *protogen.Plugin) error {
		gen.SupportedFeatures = SupportedFeatures

		e := NewGenerator(GeneratorConfig{
			PreservingProtoFieldName:            *preservingProtoFieldName,
			AutoTrimEnumPrefix:                  *autoTrimEnumPrefix,
			UseIntegersForEnums:                 *useIntegersForEnums,
			DisableFieldDescription:             *disableFieldDescription,
			UseNoneUnionSyntaxInsteadOfOptional: *useNoneUnionSyntaxInsteadOfOptional,
		})
		e.resolver = buildEnumValueOptionsResolver(gen)
		e.customOptionFields = buildCustomOptionFields(gen)
		e.fieldConstraintExt = buildFieldConstraintExt(gen)

		leafDirs := map[string]bool{}
		protoTypeDirs := map[string]map[string]bool{}
		for _, f := range gen.Files {
			if !f.Generate {
				continue
			}

			e.reset()
			if err := e.processFile(f.Desc, f.Proto); err != nil {
				return fmt.Errorf("processing %s: %w", f.Desc.Path(), err)
			}

			filename := f.GeneratedFilenamePrefix + "_pydantic.py"
			g := gen.NewGeneratedFile(filename, f.GoImportPath)
			if err := e.Generate(g); err != nil {
				return fmt.Errorf("failed to write to %s: %w", filename, err)
			}

			dir := filepath.Dir(f.GeneratedFilenamePrefix)
			leafDirs[dir] = true
			if len(e.runtimeImports) > 0 {
				if protoTypeDirs[dir] == nil {
					protoTypeDirs[dir] = map[string]bool{}
				}
				for name := range e.runtimeImports {
					protoTypeDirs[dir][name] = true
				}
			}
		}

		for dir := range leafDirs {
			initPath := filepath.Join(dir, "__init__.py")
			g := gen.NewGeneratedFile(initPath, "")
			g.P("# Generated by protoc-gen-pydantic.")
		}

		for dir, needed := range protoTypeDirs {
			path := filepath.Join(dir, "_proto_types.py")
			g := gen.NewGeneratedFile(path, "")
			g.P(strings.TrimRight(buildProtoTypesContent(needed), "\n"))
		}

		return nil
	})
}

// Template for Pydantic model
const modelTemplate = `# DO NOT EDIT. Generated by protoc-gen-pydantic.
{{- $config := .Config -}}
{{- $hasEnumOptions := .HasEnumOptions -}}
{{- $customOptionFields := .CustomOptionFields -}}
{{- if .File.LeadingComments }}
"""
{{- range .File.LeadingComments }}
{{ . }}
{{- end }}
"""
{{- end }}
{{ if .StdImports._Enum }}
from enum import Enum as _Enum
{{- end }}
{{- if $hasEnumOptions }}
from dataclasses import dataclass as _dataclass
{{- end }}
{{- if .TypingImportLine }}
{{ .TypingImportLine }}
{{- end }}
{{- if .PydanticImportLine }}

{{ .PydanticImportLine }}
{{- end }}
{{- if .RuntimeImportLine }}

{{ .RuntimeImportLine }}
{{- end }}
{{- range .RelativeImports }}

{{ . }}
{{- end }}
{{- range .ExternalImports }}

{{ . }}
{{- end }}
{{- if .StdImports._BaseModel }}


class _ProtoModel(_BaseModel):
    """Base class for generated Pydantic models with ProtoJSON helpers."""

    def to_proto_dict(self, **kwargs) -> dict:
        """Serialize to a dict using ProtoJSON conventions.

        Omits fields with default (zero) values and uses original proto
        field names (camelCase aliases).
        """
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)

    def to_proto_json(self, **kwargs) -> str:
        """Serialize to a JSON string using ProtoJSON conventions.

        Omits fields with default (zero) values and uses original proto
        field names (camelCase aliases).
        """
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump_json(**kwargs)

    @classmethod
    def from_proto_dict(cls, data: dict, **kwargs):
        """Deserialize from a dict using ProtoJSON conventions."""
        return cls.model_validate(data, **kwargs)

    @classmethod
    def from_proto_json(cls, json_str: str, **kwargs):
        """Deserialize from a JSON string using ProtoJSON conventions."""
        return cls.model_validate_json(json_str, **kwargs)
{{- end }}
{{- if $hasEnumOptions }}


@_dataclass(frozen=True)
class _EnumValueOptions:
    number: int
    deprecated: bool = False
    debug_redact: bool = False
{{- range $customOptionFields }}
    {{ .Name }}: {{ .PythonType }} | None = None
{{- end }}


class _ProtoEnum({{ if $config.UseIntegersForEnums }}int{{ else }}str{{ end }}, _Enum):
    _options_: _EnumValueOptions

    def __new__(cls, value: {{ if $config.UseIntegersForEnums }}int{{ else }}str{{ end }}, options: _EnumValueOptions | None = None):
        obj = {{ if $config.UseIntegersForEnums }}int{{ else }}str{{ end }}.__new__(cls, value)
        obj._value_ = value
        if options is not None:
            obj._options_ = options
        return obj

    @property
    def options(self) -> _EnumValueOptions:
        return self._options_
{{- end }}
{{- range .Enums }}


class {{ .Name }}({{ if .HasOptions }}_ProtoEnum{{ else }}{{ if $config.UseIntegersForEnums }}int{{ else }}str{{ end }}, _Enum{{ end }}):
    {{- if .LeadingComments }}
    """
    {{- range .LeadingComments }}
    {{ . }}
    {{- end }}
    """
    {{- else }}
    """ """
    {{- end }}
    {{- if .TrailingComments }}
    {{ range .TrailingComments }}
    # {{ . }}
    {{- end }}
    {{- end }}
    {{- range .Values }}
    {{ range .LeadingComments }}
    # {{ . }}
    {{- end }}
    {{- if .EnumHasOptions }}
    {{- if .SortedCustomOptions }}
    {{- if $config.UseIntegersForEnums }}
    {{ .Name }} = (
        {{ .Number }},
        _EnumValueOptions(
            number={{ .Number }},
{{- if .Deprecated }}
            deprecated=True,
{{- end }}
{{- if .DebugRedact }}
            debug_redact=True,
{{- end }}
{{- range .SortedCustomOptions }}
            {{ .Key }}={{ .Value }},
{{- end }}
        ),
    )  # {{ .Name }}
    {{- else }}
    {{ .Name }} = (
        "{{ .Name }}",
        _EnumValueOptions(
            number={{ .Number }},
{{- if .Deprecated }}
            deprecated=True,
{{- end }}
{{- if .DebugRedact }}
            debug_redact=True,
{{- end }}
{{- range .SortedCustomOptions }}
            {{ .Key }}={{ .Value }},
{{- end }}
        ),
    )  # {{ .Number }}
    {{- end }}
    {{- else }}
    {{- if $config.UseIntegersForEnums }}
    {{ .Name }} = (
        {{ .Number }},
        _EnumValueOptions(number={{ .Number }}{{ if .Deprecated }}, deprecated=True{{ end }}{{ if .DebugRedact }}, debug_redact=True{{ end }}),
    )  # {{ .Name }}
    {{- else }}
    {{ .Name }} = (
        "{{ .Name }}",
        _EnumValueOptions(number={{ .Number }}{{ if .Deprecated }}, deprecated=True{{ end }}{{ if .DebugRedact }}, debug_redact=True{{ end }}),
    )  # {{ .Number }}
    {{- end }}
    {{- end }}
    {{- else }}
    {{- if $config.UseIntegersForEnums }}
    {{ .Name }} = {{ .Number }}  # {{ .Name }}
    {{- else }}
    {{ .Name }} = "{{ .Name }}"  # {{ .Number }}
    {{- end }}
    {{- end }}
    {{- range .TrailingComments }}
    # {{ . }}
    {{- end }}
    {{- end }}
{{- end }}
{{- range .Messages }}


class {{ .Name }}(_ProtoModel):
    """
    {{- range .LeadingComments }}
    {{ . }}
    {{- end }}

    Attributes:
    {{- range .Fields }}
      {{ .Name }} ({{ .Type }}):
    {{- range .LeadingComments }}
        {{ . }}
    {{- end }}
    {{- end }}
    """
    {{- if .HasModelConfig }}

    model_config = _ConfigDict(
        {{- if .HasAlias }}
        populate_by_name=True,
        {{- end }}
        ser_json_bytes="base64",
        val_json_bytes="base64",
        ser_json_inf_nan="strings",
    )
    {{- end }}
    {{- range $i, $v := .TrailingComments }}{{ if eq $i 0 }}
{{ end }}
    # {{ $v }}
    {{- end }}
    {{ range .Fields }}
    {{- range .LeadingComments }}
    # {{ . }}
    {{- end }}
    {{- if or (and (not $config.DisableFieldDescription) (or (ne (len .LeadingComments) 0) (ne .OneOf nil))) .Alias .IsDefaultFactory .HasConstraints }}
    {{ .Name }}: "{{ .Type }}" = _Field(
        {{ .Default }},
    {{- if and (not $config.DisableFieldDescription) (or (ne (len .LeadingComments) 0) (ne .OneOf nil)) }}
        description={{ pyQuote .Description }},
    {{- end }}
    {{- if .Alias }}
        alias="{{ .Alias }}",
    {{- end }}
    {{- range .ConstraintArgs }}
        {{ . }},
    {{- end }}
    {{- range .DroppedConstraintComments }}
        {{ . }}
    {{- end }}
    )
    {{- else }}
    {{ .Name }}: "{{ .Type }}" = _Field({{ .Default }})
    {{- end }}
    {{- range .TrailingComments }}
    # {{ . }}
    {{- end }}
    {{ end }}
    {{- if eq (len .Fields) 0 }}
    pass
    {{- end }}
{{- end }}
{{- range .File.TrailingComments }}
# {{ . }}
{{- end }}
`

// protoTypesBaseFuncs contains the always-present base function bodies for
// _proto_types.py. It starts with two newlines so that when appended directly
// after the last import/assignment line (which ends with \n), the result has
// exactly two blank lines before the first function — satisfying ruff E302.
const protoTypesBaseFuncs = `

def _coerce_int(v):
    return int(v)


ProtoInt64 = _Annotated[
    int,
    _BeforeValidator(_coerce_int),
    _PlainSerializer(lambda v: str(v), return_type=str, when_used="json"),
]

ProtoUInt64 = _Annotated[
    int,
    _BeforeValidator(_coerce_int),
    _PlainSerializer(lambda v: str(v), return_type=str, when_used="json"),
]


def _parse_timestamp(v):
    if isinstance(v, str):
        return _datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
    if isinstance(v, _datetime.datetime):
        return v
    raise ValueError(f"Cannot parse timestamp from {type(v)}")


def _serialize_timestamp(v):
    if v.tzinfo is None:
        v = v.replace(tzinfo=_datetime.timezone.utc)
    s = v.strftime("%Y-%m-%dT%H:%M:%S")
    us = v.microsecond
    if us:
        s += f".{us:06d}".rstrip("0")
    return s + "Z"


ProtoTimestamp = _Annotated[
    _datetime.datetime,
    _BeforeValidator(_parse_timestamp),
    _PlainSerializer(_serialize_timestamp, return_type=str, when_used="json"),
]


def _parse_duration(v):
    if isinstance(v, str):
        m = _re.match(r"^(-?\d+(?:\.\d+)?)s$", v)
        if not m:
            raise ValueError(f"Invalid duration: {v}")
        return _datetime.timedelta(seconds=float(m.group(1)))
    if isinstance(v, _datetime.timedelta):
        return v
    raise ValueError(f"Cannot parse duration from {type(v)}")


def _serialize_duration(v):
    total = v.total_seconds()
    if total == int(total):
        return f"{int(total)}s"
    return f"{total}s"


ProtoDuration = _Annotated[
    _datetime.timedelta,
    _BeforeValidator(_parse_duration),
    _PlainSerializer(_serialize_duration, return_type=str, when_used="json"),
]


def _require_unique(v):
    if len(v) != len(set(v)):
        raise ValueError("list items must be unique")
    return v


def _make_in_validator(valid_values):
    def _validate(v):
        if v not in valid_values:
            raise ValueError(f"value must be one of {sorted(valid_values)}")
        return v

    return _validate


def _make_not_in_validator(excluded_values):
    def _validate(v):
        if v in excluded_values:
            raise ValueError(f"value must not be one of {sorted(excluded_values)}")
        return v

    return _validate
`

// Each per-validator constant starts with two newlines so that when appended
// after content that ends with \n, the result has exactly two blank lines
// before the function definition (ruff E302).

const protoTypesEmailFunc = `

def _validate_email(v: str) -> str:
    if not v:
        return v
    from pydantic.networks import validate_email as _pydantic_validate_email

    _pydantic_validate_email(v)
    return v
`

const protoTypesURIFunc = `

def _validate_uri(v: str) -> str:
    if not v:
        return v
    _url_adapter.validate_python(v)
    return v
`

const protoTypesIPFunc = `

def _validate_ip(v: str) -> str:
    if not v:
        return v
    _ipaddress.ip_address(v)
    return v
`

const protoTypesIPv4Func = `

def _validate_ipv4(v: str) -> str:
    if not v:
        return v
    _ipaddress.IPv4Address(v)
    return v
`

const protoTypesIPv6Func = `

def _validate_ipv6(v: str) -> str:
    if not v:
        return v
    _ipaddress.IPv6Address(v)
    return v
`

const protoTypesUUIDFunc = `

def _validate_uuid(v: str) -> str:
    if not v:
        return v
    _uuid_lib.UUID(v)
    return v
`

const protoTypesFiniteFunc = `

def _require_finite(v: float) -> float:
    if not _math.isfinite(v):
        raise ValueError("value must be finite")
    return v
`

const protoTypesConstValidatorFunc = `

def _make_const_validator(c):
    def _validate(v):
        if v != c:
            raise ValueError(f"value must equal {c!r}")
        return v

    return _validate
`

// buildProtoTypesContent assembles the content for _proto_types.py, including
// only the format validator functions (and their imports) that are actually
// used by files in the same output directory.
func buildProtoTypesContent(needed map[string]bool) string {
	needIP := needed["_validate_ip"] || needed["_validate_ipv4"] || needed["_validate_ipv6"]
	needURI := needed["_validate_uri"]

	var b strings.Builder

	b.WriteString("# DO NOT EDIT. Generated by protoc-gen-pydantic.\n")

	// Stdlib imports (alphabetical).
	b.WriteString("import datetime as _datetime\n")
	if needIP {
		b.WriteString("import ipaddress as _ipaddress\n")
	}
	if needed["_require_finite"] {
		b.WriteString("import math as _math\n")
	}
	b.WriteString("import re as _re\n")
	if needed["_validate_uuid"] {
		b.WriteString("import uuid as _uuid_lib\n")
	}
	b.WriteString("from typing import Annotated as _Annotated\n")
	b.WriteString("\n")

	// Third-party imports (alphabetical within group).
	if needURI {
		b.WriteString("from pydantic import AnyUrl as _AnyUrl\n")
	}
	b.WriteString("from pydantic import BeforeValidator as _BeforeValidator\n")
	b.WriteString("from pydantic import PlainSerializer as _PlainSerializer\n")
	if needURI {
		b.WriteString("from pydantic import TypeAdapter as _TypeAdapter\n")
	}

	// Module-level declarations.
	if needURI {
		b.WriteString("\n_url_adapter = _TypeAdapter(_AnyUrl)\n")
	}

	// Always-present base functions.
	b.WriteString(protoTypesBaseFuncs)

	// Conditional format validator functions.
	if needed["_validate_email"] {
		b.WriteString(protoTypesEmailFunc)
	}
	if needURI {
		b.WriteString(protoTypesURIFunc)
	}
	if needed["_validate_ip"] {
		b.WriteString(protoTypesIPFunc)
	}
	if needed["_validate_ipv4"] {
		b.WriteString(protoTypesIPv4Func)
	}
	if needed["_validate_ipv6"] {
		b.WriteString(protoTypesIPv6Func)
	}
	if needed["_validate_uuid"] {
		b.WriteString(protoTypesUUIDFunc)
	}
	if needed["_require_finite"] {
		b.WriteString(protoTypesFiniteFunc)
	}
	if needed["_make_const_validator"] {
		b.WriteString(protoTypesConstValidatorFunc)
	}

	return b.String()
}

// reservedNames is the set of names that must not be used as Pydantic field
// names. Fields with these names are renamed with a trailing underscore and
// given an alias to preserve the original proto field name.
var reservedNames = map[string]bool{
	// Python builtins (shadow type annotations)
	"int": true, "float": true, "bool": true, "str": true, "bytes": true,
	"list": true, "dict": true, "set": true, "tuple": true, "type": true,
	"object": true, "range": true, "map": true, "filter": true,
	"id": true, "hash": true, "len": true, "max": true, "min": true,
	"sum": true, "abs": true, "round": true, "complex": true,
	"frozenset": true, "memoryview": true, "bytearray": true,
	"property": true, "classmethod": true, "staticmethod": true, "super": true,
	// Python keywords (cause SyntaxError if used as identifiers)
	"False": true, "None": true, "True": true,
	"and": true, "as": true, "assert": true, "async": true, "await": true,
	"break": true, "class": true, "continue": true, "def": true, "del": true,
	"elif": true, "else": true, "except": true, "finally": true, "for": true,
	"from": true, "global": true, "if": true, "import": true, "in": true,
	"is": true, "lambda": true, "nonlocal": true, "not": true, "or": true,
	"pass": true, "raise": true, "return": true, "try": true, "while": true,
	"with": true, "yield": true,
	// Pydantic BaseModel attributes (shadow model internals)
	"model_config": true, "model_fields": true, "model_computed_fields": true,
	"model_extra": true, "model_fields_set": true,
	"model_construct": true, "model_copy": true,
	"model_dump": true, "model_dump_json": true,
	"model_json_schema": true, "model_parametrized_name": true,
	"model_post_init": true, "model_rebuild": true,
	"model_validate": true, "model_validate_json": true,
	"model_validate_strings": true,
}

// wellKnownTypes maps protobuf well-known type full names to native Python types.
type wktMapping struct {
	pythonType  string
	importLine  string // added to external imports if non-empty
	runtimeType string // if set, imported from _proto_types instead
}

var wellKnownTypes = map[string]wktMapping{
	"google.protobuf.Timestamp":   {pythonType: "ProtoTimestamp", runtimeType: "ProtoTimestamp"},
	"google.protobuf.Duration":    {pythonType: "ProtoDuration", runtimeType: "ProtoDuration"},
	"google.protobuf.Struct":      {pythonType: "dict[str, _Any]"},
	"google.protobuf.Value":       {pythonType: "_Any"},
	"google.protobuf.ListValue":   {pythonType: "list[_Any]"},
	"google.protobuf.Empty":       {pythonType: "None"},
	"google.protobuf.FieldMask":   {pythonType: "list[str]"},
	"google.protobuf.Any":         {pythonType: "_Any"},
	"google.protobuf.BoolValue":   {pythonType: "bool"},
	"google.protobuf.Int32Value":  {pythonType: "int"},
	"google.protobuf.Int64Value":  {pythonType: "ProtoInt64", runtimeType: "ProtoInt64"},
	"google.protobuf.UInt32Value": {pythonType: "int"},
	"google.protobuf.UInt64Value": {pythonType: "ProtoUInt64", runtimeType: "ProtoUInt64"},
	"google.protobuf.FloatValue":  {pythonType: "float"},
	"google.protobuf.DoubleValue": {pythonType: "float"},
	"google.protobuf.StringValue": {pythonType: "str"},
	"google.protobuf.BytesValue":  {pythonType: "bytes"},
}

type CustomOption struct {
	Key   string
	Value string // Python literal representation
}

type CustomOptionField struct {
	Name       string // e.g. "display_name"
	PythonType string // e.g. "str", "int", "bool"
}

func protoKindToPythonType(kind protoreflect.Kind) string {
	switch kind {
	case protoreflect.BoolKind:
		return "bool"
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind,
		protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return "int"
	case protoreflect.FloatKind, protoreflect.DoubleKind:
		return "float"
	case protoreflect.StringKind:
		return "str"
	case protoreflect.BytesKind:
		return "bytes"
	default:
		return "_Any"
	}
}

type EnumValue struct {
	Name             string
	Number           int32
	Deprecated       bool
	DebugRedact      bool
	CustomOptions    map[string]interface{}
	EnumHasOptions   bool // true if parent enum has any value options
	LeadingComments  []string
	TrailingComments []string
}

func (v EnumValue) SortedCustomOptions() []CustomOption {
	if len(v.CustomOptions) == 0 {
		return nil
	}
	keys := make([]string, 0, len(v.CustomOptions))
	for k := range v.CustomOptions {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	opts := make([]CustomOption, len(keys))
	for i, k := range keys {
		opts[i] = CustomOption{Key: k, Value: pythonLiteral(v.CustomOptions[k])}
	}
	return opts
}

type Enum struct {
	Name             string
	Values           []EnumValue
	LeadingComments  []string
	TrailingComments []string
}

func (e Enum) HasOptions() bool {
	for _, v := range e.Values {
		if v.Deprecated || v.DebugRedact || len(v.CustomOptions) > 0 {
			return true
		}
	}
	return false
}

type Field struct {
	Name             string
	Alias            string // non-empty when Name was renamed to avoid shadowing Python builtins
	Type             string
	Optional         bool
	Default          string // proto3 zero-value default (e.g. "0", "False", "None", "default_factory=list")
	OneOf            *OneOf
	Constraints      *FieldConstraints
	LeadingComments  []string
	TrailingComments []string
}

func (f Field) IsDefaultFactory() bool {
	return strings.HasPrefix(f.Default, "default_factory=")
}

func (f Field) HasConstraints() bool {
	return f.Constraints != nil && f.Constraints.HasAny()
}

func (f Field) ConstraintArgs() []string {
	return f.Constraints.PydanticArgs()
}

func (f Field) DroppedConstraintComments() []string {
	return f.Constraints.DroppedConstraintComments()
}

// Description returns the field's description string for use in _Field().
// Leading comment lines are joined with newlines; the oneof annotation is
// appended (separated by a newline) when present.
func (f Field) Description() string {
	parts := make([]string, 0, len(f.LeadingComments)+1)
	parts = append(parts, f.LeadingComments...)
	if f.OneOf != nil {
		parts = append(parts, fmt.Sprintf(
			"Only one of the fields can be specified with: %v (oneof %s)",
			f.OneOf.FieldNames, f.OneOf.Name,
		))
	}
	return strings.Join(parts, "\n")
}

type OneOf struct {
	Name       string
	FieldNames []string
}

// FieldConstraints holds Tier 1 buf.validate constraints that map
// directly to Pydantic Field() kwargs, plus names of constraints that
// are recognised but not translated (emitted as comments instead).
type FieldConstraints struct {
	Gt                 *string  // exclusive lower bound, Python literal
	Gte                *string  // inclusive lower bound, Python literal
	Lt                 *string  // exclusive upper bound, Python literal
	Lte                *string  // inclusive upper bound, Python literal
	MinLength          *int64   // string.min_len / string.len / repeated.min_items / map.min_pairs
	MaxLength          *int64   // string.max_len / string.len / repeated.max_items / map.max_pairs
	Pattern            *string  // string.pattern regex (may be derived from Prefix/Suffix)
	Prefix             *string  // string.prefix — intermediate; resolved into Pattern by combinePatternConstraints
	Suffix             *string  // string.suffix — intermediate; resolved into Pattern by combinePatternConstraints
	Examples           []string // field examples as Python literals for Field(examples=[...])
	DroppedConstraints []string // constraint names not translated (required, cel, ...)
	ConstLiteral       *string  // Python literal for Literal[...] (single-quoted string for strings)
	ConstDefault       *string  // Python literal for _Field(...) default (double-quoted for strings)
	InValues           []string // Python literals for AfterValidator in-set
	NotInValues        []string // Python literals for AfterValidator exclusion-set
	UniqueItems        bool     // true when repeated.unique = true
	FormatValidator    *string  // one of: "email", "uri", "ip", "ipv4", "ipv6", "uuid"
	RequireFinite      bool     // true when float/double.finite = true
	Contains           *string  // string.contains substring — intermediate; resolved into Pattern by combinePatternConstraints
	ConstFloatLiteral  *string  // Python float literal for float/double const (Literal[] is invalid per PEP 586)
}

func (c *FieldConstraints) HasAny() bool {
	if c == nil {
		return false
	}
	return c.ConstLiteral != nil || c.ConstFloatLiteral != nil || c.RequireFinite ||
		len(c.InValues) > 0 || len(c.NotInValues) > 0 || c.UniqueItems ||
		c.Gt != nil || c.Gte != nil || c.Lt != nil || c.Lte != nil ||
		c.MinLength != nil || c.MaxLength != nil || c.Pattern != nil || c.Contains != nil ||
		len(c.Examples) > 0 || c.FormatValidator != nil ||
		len(c.DroppedConstraints) > 0
}

// PydanticArgs returns ["gt=0", "le=150", ...] to inject into _Field().
func (c *FieldConstraints) PydanticArgs() []string {
	if c == nil {
		return nil
	}
	var args []string
	if c.Gte != nil {
		args = append(args, fmt.Sprintf("ge=%s", *c.Gte))
	}
	if c.Gt != nil {
		args = append(args, fmt.Sprintf("gt=%s", *c.Gt))
	}
	if c.Lte != nil {
		args = append(args, fmt.Sprintf("le=%s", *c.Lte))
	}
	if c.Lt != nil {
		args = append(args, fmt.Sprintf("lt=%s", *c.Lt))
	}
	if c.MinLength != nil {
		args = append(args, fmt.Sprintf("min_length=%d", *c.MinLength))
	}
	if c.MaxLength != nil {
		args = append(args, fmt.Sprintf("max_length=%d", *c.MaxLength))
	}
	if c.Pattern != nil {
		args = append(args, fmt.Sprintf("pattern=%s", pyQuote(*c.Pattern)))
	}
	if len(c.Examples) > 0 {
		args = append(args, fmt.Sprintf("examples=[%s]", strings.Join(c.Examples, ", ")))
	}
	return args
}

// DroppedConstraintComments returns a Python comment string for each
// constraint that was recognised but could not be translated.
func (c *FieldConstraints) DroppedConstraintComments() []string {
	if c == nil || len(c.DroppedConstraints) == 0 {
		return nil
	}
	comments := make([]string, len(c.DroppedConstraints))
	for i, name := range c.DroppedConstraints {
		comments[i] = fmt.Sprintf("# buf.validate: %s (not translated)", name)
	}
	return comments
}

// combinePatternConstraints merges Prefix and Suffix into Pattern (or drops
// them to DroppedConstraints if an explicit Pattern is already set). Must be
// called after iterating all sub-message rule fields so that all three fields
// are populated before combining.
func (c *FieldConstraints) combinePatternConstraints() {
	if c.Prefix == nil && c.Suffix == nil && c.Contains == nil {
		return
	}
	if c.Pattern != nil {
		// An explicit pattern is already present; we cannot combine, so drop
		// prefix/suffix/contains as untranslated comments.
		if c.Prefix != nil {
			c.DroppedConstraints = append(c.DroppedConstraints, "prefix")
			c.Prefix = nil
		}
		if c.Suffix != nil {
			c.DroppedConstraints = append(c.DroppedConstraints, "suffix")
			c.Suffix = nil
		}
		if c.Contains != nil {
			c.DroppedConstraints = append(c.DroppedConstraints, "contains")
			c.Contains = nil
		}
		return
	}
	// Build pattern from prefix/suffix first.
	if c.Prefix != nil || c.Suffix != nil {
		var pat string
		switch {
		case c.Prefix != nil && c.Suffix != nil:
			pat = "^" + regexp.QuoteMeta(*c.Prefix) + ".*" + regexp.QuoteMeta(*c.Suffix) + "$"
		case c.Prefix != nil:
			pat = "^" + regexp.QuoteMeta(*c.Prefix)
		default:
			pat = regexp.QuoteMeta(*c.Suffix) + "$"
		}
		c.Pattern = &pat
		c.Prefix = nil
		c.Suffix = nil
		// If contains is also set, it conflicts with the prefix/suffix pattern.
		if c.Contains != nil {
			c.DroppedConstraints = append(c.DroppedConstraints, "contains")
			c.Contains = nil
		}
		return
	}
	// Only contains is set — translate to an unanchored regex.
	pat := regexp.QuoteMeta(*c.Contains)
	c.Pattern = &pat
	c.Contains = nil
}

type Message struct {
	Name             string
	Fields           []Field
	LeadingComments  []string
	TrailingComments []string
}

func (m Message) TopoKey() string {
	return m.Name
}

func (m Message) HasAlias() bool {
	for _, f := range m.Fields {
		if f.Alias != "" {
			return true
		}
	}
	return false
}

func (m Message) HasModelConfig() bool {
	return true
}

type File struct {
	LeadingComments  []string
	TrailingComments []string
}

type generator struct {
	file            File
	enums           []Enum
	messages        []Message
	externalImports []string
	relativeImports []string
	stdImports      map[string]bool
	runtimeImports  map[string]bool

	customOptionFields []CustomOptionField

	config             GeneratorConfig
	resolver           *protoregistry.Types
	fieldConstraintExt protoreflect.ExtensionDescriptor
}

type GeneratorConfig struct {
	PreservingProtoFieldName            bool
	AutoTrimEnumPrefix                  bool
	UseIntegersForEnums                 bool
	DisableFieldDescription             bool
	UseNoneUnionSyntaxInsteadOfOptional bool
}

func NewGenerator(c GeneratorConfig) *generator {
	return &generator{
		config: c,
	}
}

func (e *generator) reset() {
	e.file = File{}
	e.enums = nil
	e.messages = nil
	e.externalImports = nil
	e.relativeImports = nil
	e.stdImports = map[string]bool{}
	e.runtimeImports = nil
}

func (e *generator) addRuntimeImport(name string) {
	if e.runtimeImports == nil {
		e.runtimeImports = make(map[string]bool)
	}
	e.runtimeImports[name] = true
}

func (e *generator) runtimeImportLine() string {
	if len(e.runtimeImports) == 0 {
		return ""
	}
	names := make([]string, 0, len(e.runtimeImports))
	for name := range e.runtimeImports {
		names = append(names, name)
	}
	sort.Strings(names)
	return formatImportBlock("from ._proto_types import ", names)
}

func (e *generator) hasEnumOptions() bool {
	for _, enum := range e.enums {
		if enum.HasOptions() {
			return true
		}
	}
	return false
}

func (e *generator) addStdImport(name string) {
	e.stdImports[name] = true
}

// formatImportBlock formats a Python import statement, expanding to the
// multi-line parenthesized form when the single-line form would exceed
// 88 characters (ruff's default line length).
func formatImportBlock(prefix string, symbols []string) string {
	oneLine := prefix + strings.Join(symbols, ", ")
	if len(oneLine) <= 88 {
		return oneLine
	}
	var sb strings.Builder
	sb.WriteString(prefix + "(\n")
	for _, sym := range symbols {
		sb.WriteString("    " + sym + ",\n")
	}
	sb.WriteString(")")
	return sb.String()
}

// typingImportLine returns a complete `from typing import ...` statement,
// or "" when nothing from typing is needed.
func (e *generator) typingImportLine() string {
	var symbols []string
	if e.stdImports["_Annotated"] {
		symbols = append(symbols, "Annotated as _Annotated")
	}
	if e.stdImports["_Any"] {
		symbols = append(symbols, "Any as _Any")
	}
	if e.stdImports["_Literal"] {
		symbols = append(symbols, "Literal as _Literal")
	}
	if e.stdImports["_Optional"] {
		symbols = append(symbols, "Optional as _Optional")
	}
	if len(symbols) == 0 {
		return ""
	}
	return formatImportBlock("from typing import ", symbols)
}

// pydanticImportLine returns a complete `from pydantic import ...` statement,
// or "" when _BaseModel is not needed (i.e. no messages in the file).
func (e *generator) pydanticImportLine() string {
	if !e.stdImports["_BaseModel"] {
		return ""
	}
	var symbols []string
	if e.stdImports["_AfterValidator"] {
		symbols = append(symbols, "AfterValidator as _AfterValidator")
	}
	symbols = append(symbols, "BaseModel as _BaseModel", "ConfigDict as _ConfigDict", "Field as _Field")
	return formatImportBlock("from pydantic import ", symbols)
}

// wrapWithAnnotated wraps a type string with _Annotated[..., validators],
// preserving `| None` and `_Optional[...]` wrappers correctly.
func wrapWithAnnotated(typ string, validators []string) string {
	vStr := strings.Join(validators, ", ")
	if strings.HasSuffix(typ, " | None") {
		inner := strings.TrimSuffix(typ, " | None")
		return "_Annotated[" + inner + ", " + vStr + "] | None"
	}
	if strings.HasPrefix(typ, "_Optional[") && strings.HasSuffix(typ, "]") {
		inner := typ[len("_Optional[") : len(typ)-1]
		return "_Optional[_Annotated[" + inner + ", " + vStr + "]]"
	}
	return "_Annotated[" + typ + ", " + vStr + "]"
}

// applyConstraintTypeOverrides modifies f.Type (and f.Default for const) based
// on FieldConstraints that require type-level changes rather than Field() kwargs.
func (e *generator) applyConstraintTypeOverrides(f *Field) {
	fc := f.Constraints
	if fc == nil {
		return
	}

	// const → Literal type override
	if fc.ConstLiteral != nil {
		litType := "_Literal[" + *fc.ConstLiteral + "]"
		switch {
		case strings.HasSuffix(f.Type, " | None"):
			f.Type = litType + " | None"
		case strings.HasPrefix(f.Type, "_Optional[") && strings.HasSuffix(f.Type, "]"):
			f.Type = "_Optional[" + litType + "]"
		default:
			f.Type = litType
			f.Default = *fc.ConstDefault
		}
	}

	// in/not_in/unique → AfterValidator wrapping
	var validators []string
	if len(fc.InValues) > 0 {
		v := "{" + strings.Join(fc.InValues, ", ") + "}"
		validators = append(validators, "_AfterValidator(_make_in_validator(frozenset("+v+")))")
		e.addRuntimeImport("_make_in_validator")
	}
	if len(fc.NotInValues) > 0 {
		v := "{" + strings.Join(fc.NotInValues, ", ") + "}"
		validators = append(validators, "_AfterValidator(_make_not_in_validator(frozenset("+v+")))")
		e.addRuntimeImport("_make_not_in_validator")
	}
	if fc.UniqueItems {
		validators = append(validators, "_AfterValidator(_require_unique)")
		e.addRuntimeImport("_require_unique")
	}
	if fc.FormatValidator != nil {
		helperName := "_validate_" + *fc.FormatValidator
		validators = append(validators, "_AfterValidator("+helperName+")")
		e.addRuntimeImport(helperName)
	}
	if fc.RequireFinite {
		validators = append(validators, "_AfterValidator(_require_finite)")
		e.addRuntimeImport("_require_finite")
	}
	if fc.ConstFloatLiteral != nil {
		validators = append(validators, "_AfterValidator(_make_const_validator("+*fc.ConstFloatLiteral+"))")
		e.addRuntimeImport("_make_const_validator")
		// Set the field default to the const value (only for non-optional fields).
		if fc.ConstDefault != nil &&
			!strings.HasSuffix(f.Type, " | None") &&
			!strings.HasPrefix(f.Type, "_Optional[") {
			f.Default = *fc.ConstDefault
		}
	}
	if len(validators) > 0 {
		f.Type = wrapWithAnnotated(f.Type, validators)
	}
}

func (e *generator) Generate(w io.Writer) error {
	var buf bytes.Buffer
	hasEnumOptions := e.hasEnumOptions()
	runtimeImportLine := e.runtimeImportLine()
	typingImportLine := e.typingImportLine()
	pydanticImportLine := e.pydanticImportLine()
	err := tmpl.Execute(&buf, struct {
		File               File
		Enums              []Enum
		Messages           []Message
		ExternalImports    []string
		RelativeImports    []string
		Config             GeneratorConfig
		StdImports         map[string]bool
		HasEnumOptions     bool
		CustomOptionFields []CustomOptionField
		RuntimeImportLine  string
		TypingImportLine   string
		PydanticImportLine string
	}{
		e.file,
		e.enums,
		e.messages,
		e.externalImports,
		e.relativeImports,
		e.config,
		e.stdImports,
		hasEnumOptions,
		e.customOptionFields,
		runtimeImportLine,
		typingImportLine,
		pydanticImportLine,
	})
	if err != nil {
		return err
	}

	// Post-process: strip trailing whitespace from each line.
	output := buf.String()
	lines := strings.Split(output, "\n")
	for i, line := range lines {
		lines[i] = strings.TrimRight(line, " \t")
	}
	output = strings.Join(lines, "\n")

	// Collapse 3+ consecutive blank lines to exactly 2.
	for strings.Contains(output, "\n\n\n\n") {
		output = strings.ReplaceAll(output, "\n\n\n\n", "\n\n\n")
	}

	// Ensure file ends with exactly one newline.
	output = strings.TrimRight(output, "\n") + "\n"

	_, err = io.WriteString(w, output)
	return err
}

func (e *generator) processFile(file protoreflect.FileDescriptor, fdp *descriptorpb.FileDescriptorProto) error {
	def := File{}
	sourceCodeInfo := fdp.GetSourceCodeInfo()
	path := []int32{12}
	def.LeadingComments, def.TrailingComments = extractComments(sourceCodeInfo, path)
	e.file = def

	for i := range file.Enums().Len() {
		ed := file.Enums().Get(i)
		ep := fdp.GetEnumType()[i]
		path := []int32{5, int32(i)}
		if err := e.processEnum(ed, ep, sourceCodeInfo, path); err != nil {
			return err
		}
	}
	for i := range file.Messages().Len() {
		msgd := file.Messages().Get(i)
		msgp := fdp.GetMessageType()[i]
		path := []int32{4, int32(i)}
		if err := e.processMessage(msgd, msgp, sourceCodeInfo, path); err != nil {
			return err
		}
	}
	return nil
}

func (e *generator) processEnum(
	enum protoreflect.EnumDescriptor,
	enumProto *descriptorpb.EnumDescriptorProto,
	sourceCodeInfo *descriptorpb.SourceCodeInfo,
	path []int32,
) error {
	def := Enum{
		Name:   resolveName(enum),
		Values: []EnumValue{},
	}
	def.LeadingComments, def.TrailingComments = extractComments(sourceCodeInfo, path)

	prefix := camelToSnakeCase(string(enum.Name())) + "_"
	for i := range enum.Values().Len() {
		v := enum.Values().Get(i)
		valueName := string(v.Name())
		if e.config.AutoTrimEnumPrefix {
			valueName = strings.TrimPrefix(valueName, prefix)
		}
		fieldPath := append(append([]int32{}, path...), 2, int32(i))
		leadingComments, trailingComments := extractComments(sourceCodeInfo, fieldPath)

		var deprecated, debugRedact bool
		var customOpts map[string]interface{}
		if vp := enumProto.GetValue()[i]; vp.GetOptions() != nil {
			deprecated = vp.GetOptions().GetDeprecated()
			debugRedact = vp.GetOptions().GetDebugRedact()
			customOpts = e.extractCustomOptions(vp.GetOptions())
		}

		def.Values = append(def.Values, EnumValue{
			Name:             valueName,
			Number:           int32(v.Number()),
			Deprecated:       deprecated,
			DebugRedact:      debugRedact,
			CustomOptions:    customOpts,
			LeadingComments:  leadingComments,
			TrailingComments: trailingComments,
		})
	}

	// If the enum has any value options, mark all values so the template
	// can emit tuple syntax for the entire enum.
	hasCustom := false
	if def.HasOptions() {
		for i := range def.Values {
			def.Values[i].EnumHasOptions = true
			if len(def.Values[i].CustomOptions) > 0 {
				hasCustom = true
			}
		}
	}
	if hasCustom {
		for _, f := range e.customOptionFields {
			if f.PythonType == "_Any" {
				e.addStdImport("_Any")
				break
			}
		}
	}

	e.addStdImport("_Enum")
	e.enums = append(e.enums, def)
	return nil
}

func (e *generator) processMessage(
	msg protoreflect.MessageDescriptor,
	msgProto *descriptorpb.DescriptorProto,
	sourceCodeInfo *descriptorpb.SourceCodeInfo,
	path []int32,
) error {
	if msg.IsMapEntry() {
		return nil
	}

	// NOTE: Process nested enums and messages before the fields.
	for i, nest := range iter(msg.Enums()) {
		nestPath := append(append([]int32{}, path...), 4, int32(i))
		if err := e.processEnum(nest, msgProto.GetEnumType()[i], sourceCodeInfo, nestPath); err != nil {
			return fmt.Errorf("enum %s: %w", string(nest.Name()), err)
		}
	}

	for i, nest := range iter(msg.Messages()) {
		nestPath := append(append([]int32{}, path...), 3, int32(i))
		if err := e.processMessage(nest, msgProto.GetNestedType()[i], sourceCodeInfo, nestPath); err != nil {
			return fmt.Errorf("message %s: %w", string(nest.Name()), err)
		}
	}

	def := Message{
		Name:   resolveName(msg),
		Fields: []Field{},
	}
	def.LeadingComments, def.TrailingComments = extractComments(sourceCodeInfo, path)

	for i, field := range iter(msg.Fields()) {
		typ, err := e.resolveType(def.Name, field)
		if err != nil {
			return fmt.Errorf("field %s.%s: %w", def.Name, field.Name(), err)
		}
		fieldPath := append(append([]int32{}, path...), 2, int32(i))
		var oneOf *OneOf
		if oo := field.ContainingOneof(); !field.HasOptionalKeyword() && oo != nil {
			var fieldNames []string
			for _, f := range iter(oo.Fields()) {
				fieldNames = append(fieldNames, string(f.Name()))
			}
			oneOf = &OneOf{
				Name:       string(oo.Name()),
				FieldNames: fieldNames,
			}
		}
		name := field.JSONName()
		if e.config.PreservingProtoFieldName {
			name = string(field.Name())
		}
		var alias string
		if reservedNames[name] {
			alias = name
			name = name + "_"
		}
		f := Field{
			Name:     name,
			Alias:    alias,
			Type:     typ,
			Optional: field.HasOptionalKeyword(),
			Default:  e.resolveDefault(field),
			OneOf:    oneOf,
		}
		f.LeadingComments, f.TrailingComments = extractComments(sourceCodeInfo, fieldPath)
		if fp := msgProto.GetField()[i]; fp.GetOptions() != nil {
			f.Constraints = e.extractFieldConstraints(fp.GetOptions(), field)
		}
		e.applyConstraintTypeOverrides(&f)
		def.Fields = append(def.Fields, f)
	}

	e.addStdImport("_BaseModel")
	e.addStdImport("_Field")
	e.addStdImport("_ConfigDict")
	e.messages = append(e.messages, def)
	return nil
}

func (e *generator) addExternalImport(importLine string) {
	for _, imp := range e.externalImports {
		if imp == importLine {
			return
		}
	}
	e.externalImports = append(e.externalImports, importLine)
}

func (e *generator) addRelativeImport(importLine string) {
	for _, imp := range e.relativeImports {
		if imp == importLine {
			return
		}
	}
	e.relativeImports = append(e.relativeImports, importLine)
}

// addCrossFileImport adds the appropriate import statement when a type from
// targetFile is referenced from sourceFile. No import is added for same-file
// references. Same-package cross-file uses relative imports; cross-package
// uses absolute imports.
func (e *generator) addCrossFileImport(sourceFile, targetFile protoreflect.FileDescriptor, typeName string) error {
	if sourceFile.Path() == targetFile.Path() {
		return nil
	}
	targetPath := string(targetFile.Path())
	moduleName := strings.TrimSuffix(filepath.Base(targetPath), ".proto") + "_pydantic"
	if string(sourceFile.Package()) == string(targetFile.Package()) {
		e.addRelativeImport(fmt.Sprintf("from .%s import %s", moduleName, typeName))
	} else {
		// Use the file path (not package name) to derive the Python module path.
		dir := filepath.Dir(targetPath)
		pyPkg := strings.ReplaceAll(dir, string(filepath.Separator), ".")
		e.addExternalImport(fmt.Sprintf("from %s.%s import %s", pyPkg, moduleName, typeName))
	}
	return nil
}

func (e *generator) resolveBaseType(referer string, field protoreflect.FieldDescriptor) (string, error) {
	switch field.Kind() {
	case
		protoreflect.Int32Kind,
		protoreflect.Uint32Kind,
		protoreflect.Fixed32Kind,
		protoreflect.Sint32Kind,
		protoreflect.Sfixed32Kind:
		return "int", nil
	case
		protoreflect.Int64Kind,
		protoreflect.Sint64Kind,
		protoreflect.Sfixed64Kind:
		e.addRuntimeImport("ProtoInt64")
		return "ProtoInt64", nil
	case
		protoreflect.Uint64Kind,
		protoreflect.Fixed64Kind:
		e.addRuntimeImport("ProtoUInt64")
		return "ProtoUInt64", nil
	case protoreflect.BoolKind:
		return "bool", nil
	case protoreflect.DoubleKind,
		protoreflect.FloatKind:
		return "float", nil
	case protoreflect.StringKind:
		return "str", nil
	case protoreflect.BytesKind:
		return "bytes", nil
	case protoreflect.MessageKind:
	case protoreflect.EnumKind:
		enum := field.Enum()
		typeName := resolveName(enum)
		if err := e.addCrossFileImport(field.ParentFile(), enum.ParentFile(), typeName); err != nil {
			return "", err
		}
		return typeName, nil
	case protoreflect.GroupKind:
		return "", fmt.Errorf("unsupported type: %s", field.Kind())
	}

	// Handle message types.
	msg := field.Message()

	// Well-known type mappings to native Python types.
	if wkt, ok := wellKnownTypes[string(msg.FullName())]; ok {
		if wkt.runtimeType != "" {
			e.addRuntimeImport(wkt.runtimeType)
		} else if wkt.importLine != "" {
			e.addExternalImport(wkt.importLine)
		}
		if strings.Contains(wkt.pythonType, "_Any") {
			e.addStdImport("_Any")
		}
		return wkt.pythonType, nil
	}

	if field.IsMap() {
		key, err := e.resolveBaseType(referer, field.MapKey())
		if err != nil {
			return "", err
		}
		val, err := e.resolveBaseType(referer, field.MapValue())
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("dict[%s, %s]", key, val), nil
	}

	typeName := resolveName(msg)
	if err := e.addCrossFileImport(field.ParentFile(), msg.ParentFile(), typeName); err != nil {
		return "", err
	}
	return typeName, nil
}

func (e *generator) wrapOptional(typ string) string {
	if typ == "None" {
		return "None"
	}
	if e.config.UseNoneUnionSyntaxInsteadOfOptional {
		return fmt.Sprintf("%s | None", typ)
	}
	e.addStdImport("_Optional")
	return fmt.Sprintf("_Optional[%s]", typ)
}

func (e *generator) resolveType(referer string, field protoreflect.FieldDescriptor) (string, error) {
	typ, err := e.resolveBaseType(referer, field)
	if err != nil {
		return "", err
	}

	if field.IsList() {
		return fmt.Sprintf("list[%s]", typ), nil
	}

	if field.HasOptionalKeyword() || field.ContainingOneof() != nil {
		return e.wrapOptional(typ), nil
	}

	// Proto3 message, enum, and WKT fields default to None,
	// so wrap them in Optional to match proto3 semantics.
	if !field.IsMap() && (field.Kind() == protoreflect.MessageKind || field.Kind() == protoreflect.EnumKind) {
		return e.wrapOptional(typ), nil
	}

	return typ, nil
}

// resolveDefault returns the default value expression for a proto3 field.
func (e *generator) resolveDefault(field protoreflect.FieldDescriptor) string {
	// Optional keyword and oneof fields default to None.
	if field.HasOptionalKeyword() || field.ContainingOneof() != nil {
		return "None"
	}

	// Repeated fields use default_factory.
	if field.IsList() {
		return "default_factory=list"
	}

	// Map fields use default_factory.
	if field.IsMap() {
		return "default_factory=dict"
	}

	// Message/enum fields default to None (wrapped in Optional by resolveType).
	if field.Kind() == protoreflect.MessageKind || field.Kind() == protoreflect.EnumKind {
		return "None"
	}

	// Scalar defaults.
	switch field.Kind() {
	case protoreflect.BoolKind:
		return "False"
	case protoreflect.Int32Kind, protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return "0"
	case protoreflect.DoubleKind, protoreflect.FloatKind:
		return "0.0"
	case protoreflect.StringKind:
		return `""`
	case protoreflect.BytesKind:
		return `b""`
	default:
		return "None"
	}
}

func equalPath(a, b []int32) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func resolveName(d protoreflect.Descriptor) string {
	prefix := string(d.ParentFile().FullName()) + "."
	name := string(d.FullName())
	name = strings.TrimPrefix(name, prefix)
	name = strings.ReplaceAll(name, ".", "_")
	return string(name)
}

func extractComments(sourceCodeInfo *descriptorpb.SourceCodeInfo, path []int32) (leading []string, trailing []string) {
	if sourceCodeInfo != nil {
		for _, location := range sourceCodeInfo.Location {
			if equalPath(location.Path, path) {
				leading = extractCommentLines(location.GetLeadingComments())
				trailing = extractCommentLines(location.GetTrailingComments())
				break
			}
		}
	}
	return
}

func extractCommentLines(comment string) []string {
	if comment == "" {
		return nil
	}
	comment = strings.TrimSpace(comment)
	comments := strings.Split(comment, "\n")
	for i := range comments {
		comments[i] = strings.TrimSpace(comments[i])
	}
	return comments
}

func iter[T any](d interface {
	Len() int
	Get(int) T
},
) func(func(k int, v T) bool) {
	return func(yield func(k int, v T) bool) {
		for i := range d.Len() {
			yield(i, d.Get(i))
		}
	}
}

func buildEnumValueOptionsResolver(gen *protogen.Plugin) *protoregistry.Types {
	resolver := &protoregistry.Types{}
	for _, f := range gen.Files {
		exts := f.Desc.Extensions()
		for i := 0; i < exts.Len(); i++ {
			ext := exts.Get(i)
			if ext.ContainingMessage().FullName() == "google.protobuf.EnumValueOptions" {
				_ = resolver.RegisterExtension(dynamicpb.NewExtensionType(ext))
			}
		}
	}
	return resolver
}

func buildCustomOptionFields(gen *protogen.Plugin) []CustomOptionField {
	seen := map[string]bool{}
	var fields []CustomOptionField
	for _, f := range gen.Files {
		exts := f.Desc.Extensions()
		for i := 0; i < exts.Len(); i++ {
			ext := exts.Get(i)
			if ext.ContainingMessage().FullName() == "google.protobuf.EnumValueOptions" {
				name := string(ext.Name())
				if seen[name] {
					continue
				}
				seen[name] = true
				fields = append(fields, CustomOptionField{
					Name:       name,
					PythonType: protoKindToPythonType(ext.Kind()),
				})
			}
		}
	}
	sort.Slice(fields, func(i, j int) bool {
		return fields[i].Name < fields[j].Name
	})
	return fields
}

// buildFieldConstraintExt scans gen.Files for the buf.validate.field extension
// on google.protobuf.FieldOptions. Returns nil when buf.validate is not imported.
func buildFieldConstraintExt(gen *protogen.Plugin) protoreflect.ExtensionDescriptor {
	for _, f := range gen.Files {
		exts := f.Desc.Extensions()
		for i := 0; i < exts.Len(); i++ {
			ext := exts.Get(i)
			if ext.ContainingMessage().FullName() == "google.protobuf.FieldOptions" &&
				string(ext.Name()) == "field" &&
				string(ext.ParentFile().Package()) == "buf.validate" {
				return ext
			}
		}
	}
	return nil
}

func (e *generator) extractCustomOptions(opts *descriptorpb.EnumValueOptions) map[string]interface{} {
	if opts == nil || e.resolver == nil {
		return nil
	}
	raw, err := proto.Marshal(opts)
	if err != nil {
		return nil
	}
	resolved := &descriptorpb.EnumValueOptions{}
	if err := (proto.UnmarshalOptions{Resolver: e.resolver}).Unmarshal(raw, resolved); err != nil {
		return nil
	}
	result := map[string]interface{}{}
	resolved.ProtoReflect().Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		if !fd.IsExtension() {
			return true
		}
		result[string(fd.Name())] = extensionValueToGo(fd, v)
		return true
	})
	if len(result) == 0 {
		return nil
	}
	return result
}

func (e *generator) extractFieldConstraints(
	opts *descriptorpb.FieldOptions,
	field protoreflect.FieldDescriptor,
) *FieldConstraints {
	if opts == nil || e.fieldConstraintExt == nil {
		return nil
	}
	raw, err := proto.Marshal(opts)
	if err != nil {
		return nil
	}
	extType := dynamicpb.NewExtensionType(e.fieldConstraintExt)
	resolver := &protoregistry.Types{}
	_ = resolver.RegisterExtension(extType)
	resolved := &descriptorpb.FieldOptions{}
	if err := (proto.UnmarshalOptions{Resolver: resolver}).Unmarshal(raw, resolved); err != nil {
		return nil
	}

	var constraintsMsg protoreflect.Message
	resolved.ProtoReflect().Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		if fd.IsExtension() && string(fd.Name()) == "field" {
			constraintsMsg = v.Message()
			return false
		}
		return true
	})
	if constraintsMsg == nil {
		return nil
	}

	result := &FieldConstraints{}
	isFloat := field.Kind() == protoreflect.FloatKind || field.Kind() == protoreflect.DoubleKind

	// Walk the top-level FieldConstraints message fields. The type-specific
	// rules live inside a oneof sub-message; required and cel are top-level.
	constraintsMsg.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		name := string(fd.Name())
		switch {
		case name == "required" && v.Bool():
			result.DroppedConstraints = append(result.DroppedConstraints, "required")
		case name == "cel":
			// cel is a repeated Constraint message; not translated.
			result.DroppedConstraints = append(result.DroppedConstraints, "cel")
		case fd.Kind() == protoreflect.MessageKind && !fd.IsList():
			// Type-specific rules sub-message (int32, string, repeated, map, etc.)
			v.Message().Range(func(rfd protoreflect.FieldDescriptor, rv protoreflect.Value) bool {
				extractRuleField(result, rfd, rv, isFloat)
				return true
			})
			// Combine prefix/suffix into pattern after all sub-fields are visited.
			result.combinePatternConstraints()
		}
		return true
	})

	if !result.HasAny() {
		return nil
	}
	// Sort dropped constraint names so the emitted comments are deterministic
	// regardless of the non-deterministic iteration order of protoreflect.Range.
	sort.Strings(result.DroppedConstraints)
	if result.ConstLiteral != nil {
		e.addStdImport("_Literal")
	}
	if len(result.InValues) > 0 || len(result.NotInValues) > 0 || result.UniqueItems || result.FormatValidator != nil ||
		result.RequireFinite || result.ConstFloatLiteral != nil {
		e.addStdImport("_Annotated")
		e.addStdImport("_AfterValidator")
	}
	return result
}

func extractRuleField(fc *FieldConstraints, fd protoreflect.FieldDescriptor, v protoreflect.Value, isFloat bool) {
	switch string(fd.Name()) {
	case "gt":
		if s, ok := formatNumericLiteral(fd, v, isFloat); ok {
			fc.Gt = &s
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "gt")
		}
	case "gte":
		if s, ok := formatNumericLiteral(fd, v, isFloat); ok {
			fc.Gte = &s
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "gte")
		}
	case "lt":
		if s, ok := formatNumericLiteral(fd, v, isFloat); ok {
			fc.Lt = &s
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "lt")
		}
	case "lte":
		if s, ok := formatNumericLiteral(fd, v, isFloat); ok {
			fc.Lte = &s
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "lte")
		}
	case "min_len":
		n := int64(v.Uint())
		fc.MinLength = &n
	case "max_len":
		n := int64(v.Uint())
		fc.MaxLength = &n
	case "len":
		// Exact-length constraint: translate as min_length=N, max_length=N.
		n := int64(v.Uint())
		n2 := n
		fc.MinLength = &n
		fc.MaxLength = &n2
	case "min_items", "min_pairs":
		n := int64(v.Uint())
		fc.MinLength = &n
	case "max_items", "max_pairs":
		n := int64(v.Uint())
		fc.MaxLength = &n
	case "pattern":
		s := v.String()
		fc.Pattern = &s
	case "prefix":
		s := v.String()
		fc.Prefix = &s
	case "suffix":
		s := v.String()
		fc.Suffix = &s
	case "example":
		if fd.IsList() {
			list := v.List()
			for i := 0; i < list.Len(); i++ {
				if s := formatExampleItem(fd, list.Get(i)); s != "" {
					fc.Examples = append(fc.Examples, s)
				}
			}
		}
	case "const":
		if lit := formatScalarLiteral(fd, v); lit != "" {
			fc.ConstLiteral = &lit
			var def string
			if fd.Kind() == protoreflect.StringKind {
				def = pyQuote(v.String()) // double-quoted for standalone default
			} else {
				def = lit
			}
			fc.ConstDefault = &def
		} else if fd.Kind() == protoreflect.FloatKind || fd.Kind() == protoreflect.DoubleKind {
			// Literal[float] is invalid per PEP 586; use AfterValidator instead.
			var flit string
			if fd.Kind() == protoreflect.FloatKind {
				flit = formatPythonFloat(float64(float32(v.Float())))
			} else {
				flit = formatPythonFloat(v.Float())
			}
			fc.ConstFloatLiteral = &flit
			fc.ConstDefault = &flit
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "const")
		}
	case "in":
		if fd.IsList() {
			list := v.List()
			var lits []string
			for i := 0; i < list.Len(); i++ {
				if l := formatScalarLiteral(fd, list.Get(i)); l != "" {
					lits = append(lits, l)
				}
			}
			if len(lits) > 0 {
				fc.InValues = append(fc.InValues, lits...)
			} else {
				fc.DroppedConstraints = append(fc.DroppedConstraints, "in")
			}
		}
	case "not_in":
		if fd.IsList() {
			list := v.List()
			var lits []string
			for i := 0; i < list.Len(); i++ {
				if l := formatScalarLiteral(fd, list.Get(i)); l != "" {
					lits = append(lits, l)
				}
			}
			if len(lits) > 0 {
				fc.NotInValues = append(fc.NotInValues, lits...)
			} else {
				fc.DroppedConstraints = append(fc.DroppedConstraints, "not_in")
			}
		}
	case "unique":
		if v.Bool() {
			fc.UniqueItems = true
		}
	case "finite":
		if v.Bool() {
			fc.RequireFinite = true
		}
	case "contains":
		s := v.String()
		fc.Contains = &s
	case "email", "uri", "ip", "ipv4", "ipv6", "uuid":
		if v.Bool() {
			name := string(fd.Name())
			fc.FormatValidator = &name
		}
	default:
		fc.DroppedConstraints = append(fc.DroppedConstraints, string(fd.Name()))
	}
}

// formatNumericLiteral formats a protoreflect Value as a Python numeric literal.
// Returns ("", false) when fd is a MessageKind (e.g. Duration or Timestamp
// bounds), which cannot be expressed as a simple numeric literal and must be
// dropped with a comment instead.
func formatNumericLiteral(fd protoreflect.FieldDescriptor, v protoreflect.Value, isFloat bool) (string, bool) {
	switch fd.Kind() {
	case protoreflect.FloatKind:
		return formatPythonFloat(float64(float32(v.Float()))), true
	case protoreflect.DoubleKind:
		return formatPythonFloat(v.Float()), true
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		return fmt.Sprintf("%d", v.Int()), true
	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return fmt.Sprintf("%d", v.Uint()), true
	case protoreflect.MessageKind:
		// Duration and Timestamp bounds are message-typed; cannot be represented
		// as a simple numeric literal.
		return "", false
	default:
		if isFloat {
			return formatPythonFloat(v.Float()), true
		}
		return fmt.Sprintf("%d", v.Int()), true
	}
}

// formatExampleItem formats a single element from a repeated `example` field
// as a Python literal. Returns "" for types that cannot be simply expressed
// (bytes, messages), which the caller should skip.
func formatExampleItem(fd protoreflect.FieldDescriptor, v protoreflect.Value) string {
	switch fd.Kind() {
	case protoreflect.StringKind:
		return pyQuote(v.String())
	case protoreflect.BoolKind:
		if v.Bool() {
			return "True"
		}
		return "False"
	case protoreflect.FloatKind:
		return formatPythonFloat(float64(float32(v.Float())))
	case protoreflect.DoubleKind:
		return formatPythonFloat(v.Float())
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		return fmt.Sprintf("%d", v.Int())
	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return fmt.Sprintf("%d", v.Uint())
	case protoreflect.EnumKind:
		return fmt.Sprintf("%d", v.Enum())
	default:
		return "" // bytes, messages — skip
	}
}

func formatPythonFloat(f float64) string {
	s := fmt.Sprintf("%g", f)
	if !strings.Contains(s, ".") && !strings.Contains(s, "e") {
		s += ".0"
	}
	return s
}

func extensionValueToGo(fd protoreflect.FieldDescriptor, v protoreflect.Value) interface{} {
	switch fd.Kind() {
	case protoreflect.BoolKind:
		return v.Bool()
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind:
		return int32(v.Int())
	case protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		return v.Int()
	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind:
		return uint32(v.Uint())
	case protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return v.Uint()
	case protoreflect.FloatKind:
		return float32(v.Float())
	case protoreflect.DoubleKind:
		return v.Float()
	case protoreflect.StringKind:
		return v.String()
	case protoreflect.BytesKind:
		return v.Bytes()
	case protoreflect.EnumKind:
		return int32(v.Enum())
	default:
		return nil
	}
}

func pythonLiteral(v interface{}) string {
	switch val := v.(type) {
	case bool:
		if val {
			return "True"
		}
		return "False"
	case string:
		return fmt.Sprintf("%q", val)
	case int32:
		return fmt.Sprintf("%d", val)
	case int64:
		return fmt.Sprintf("%d", val)
	case uint32:
		return fmt.Sprintf("%d", val)
	case uint64:
		return fmt.Sprintf("%d", val)
	case float32:
		return fmt.Sprintf("%g", val)
	case float64:
		return fmt.Sprintf("%g", val)
	default:
		return "None"
	}
}

func camelToSnakeCase(str string) string {
	snake := matchFirstCap.ReplaceAllString(str, "${1}_${2}")
	snake = matchAllCap.ReplaceAllString(snake, "${1}_${2}")
	return strings.ToUpper(snake)
}
