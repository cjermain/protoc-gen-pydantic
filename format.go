package main

import (
	"fmt"
	"strings"

	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/types/descriptorpb"
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

// formatScalarLiteral formats a scalar protoreflect.Value as a Python literal
// suitable for embedding in type annotations (double-quoted strings for strings).
// Returns "" for unsupported kinds (bytes, float, double, messages, enums) so
// callers fall through to dropped-constraint comments. Float/double are excluded
// because Python's Literal[] type does not accept float values (PEP 586).
func formatScalarLiteral(fd protoreflect.FieldDescriptor, v protoreflect.Value) string {
	switch fd.Kind() {
	case protoreflect.StringKind:
		return pyQuote(v.String())
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

// resolveQualifiedName returns the dotted path from the file package root
// (e.g. "Outer.Inner.Deepest"), suitable for use in Python type annotations.
func resolveQualifiedName(d protoreflect.Descriptor) string {
	prefix := string(d.ParentFile().FullName()) + "."
	name := string(d.FullName())
	return strings.TrimPrefix(name, prefix) // keep dots
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
		panic("unreachable: unexpected Kind in formatNumericLiteral")
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

// isBalancedOuterParens reports whether s is wrapped in a single balanced
// pair of parentheses — i.e., s starts with "(" and the matching ")" is
// the very last character.
func isBalancedOuterParens(s string) bool {
	if len(s) < 2 || s[0] != '(' || s[len(s)-1] != ')' {
		return false
	}
	depth := 0
	for i, ch := range s {
		switch ch {
		case '(':
			depth++
		case ')':
			depth--
		}
		if depth == 0 {
			return i == len(s)-1
		}
	}
	return false
}

// stripOuterParens removes one layer of balanced outer parentheses from s
// if present; otherwise returns s unchanged.
func stripOuterParens(s string) string {
	if isBalancedOuterParens(s) {
		return s[1 : len(s)-1]
	}
	return s
}

// splitBoolOps splits expr at top-level " or " and " and " operators.
// The operator is kept at the start of each continuation part:
//
//	"a or b and c" → ["a", "or b", "and c"]
func splitBoolOps(expr string) []string {
	var parts []string
	depth := 0
	start := 0
	i := 0
	for i < len(expr) {
		ch := expr[i]
		if ch == '(' || ch == '[' {
			depth++
			i++
			continue
		}
		if ch == ')' || ch == ']' {
			depth--
			i++
			continue
		}
		if depth == 0 {
			split := false
			for _, op := range []string{" or ", " and "} {
				if i+len(op) <= len(expr) && expr[i:i+len(op)] == op {
					parts = append(parts, strings.TrimSpace(expr[start:i]))
					start = i + 1 // skip leading space; "or "/"and " stays
					i += len(op)
					split = true
					break
				}
			}
			if split {
				continue
			}
		}
		i++
	}
	if start < len(expr) {
		parts = append(parts, strings.TrimSpace(expr[start:]))
	}
	return parts
}

// formatBoolExpr formats a boolean expression for use inside an `if not (…):`
// block. If the expression fits on one line at indent, it returns the single
// indented line; otherwise it splits at top-level or/and operators.
func formatBoolExpr(expr, indent string) string {
	if len(indent+expr) <= 88 {
		return indent + expr
	}
	parts := splitBoolOps(expr)
	if len(parts) <= 1 {
		return indent + expr
	}
	lines := make([]string, len(parts))
	for i, p := range parts {
		lines[i] = indent + p
	}
	return strings.Join(lines, "\n")
}

// pycelCondLine returns the ruff-stable `if not (expr):` line for a message-
// level bool-returning CEL validator. The expression's outer parens are
// stripped to avoid double-parens inside `not (…)`, and long lines are
// split into ruff's binary-operator continuation style.
func pycelCondLine(bi, expr string) string {
	methodIndent := bi + "    "
	stripped := stripOuterParens(expr)
	single := methodIndent + "if not (" + stripped + "):"
	if len(single) <= 88 {
		return single
	}
	innerIndent := methodIndent + "    "
	formatted := formatBoolExpr(stripped, innerIndent)
	return methodIndent + "if not (\n" + formatted + "\n" + methodIndent + "):"
}

// formatAnnotationElement formats a single element of an _Annotated[…] type
// to be ruff-stable at the given base indent (the indent level where this
// element will appear). If the element is an _AfterValidator(…) call that
// doesn't fit on one line, it is wrapped across multiple lines matching
// ruff's function-call expansion style.
func formatAnnotationElement(s, elemIndent string) string {
	// If the element plus its trailing comma fits at this indent: single line.
	if len(elemIndent+s+",") <= 88 {
		return s
	}
	// Try to wrap _AfterValidator(inner) onto two lines.
	const avPrefix = "_AfterValidator("
	if strings.HasPrefix(s, avPrefix) && strings.HasSuffix(s, ")") {
		inner := s[len(avPrefix) : len(s)-1]
		innerIndent := elemIndent + "    "
		// If inner fits on one line at innerIndent (no trailing comma — it's
		// inside a function call, not a list/annotation element):
		if len(innerIndent+inner) <= 88 {
			return "_AfterValidator(\n" + innerIndent + inner + "\n" + elemIndent + ")"
		}
		// inner is also too long — try to wrap the factory call inside it.
		factoryWrapped := formatFactoryCall(inner, innerIndent)
		if factoryWrapped != "" {
			return "_AfterValidator(\n" + innerIndent + factoryWrapped + "\n" + elemIndent + ")"
		}
	}
	return s
}

// formatBracketElement formats a single list[...]/dict[...] element type at
// elemIndent, matching ruff's style: if "elem," fits at elemIndent it is
// returned unchanged; if it's an _Annotated[...] that doesn't fit, it is
// split one part per line (mirroring the top-level _Annotated[...] case in
// Field.TypeAnnotationFormatted). Other overlong element types are returned
// unchanged — best effort, since no further split rule is defined for them.
func formatBracketElement(s, elemIndent string) string {
	if len(elemIndent+s+",") <= 88 {
		return s
	}
	if !strings.HasPrefix(s, "_Annotated[") || !strings.HasSuffix(s, "]") {
		return s
	}
	inner := s[len("_Annotated[") : len(s)-1]
	innerIndent := elemIndent + "    "
	parts := splitTopLevelCommas(inner)
	var sb strings.Builder
	sb.WriteString("_Annotated[\n")
	for _, p := range parts {
		trimmed := strings.TrimSpace(p)
		formatted := formatAnnotationElement(trimmed, innerIndent)
		sb.WriteString(innerIndent + formatted + ",\n")
	}
	sb.WriteString(elemIndent + "]")
	return sb.String()
}

// formatFactoryCall wraps a factory(args) call when it doesn't fit on one
// line at indent. Two strategies are tried in order:
//  1. All args on one inner line (ruff's preferred form when they fit).
//  2. One arg per line with trailing commas (ruff's magic-trailing-comma form
//     when the combined args don't fit).
//
// Returns "" if neither strategy produces a result ≤ 88 chars per line.
func formatFactoryCall(s, indent string) string {
	parenIdx := strings.Index(s, "(")
	if parenIdx < 0 || !strings.HasSuffix(s, ")") {
		return ""
	}
	factory := s[:parenIdx]
	args := s[parenIdx+1 : len(s)-1]
	innerIndent := indent + "    "

	// Strategy 1: all args on one inner line.
	if len(innerIndent+args) <= 88 {
		return factory + "(\n" + innerIndent + args + "\n" + indent + ")"
	}

	// Strategy 2: one arg per line (magic trailing comma).
	parts := splitTopLevelCommas(args)
	if len(parts) > 1 {
		allFit := true
		for _, p := range parts {
			if len(innerIndent+strings.TrimSpace(p)+",") > 88 {
				allFit = false
				break
			}
		}
		if allFit {
			var sb strings.Builder
			sb.WriteString(factory + "(\n")
			for _, p := range parts {
				sb.WriteString(innerIndent + strings.TrimSpace(p) + ",\n")
			}
			sb.WriteString(indent + ")")
			return sb.String()
		}
	}

	// Strategy 3: lambda body wrap — used when the first argument is a
	// "lambda v: body" whose body is too long for a single line at innerIndent.
	// Ruff wraps it as:
	//
	//   factory(
	//       lambda v: (
	//           body           ← or split at or/and
	//       ),
	//       other_args,
	//   )
	if len(parts) >= 1 {
		firstArg := strings.TrimSpace(parts[0])
		if wrappedLambda := formatLambdaArg(firstArg, innerIndent); wrappedLambda != "" {
			restFit := true
			for _, p := range parts[1:] {
				if len(innerIndent+strings.TrimSpace(p)+",") > 88 {
					restFit = false
					break
				}
			}
			if restFit {
				var sb strings.Builder
				sb.WriteString(factory + "(\n")
				sb.WriteString(innerIndent + wrappedLambda + ",\n")
				for _, p := range parts[1:] {
					sb.WriteString(innerIndent + strings.TrimSpace(p) + ",\n")
				}
				sb.WriteString(indent + ")")
				return sb.String()
			}
		}
	}

	return ""
}

// formatLambdaArg wraps a "lambda v: body" expression when body is too long
// for a single line at innerIndent. It first tries the single-line body form:
//
//	lambda v: (
//	    body
//	)
//
// If body itself doesn't fit, it splits at top-level or/and operators:
//
//	lambda v: (
//	    part1
//	    or part2
//	)
//
// Returns "" if no stable form is found.
func formatLambdaArg(s, innerIndent string) string {
	const prefix = "lambda v: "
	if !strings.HasPrefix(s, prefix) {
		return ""
	}
	// Only attempt wrapping when the whole lambda doesn't fit at innerIndent.
	if len(innerIndent+s+",") <= 88 {
		return ""
	}
	body := s[len(prefix):]
	bodyIndent := innerIndent + "    "

	// Try single-line body: "lambda v: (\n    body\n)"
	if len(bodyIndent+body) <= 88 {
		return "lambda v: (\n" + bodyIndent + body + "\n" + innerIndent + ")"
	}

	// Try splitting the body at top-level or/and operators.
	parts := splitBoolOps(body)
	if len(parts) <= 1 {
		return ""
	}
	for _, p := range parts {
		if len(bodyIndent+p) > 88 {
			return ""
		}
	}
	var sb strings.Builder
	sb.WriteString("lambda v: (\n")
	for _, p := range parts {
		sb.WriteString(bodyIndent + p + "\n")
	}
	sb.WriteString(innerIndent + ")")
	return sb.String()
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
