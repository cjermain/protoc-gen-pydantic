package main

import (
	"fmt"
	"sort"
	"strings"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
)

// splitDictType splits "dict[K, V]" into its key and value type strings,
// respecting nested brackets so types like "dict[str, dict[str, int]]" work.
// Parenthesis depth is not tracked separately: any comma inside a function
// call (e.g. _Field(min_length=1, max_length=32)) will always appear inside
// _Annotated[...] brackets as well, so the bracket depth counter is sufficient.
func splitDictType(t string) (key, val string, ok bool) {
	if !strings.HasPrefix(t, "dict[") || !strings.HasSuffix(t, "]") {
		return "", "", false
	}
	inner := t[len("dict[") : len(t)-1]
	depth := 0
	for i, ch := range inner {
		switch ch {
		case '[':
			depth++
		case ']':
			depth--
		case ',':
			if depth == 0 {
				return strings.TrimSpace(inner[:i]), strings.TrimSpace(inner[i+1:]), true
			}
		}
	}
	return "", "", false
}

// splitTopLevelCommas splits s on commas at bracket depth 0, respecting
// nested square brackets and parentheses.
func splitTopLevelCommas(s string) []string {
	var parts []string
	depth := 0
	inDouble := false
	start := 0
	prev := rune(0)
	for i, ch := range s {
		if inDouble {
			if ch == '"' && prev != '\\' {
				inDouble = false
			}
			prev = ch
			continue
		}
		switch ch {
		case '"':
			inDouble = true
		case '[', '(':
			depth++
		case ']', ')':
			depth--
		case ',':
			if depth == 0 {
				parts = append(parts, s[start:i])
				start = i + 1
			}
		}
		prev = ch
	}
	parts = append(parts, s[start:])
	return parts
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

// buildItemAnnotation wraps itemType with per-element constraints from
// repeated.items, producing e.g. _Annotated[str, _Field(min_length=1, max_length=32)].
func (e *generator) buildItemAnnotation(itemType string, fc *FieldConstraints) string {
	if fc == nil {
		return itemType
	}
	if fc.ConstLiteral != nil {
		itemType = "_Literal[" + *fc.ConstLiteral + "]"
		e.addStdImport("_Literal")
	}
	var metaParts []string
	if args := fc.PydanticArgs(); len(args) > 0 {
		e.addStdImport("_Field")
		metaParts = append(metaParts, "_Field("+strings.Join(args, ", ")+")")
	}
	if len(fc.InValues) > 0 {
		v := "{" + strings.Join(fc.InValues, ", ") + "}"
		metaParts = append(metaParts, "_AfterValidator(_make_in_validator(frozenset("+v+")))")
		e.addRuntimeImport("_make_in_validator")
	}
	if len(fc.NotInValues) > 0 {
		v := "{" + strings.Join(fc.NotInValues, ", ") + "}"
		metaParts = append(metaParts, "_AfterValidator(_make_not_in_validator(frozenset("+v+")))")
		e.addRuntimeImport("_make_not_in_validator")
	}
	if fc.NotContains != nil {
		metaParts = append(metaParts, "_AfterValidator(_make_not_contains_validator("+pyQuote(*fc.NotContains)+"))")
		e.addRuntimeImport("_make_not_contains_validator")
	}
	if fc.MinBytes != nil {
		metaParts = append(metaParts, fmt.Sprintf("_AfterValidator(_make_min_bytes_validator(%d))", *fc.MinBytes))
		e.addRuntimeImport("_make_min_bytes_validator")
	}
	if fc.MaxBytes != nil {
		metaParts = append(metaParts, fmt.Sprintf("_AfterValidator(_make_max_bytes_validator(%d))", *fc.MaxBytes))
		e.addRuntimeImport("_make_max_bytes_validator")
	}
	if fc.LenBytes != nil {
		metaParts = append(metaParts, fmt.Sprintf("_AfterValidator(_make_len_bytes_validator(%d))", *fc.LenBytes))
		e.addRuntimeImport("_make_len_bytes_validator")
	}
	if fc.FormatValidator != nil {
		helperName := "_validate_" + *fc.FormatValidator
		metaParts = append(metaParts, "_AfterValidator("+helperName+")")
		e.addRuntimeImport(helperName)
	}
	if fc.RequireFinite {
		metaParts = append(metaParts, "_AfterValidator(_require_finite)")
		e.addRuntimeImport("_require_finite")
	}
	if fc.ConstFloatLiteral != nil {
		metaParts = append(metaParts, "_AfterValidator(_make_const_validator("+*fc.ConstFloatLiteral+"))")
		e.addRuntimeImport("_make_const_validator")
	}
	if len(metaParts) == 0 {
		return itemType
	}
	e.addStdImport("_Annotated")
	return "_Annotated[" + itemType + ", " + strings.Join(metaParts, ", ") + "]"
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

	// repeated.items: wrap inner list element type with per-element constraints
	if fc.ItemConstraints != nil &&
		strings.HasPrefix(f.Type, "list[") && strings.HasSuffix(f.Type, "]") {
		innerType := f.Type[len("list[") : len(f.Type)-1]
		annotatedInner := e.buildItemAnnotation(innerType, fc.ItemConstraints)
		if annotatedInner != innerType {
			f.Type = "list[" + annotatedInner + "]"
		}
	}

	// map.keys / map.values: wrap key/value types with per-entry constraints
	if fc.KeyConstraints != nil || fc.ValueConstraints != nil {
		if keyType, valType, ok := splitDictType(f.Type); ok {
			if fc.KeyConstraints != nil {
				keyType = e.buildItemAnnotation(keyType, fc.KeyConstraints)
			}
			if fc.ValueConstraints != nil {
				valType = e.buildItemAnnotation(valType, fc.ValueConstraints)
			}
			f.Type = "dict[" + keyType + ", " + valType + "]"
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
	if fc.MinBytes != nil {
		validators = append(validators, fmt.Sprintf("_AfterValidator(_make_min_bytes_validator(%d))", *fc.MinBytes))
		e.addRuntimeImport("_make_min_bytes_validator")
	}
	if fc.MaxBytes != nil {
		validators = append(validators, fmt.Sprintf("_AfterValidator(_make_max_bytes_validator(%d))", *fc.MaxBytes))
		e.addRuntimeImport("_make_max_bytes_validator")
	}
	if fc.LenBytes != nil {
		validators = append(validators, fmt.Sprintf("_AfterValidator(_make_len_bytes_validator(%d))", *fc.LenBytes))
		e.addRuntimeImport("_make_len_bytes_validator")
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
	// CEL field-level validators → AfterValidator wrapping via lambda factories.
	for _, cv := range fc.CelValidators {
		// Strip redundant outer parens from the expression when it is the
		// entire body of a lambda: "lambda v: (v > 0)" → "lambda v: v > 0".
		lambdaExpr := stripOuterParens(cv.Expression)

		// Null-safe fields (WKT message types like Timestamp/Duration) are
		// Optional in Python.  When the field is absent (v is None), CEL rules
		// are skipped in protovalidate, so we replicate that with a guard.
		// The stripped expression is re-wrapped in parens so that operator
		// precedence is preserved: "v is None or (a and b)" stays correct.
		if cv.NullSafe {
			lambdaExpr = fmt.Sprintf("v is None or (%s)", lambdaExpr)
		}

		var validatorStr string
		if cv.ReturnsBool {
			validatorStr = fmt.Sprintf(
				"_AfterValidator(_make_cel_validator(lambda v: %s, %s))",
				lambdaExpr, pyQuote(cv.Message),
			)
			e.addRuntimeImport("_make_cel_validator")
		} else {
			validatorStr = fmt.Sprintf(
				"_AfterValidator(_make_cel_str_validator(lambda v: %s))",
				lambdaExpr,
			)
			e.addRuntimeImport("_make_cel_str_validator")
		}
		validators = append(validators, validatorStr)
		for _, imp := range cv.Imports {
			e.addRuntimeImport(imp)
		}
		e.addStdImport("_Annotated")
		e.addStdImport("_AfterValidator")
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
				result.HasIgnore = true
			}
		case name == "cel":
			// Attempt to transpile each Constraint message; failures are dropped.
			list := v.List()
			for i := 0; i < list.Len(); i++ {
				rule := extractCelRule(list.Get(i).Message())
				cv, err := transpileCELField(rule, field, e.celEnvCache)
				if err != nil {
					result.DroppedConstraints = append(result.DroppedConstraints,
						fmt.Sprintf("cel id=%q (not translated: %v)", rule.ID, err))
				} else {
					result.CelValidators = append(result.CelValidators, cv)
				}
			}
		case fd.Kind() == protoreflect.MessageKind && !fd.IsList():
			// Type-specific rules sub-message (int32, string, repeated, map, etc.)
			v.Message().Range(func(rfd protoreflect.FieldDescriptor, rv protoreflect.Value) bool {
				switch {
				case string(rfd.Name()) == "items" && rfd.Kind() == protoreflect.MessageKind:
					result.ItemConstraints = e.extractConstraintsFromMsg(rv.Message(), isFloat, isBytesField)
				case string(rfd.Name()) == "keys" && rfd.Kind() == protoreflect.MessageKind && field.IsMap():
					keyKind := field.MapKey().Kind()
					isKeyFloat := keyKind == protoreflect.FloatKind || keyKind == protoreflect.DoubleKind
					isKeyBytes := keyKind == protoreflect.BytesKind
					result.KeyConstraints = e.extractConstraintsFromMsg(rv.Message(), isKeyFloat, isKeyBytes)
				case string(rfd.Name()) == "values" && rfd.Kind() == protoreflect.MessageKind && field.IsMap():
					valKind := field.MapValue().Kind()
					isValFloat := valKind == protoreflect.FloatKind || valKind == protoreflect.DoubleKind
					isValBytes := valKind == protoreflect.BytesKind
					result.ValueConstraints = e.extractConstraintsFromMsg(rv.Message(), isValFloat, isValBytes)
				default:
					extractRuleField(result, rfd, rv, isFloat, isBytesField)
				}
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
		result.RequireFinite || result.ConstFloatLiteral != nil || result.NotContains != nil ||
		result.MinBytes != nil || result.MaxBytes != nil || result.LenBytes != nil ||
		len(result.CelValidators) > 0 {
		e.addStdImport("_Annotated")
		e.addStdImport("_AfterValidator")
	}
	return result
}

// extractConstraintsFromMsg extracts FieldConstraints from a nested
// FieldConstraints sub-message (e.g. the value of repeated.items). It mirrors
// the inner part of extractFieldConstraints but takes a Message directly.
func (e *generator) extractConstraintsFromMsg(
	msg protoreflect.Message,
	isFloat bool,
	isBytesField bool,
) *FieldConstraints {
	result := &FieldConstraints{}
	msg.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		name := string(fd.Name())
		switch {
		case name == "cel":
			// CEL inside items/keys/values: drop with a comment (no field descriptor available).
			result.DroppedConstraints = append(result.DroppedConstraints, "cel")
		case fd.Kind() == protoreflect.MessageKind && !fd.IsList():
			v.Message().Range(func(rfd protoreflect.FieldDescriptor, rv protoreflect.Value) bool {
				extractRuleField(result, rfd, rv, isFloat, isBytesField)
				return true
			})
			result.combinePatternConstraints()
		}
		return true
	})
	if !result.HasAny() {
		return nil
	}
	sort.Strings(result.DroppedConstraints)
	if result.ConstLiteral != nil {
		e.addStdImport("_Literal")
	}
	if len(result.InValues) > 0 || len(result.NotInValues) > 0 || result.UniqueItems ||
		result.FormatValidator != nil || result.RequireFinite ||
		result.ConstFloatLiteral != nil || result.NotContains != nil ||
		result.MinBytes != nil || result.MaxBytes != nil || result.LenBytes != nil {
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
	case "min_bytes":
		n := int64(v.Uint())
		fc.MinBytes = &n
	case "max_bytes":
		n := int64(v.Uint())
		fc.MaxBytes = &n
	case "len_bytes":
		n := int64(v.Uint())
		fc.LenBytes = &n
	case "email", "uri":
		if v.Bool() {
			if isBytesField {
				fc.DroppedConstraints = append(fc.DroppedConstraints, string(fd.Name()))
			} else {
				name := string(fd.Name())
				fc.FormatValidator = &name
			}
		}
	case "ip", "ipv4", "ipv6":
		if v.Bool() {
			if isBytesField {
				name := "bytes_" + string(fd.Name())
				fc.FormatValidator = &name
			} else {
				name := string(fd.Name())
				fc.FormatValidator = &name
			}
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
