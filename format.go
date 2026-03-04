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
