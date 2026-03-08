package main

import (
	"fmt"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"google.golang.org/protobuf/reflect/protoreflect"
)

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
	Name                string
	Alias               string // non-empty when Name was renamed to avoid shadowing Python builtins
	Type                string
	NeedsQuote          bool // true when Type contains a user-defined class (message/enum) requiring a forward-reference string annotation
	Optional            bool
	Default             string // proto3 zero-value default (e.g. "0", "False", "None", "default_factory=list")
	OneOf               *OneOf
	Constraints         *FieldConstraints
	ConstrainedRequired bool // no default; zero-arg construction requires explicit value
	LeadingComments     []string
	TrailingComments    []string
}

func (f Field) IsDefaultFactory() bool {
	return strings.HasPrefix(f.Default, "default_factory=")
}

func (f Field) HasConstraints() bool {
	return f.Constraints != nil && f.Constraints.HasAny()
}

// HasConstraintKwargs returns true when the field has content for _Field() beyond
// a default value: direct constraint kwargs or dropped constraint comments.
// Used to decide whether a multi-line _Field(...) form is needed.
func (f Field) HasConstraintKwargs() bool {
	if f.Constraints == nil {
		return false
	}
	return len(f.Constraints.PydanticArgs()) > 0 || len(f.Constraints.DroppedConstraints) > 0
}

// TypeAnnotation returns the type as it should appear in a Python annotation,
// wrapped in double quotes when the type is a forward reference to a
// user-defined class (message or enum).
func (f Field) TypeAnnotation() string {
	if f.NeedsQuote {
		return `"` + f.Type + `"`
	}
	return f.Type
}

// TypeAnnotationFormatted returns the type annotation formatted for the field
// definition line at the given base indent level. For unquoted _Annotated[...]
// types whose definition line would exceed 88 characters, it wraps the
// annotation across multiple lines to match ruff's output style.
//
// Splitting only happens when the annotation itself with the field name prefix
// exceeds 88 chars; when the annotation fits on one line but the trailing
// " = _Field(" pushes the line over, NeedsParenAssignment should be used
// instead so the template can emit the parenthesized assignment form.
func (f Field) TypeAnnotationFormatted(bi string) string {
	annotation := f.TypeAnnotation()
	// Only wrap unquoted _Annotated[...] types (quoted types are never split).
	if f.NeedsQuote || !strings.HasPrefix(annotation, "_Annotated[") || !strings.HasSuffix(annotation, "]") {
		return annotation
	}
	annotationLine := bi + f.Name + ": " + annotation
	// Case 1: full line fits — no wrapping needed.
	if len(annotationLine+" = _Field(") <= 88 {
		return annotation
	}
	// Case 2: ruff-stable paren form — "name: annotation = (" fits in 88.
	// NeedsParenAssignment handles the template rendering; return annotation unsplit.
	if len(annotationLine+" = (") <= 88 {
		return annotation
	}
	// Case 3: annotation itself is too long — split across multiple lines.
	inner := annotation[len("_Annotated[") : len(annotation)-1]
	return "_Annotated[\n" + bi + "    " + inner + "\n" + bi + "]"
}

// TypeAnnotationFormattedBare is like TypeAnnotationFormatted but for fields
// that emit a bare annotation with no assignment. It only splits the annotation
// when the bare "name: annotation" line alone exceeds 88 characters, rather
// than when adding "= _Field(" would push it over.
func (f Field) TypeAnnotationFormattedBare(bi string) string {
	annotation := f.TypeAnnotation()
	if f.NeedsQuote || !strings.HasPrefix(annotation, "_Annotated[") || !strings.HasSuffix(annotation, "]") {
		return annotation
	}
	annotationLine := bi + f.Name + ": " + annotation
	if len(annotationLine) <= 88 {
		return annotation
	}
	inner := annotation[len("_Annotated[") : len(annotation)-1]
	return "_Annotated[\n" + bi + "    " + inner + "\n" + bi + "]"
}

// NeedsMultilineDefault reports whether the field should use the multi-line
// _Field() form because it has a default value but no constraint kwargs, and
// the simple "name: annotation = _Field(default)" line would exceed 88 chars.
func (f Field) NeedsMultilineDefault(bi string) bool {
	if f.Default == "" || f.HasConstraintKwargs() {
		return false
	}
	annotation := f.TypeAnnotation()
	line := bi + f.Name + ": " + annotation + " = _Field(" + f.Default + ")"
	return len(line) > 88
}

