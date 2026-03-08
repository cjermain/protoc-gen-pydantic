package main

import (
	"sort"
	"strings"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
)

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

	// required = true → strip | None and set default to ...
	// Only for scalar-kinded proto3-optional/oneof fields. Message/enum-typed fields
	// and plain scalars (no | None) keep the dropped comment.
	if fc.Required {
		hasNoneSuffix := strings.HasSuffix(f.Type, " | None")
		hasOptionalPrefix := strings.HasPrefix(f.Type, "_Optional[") && strings.HasSuffix(f.Type, "]")
		if (hasNoneSuffix || hasOptionalPrefix) && !fc.IsNonScalar {
			if hasNoneSuffix {
				f.Type = strings.TrimSuffix(f.Type, " | None")
			} else {
				f.Type = f.Type[len("_Optional[") : len(f.Type)-1]
			}
			f.Default = "default=..."
		} else {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "required")
			sort.Strings(fc.DroppedConstraints)
		}
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
			f.Default = "default=" + *fc.ConstDefault
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
	if fc.NotContains != nil {
		validators = append(validators, "_AfterValidator(_make_not_contains_validator("+pyQuote(*fc.NotContains)+"))")
		e.addRuntimeImport("_make_not_contains_validator")
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
			f.Default = "default=" + *fc.ConstDefault
		}
	}
	if len(validators) > 0 {
		f.Type = wrapWithAnnotated(f.Type, validators)
	}
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
	isBytesField := field.Kind() == protoreflect.BytesKind
	result.IsNonScalar = field.Kind() == protoreflect.MessageKind || field.Kind() == protoreflect.EnumKind

	// Walk the top-level FieldConstraints message fields. The type-specific
	// rules live inside a oneof sub-message; required and cel are top-level.
	constraintsMsg.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		name := string(fd.Name())
		switch {
		case name == "required" && v.Bool():
			result.Required = true
		case name == "ignore":
			if v.Enum() != 0 {
				result.IgnoreZero = true
			}
		case name == "cel":
			// cel is a repeated Constraint message; not translated.
			result.DroppedConstraints = append(result.DroppedConstraints, "cel")
		case fd.Kind() == protoreflect.MessageKind && !fd.IsList():
			// Type-specific rules sub-message (int32, string, repeated, map, etc.)
			v.Message().Range(func(rfd protoreflect.FieldDescriptor, rv protoreflect.Value) bool {
				extractRuleField(result, rfd, rv, isFloat, isBytesField)
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
		result.RequireFinite || result.ConstFloatLiteral != nil || result.NotContains != nil {
		e.addStdImport("_Annotated")
		e.addStdImport("_AfterValidator")
	}
	return result
}

func extractRuleField(fc *FieldConstraints, fd protoreflect.FieldDescriptor, v protoreflect.Value, isFloat bool, isBytesField bool) {
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
		if fd.Kind() == protoreflect.BytesKind {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "prefix")
		} else {
			s := v.String()
			fc.Prefix = &s
		}
	case "suffix":
		if fd.Kind() == protoreflect.BytesKind {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "suffix")
		} else {
			s := v.String()
			fc.Suffix = &s
		}
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
				item := list.Get(i)
				l := formatScalarLiteral(fd, item)
				if l == "" {
					switch fd.Kind() {
					case protoreflect.FloatKind:
						l = formatPythonFloat(float64(float32(item.Float())))
					case protoreflect.DoubleKind:
						l = formatPythonFloat(item.Float())
					}
				}
				if l != "" {
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
				item := list.Get(i)
				l := formatScalarLiteral(fd, item)
				if l == "" {
					switch fd.Kind() {
					case protoreflect.FloatKind:
						l = formatPythonFloat(float64(float32(item.Float())))
					case protoreflect.DoubleKind:
						l = formatPythonFloat(item.Float())
					}
				}
				if l != "" {
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
		if fd.Kind() == protoreflect.BytesKind {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "contains")
		} else {
			s := v.String()
			fc.Contains = &s
		}
	case "not_contains":
		if fd.Kind() == protoreflect.BytesKind {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "not_contains")
		} else {
			s := v.String()
			fc.NotContains = &s
		}
	case "email", "uri", "ip", "ipv4", "ipv6":
		if v.Bool() {
			name := string(fd.Name())
			fc.FormatValidator = &name
		}
	case "uuid":
		if v.Bool() {
			if isBytesField {
				name := "bytes_uuid"
				fc.FormatValidator = &name
			} else {
				name := string(fd.Name())
				fc.FormatValidator = &name
			}
		}
	case "hostname", "uri_ref", "address", "tuuid",
		"ip_with_prefixlen", "ipv4_with_prefixlen", "ipv6_with_prefixlen",
		"ip_prefix", "ipv4_prefix", "ipv6_prefix",
		"host_and_port", "ulid":
		if v.Bool() {
			name := string(fd.Name())
			fc.FormatValidator = &name
		}
	case "well_known_regex":
		switch v.Enum() {
		case 1: // KNOWN_REGEX_HTTP_HEADER_NAME
			name := "http_header_name"
			fc.FormatValidator = &name
		case 2: // KNOWN_REGEX_HTTP_HEADER_VALUE
			name := "http_header_value"
			fc.FormatValidator = &name
		}
	case "strict":
		// strict=false loosens well_known_regex validation; not supported — use strict always.
		if !v.Bool() {
			fc.DroppedConstraints = append(fc.DroppedConstraints, "strict=false")
		}
	default:
		fc.DroppedConstraints = append(fc.DroppedConstraints, string(fd.Name()))
	}
}