// NeedsParenAssignment reports whether this field should use the ruff-stable
// parenthesized assignment form. Ruff uses this form when the annotation fits
// on one line with the field name (i.e. "name: annotation = (" ≤ 88 chars)
// but the full "name: annotation = _Field(" line would exceed 88 chars.
//
//	name: _Annotated[...] = (
//	    _Field(
//	        ...
//	    )
//	)
func (f Field) NeedsParenAssignment(bi string) bool {
	annotation := f.TypeAnnotation()
	if f.NeedsQuote || !strings.HasPrefix(annotation, "_Annotated[") || !strings.HasSuffix(annotation, "]") {
		return false
	}
	annotationLine := bi + f.Name + ": " + annotation
	if len(annotationLine+" = _Field(") <= 88 {
		return false // full line fits; no paren needed
	}
	return len(annotationLine+" = (") <= 88 // paren form is stable
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
		quotedNames := make([]string, len(f.OneOf.FieldNames))
		for i, n := range f.OneOf.FieldNames {
			quotedNames[i] = fmt.Sprintf("%q", n)
		}
		parts = append(parts, fmt.Sprintf(
			"Only one of the fields can be specified with: [%s] (oneof %s)",
			strings.Join(quotedNames, ", "), f.OneOf.Name,
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
	FormatValidator    *string  // one of: "email", "uri", "ip", "ipv4", "ipv6", "uuid", "hostname", etc.
	RequireFinite      bool     // true when float/double.finite = true
	Contains           *string  // string.contains substring — intermediate; resolved into Pattern by combinePatternConstraints
	NotContains        *string  // string.not_contains substring — translated to _AfterValidator
	ConstFloatLiteral  *string  // Python float literal for float/double const (Literal[] is invalid per PEP 586)
	Required           bool     // true when buf.validate required = true is set
	IsNonScalar        bool     // true when field kind is MessageKind or EnumKind
	HasIgnore          bool     // true when ignore != IGNORE_UNSPECIFIED (any non-zero ignore enum value)
}

func (c *FieldConstraints) HasAny() bool {
	if c == nil {
		return false
	}
	return c.Required ||
		c.ConstLiteral != nil || c.ConstFloatLiteral != nil || c.RequireFinite ||
		len(c.InValues) > 0 || len(c.NotInValues) > 0 || c.UniqueItems ||
		c.Gt != nil || c.Gte != nil || c.Lt != nil || c.Lte != nil ||
		c.MinLength != nil || c.MaxLength != nil || c.Pattern != nil || c.Contains != nil ||
		c.NotContains != nil ||
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

// ZeroValueFails reports whether the proto3 zero value for kind fails this
// field's constraints, indicating the field should become ConstrainedRequired.
// Const constraints are excluded: they supply their own valid default.
// HasIgnore is checked by the caller before invoking this method.
func (c *FieldConstraints) ZeroValueFails(kind protoreflect.Kind) bool {
	if c == nil {
		return false
	}
	if c.ConstLiteral != nil || c.ConstFloatLiteral != nil {
		return false
	}
	if c.FormatValidator != nil {
		return true
	}
	// gt=N where N >= 0: zero is not > N.
	if c.Gt != nil {
		if v, err := strconv.ParseFloat(*c.Gt, 64); err == nil && v >= 0 {
			return true
		}
	}
	// ge=N where N > 0: zero is not >= N.
	if c.Gte != nil {
		if v, err := strconv.ParseFloat(*c.Gte, 64); err == nil && v > 0 {
			return true
		}
	}
	if c.MinLength != nil && *c.MinLength > 0 {
		return true
	}
	// All patterns produced by the generator (from prefix/suffix/contains/min_len
	// or explicit string.pattern rules) reject the empty string. A user-supplied
	// pattern that can match "" (e.g. "[a-z]*") would be a false positive here,
	// but such patterns are not generated.
	if c.Pattern != nil {
		return true
	}
	if len(c.InValues) > 0 && !c.inValuesContainZero(kind) {
		return true
	}
	return false
}

// zeroLiteralForKind returns the Python literal for the proto3 zero value of
// kind, matching the format produced by formatScalarLiteral/formatPythonFloat,
// so it can be compared directly against InValues entries.
func zeroLiteralForKind(kind protoreflect.Kind) string {
	switch kind {
	case protoreflect.StringKind:
		return `""`
	case protoreflect.BoolKind:
		return "False"
	case protoreflect.FloatKind, protoreflect.DoubleKind:
		return "0.0"
	default: // all integer kinds
		return "0"
	}
}

func (c *FieldConstraints) inValuesContainZero(kind protoreflect.Kind) bool {
	zero := zeroLiteralForKind(kind)
	for _, v := range c.InValues {
		if v == zero {
			return true
		}
	}
	return false
}

type Message struct {
	Name             string
	Fields           []Field
	NestedMessages   []Message
	NestedEnums      []Enum
	LeadingComments  []string
	TrailingComments []string
	OneOfGroups      []OneOf // deduplicated oneof groups; populated after all fields are processed
}

func (m Message) HasAlias() bool {
	for _, f := range m.Fields {
		if f.Alias != "" {
			return true
		}
	}
	return false
}

type File struct {
	LeadingComments  []string
	TrailingComments []string
}

type GeneratorConfig struct {
	PreservingProtoFieldName            bool
	AutoTrimEnumPrefix                  bool
	UseIntegersForEnums                 bool
	DisableFieldDescription             bool
	UseNoneUnionSyntaxInsteadOfOptional bool
}
