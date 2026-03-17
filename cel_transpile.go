package main

import (
	"fmt"
	"regexp"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/google/cel-go/cel"
	celast "github.com/google/cel-go/common/ast"
	"github.com/google/cel-go/common/operators"
	"github.com/google/cel-go/common/types/ref"
	"github.com/google/cel-go/ext"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/types/known/structpb"
)

// celRule holds the three fields extracted from a buf.validate Constraint message.
type celRule struct {
	ID         string
	Expression string
	Message    string // may be empty for string-returning expressions
}

// celEnvCache caches cel.Env instances to avoid rebuilding for every field.
type celEnvCache struct {
	mu   sync.Mutex
	envs map[string]*cel.Env
	base *cel.Env
}

func newCelEnvCache() *celEnvCache {
	base, err := buildBaseCelEnv()
	if err != nil {
		// Fallback to minimal env if base construction fails.
		base, _ = cel.NewEnv()
	}
	return &celEnvCache{
		envs: make(map[string]*cel.Env),
		base: base,
	}
}

func buildBaseCelEnv() (*cel.Env, error) {
	return cel.NewEnv(
		ext.Strings(),
		cel.Variable("now", cel.TimestampType),
		// unique() — member function on list returning bool
		cel.Function("unique",
			cel.MemberOverload("list_unique_bool",
				[]*cel.Type{cel.ListType(cel.DynType)},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isEmail
		cel.Function("isEmail",
			cel.MemberOverload("string_is_email_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isHostname
		cel.Function("isHostname",
			cel.MemberOverload("string_is_hostname_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isUri
		cel.Function("isUri",
			cel.MemberOverload("string_is_uri_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isUriRef
		cel.Function("isUriRef",
			cel.MemberOverload("string_is_uri_ref_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isNan
		cel.Function("isNan",
			cel.MemberOverload("double_is_nan_bool",
				[]*cel.Type{cel.DoubleType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") }))),
		// isInf — no arg version
		cel.Function("isInf",
			cel.MemberOverload("double_is_inf_bool",
				[]*cel.Type{cel.DoubleType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") })),
			cel.MemberOverload("double_int_is_inf_bool",
				[]*cel.Type{cel.DoubleType, cel.IntType},
				cel.BoolType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") }))),
		// isIp
		cel.Function("isIp",
			cel.MemberOverload("string_is_ip_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") })),
			cel.MemberOverload("string_int_is_ip_bool",
				[]*cel.Type{cel.StringType, cel.IntType},
				cel.BoolType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") }))),
		// isIpPrefix
		cel.Function("isIpPrefix",
			cel.MemberOverload("string_is_ip_prefix_bool",
				[]*cel.Type{cel.StringType},
				cel.BoolType,
				cel.UnaryBinding(func(v ref.Val) ref.Val { panic("stub") })),
			cel.MemberOverload("string_int_is_ip_prefix_bool",
				[]*cel.Type{cel.StringType, cel.IntType},
				cel.BoolType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") })),
			cel.MemberOverload("string_bool_is_ip_prefix_bool",
				[]*cel.Type{cel.StringType, cel.BoolType},
				cel.BoolType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") })),
			cel.MemberOverload("string_int_bool_is_ip_prefix_bool",
				[]*cel.Type{cel.StringType, cel.IntType, cel.BoolType},
				cel.BoolType,
				cel.FunctionBinding(func(args ...ref.Val) ref.Val { panic("stub") }))),
		// isHostAndPort
		cel.Function("isHostAndPort",
			cel.MemberOverload("string_bool_is_host_and_port_bool",
				[]*cel.Type{cel.StringType, cel.BoolType},
				cel.BoolType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") }))),
		// getField
		cel.Function("getField",
			cel.Overload("get_field_dyn",
				[]*cel.Type{cel.DynType, cel.StringType},
				cel.DynType,
				cel.BinaryBinding(func(v ref.Val, a ref.Val) ref.Val { panic("stub") }))),
	)
}

// forField returns (or builds and caches) a cel.Env with this = field type.
func (c *celEnvCache) forField(fd protoreflect.FieldDescriptor) (*cel.Env, error) {
	key := celFieldKey(fd)
	c.mu.Lock()
	defer c.mu.Unlock()
	if env, ok := c.envs[key]; ok {
		return env, nil
	}
	env, err := c.base.Extend(cel.Variable("this", celTypeForField(fd)))
	if err != nil {
		return nil, err
	}
	c.envs[key] = env
	return env, nil
}

// forMessage returns (or builds and caches) a cel.Env with this = dyn.
func (c *celEnvCache) forMessage() (*cel.Env, error) {
	const key = "_message_"
	c.mu.Lock()
	defer c.mu.Unlock()
	if env, ok := c.envs[key]; ok {
		return env, nil
	}
	env, err := c.base.Extend(cel.Variable("this", cel.DynType))
	if err != nil {
		return nil, err
	}
	c.envs[key] = env
	return env, nil
}

func celFieldKey(fd protoreflect.FieldDescriptor) string {
	if fd.IsMap() {
		return fmt.Sprintf("map_%d_%d", fd.MapKey().Kind(), fd.MapValue().Kind())
	}
	if fd.IsList() {
		return fmt.Sprintf("list_%d", fd.Kind())
	}
	// Message-kind fields need a key that includes the full type name so that
	// different message types (e.g. Timestamp vs Duration) don't share an env.
	if fd.Kind() == protoreflect.MessageKind {
		return fmt.Sprintf("msg_%s", fd.Message().FullName())
	}
	return fmt.Sprintf("scalar_%d", fd.Kind())
}

func celTypeForField(fd protoreflect.FieldDescriptor) *cel.Type {
	if fd.IsMap() {
		return cel.MapType(celTypeForKind(fd.MapKey().Kind()), celTypeForKind(fd.MapValue().Kind()))
	}
	if fd.IsList() {
		return cel.ListType(celTypeForKind(fd.Kind()))
	}
	// Map well-known protobuf message types to their concrete CEL types so
	// that temporal expressions (e.g. "this > now") type-check correctly.
	if fd.Kind() == protoreflect.MessageKind {
		switch string(fd.Message().FullName()) {
		case "google.protobuf.Timestamp":
			return cel.TimestampType
		case "google.protobuf.Duration":
			return cel.DurationType
		}
	}
	return celTypeForKind(fd.Kind())
}

func celTypeForKind(k protoreflect.Kind) *cel.Type {
	switch k {
	case protoreflect.BoolKind:
		return cel.BoolType
	case protoreflect.Int32Kind, protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind:
		return cel.IntType
	case protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return cel.UintType
	case protoreflect.FloatKind, protoreflect.DoubleKind:
		return cel.DoubleType
	case protoreflect.StringKind:
		return cel.StringType
	case protoreflect.BytesKind:
		return cel.BytesType
	case protoreflect.EnumKind:
		return cel.IntType
	default:
		return cel.DynType
	}
}

// operatorMap maps CEL internal operator names to Python operator strings.
var operatorMap = map[string]string{
	operators.Greater:       ">",
	operators.GreaterEquals: ">=",
	operators.Less:          "<",
	operators.LessEquals:    "<=",
	operators.Equals:        "==",
	operators.NotEquals:     "!=",
	operators.Add:           "+",
	operators.Subtract:      "-",
	operators.Multiply:      "*",
	operators.Divide:        "/",
	operators.Modulo:        "%",
	operators.LogicalAnd:    "and",
	operators.LogicalOr:     "or",
	operators.In:            "in",
	operators.OldIn:         "in",
}

// transpiler walks a CEL NavigableExpr and produces a Python expression string.
type transpiler struct {
	isMsg      bool              // false → "this" = "v"; true → "this" = "self"
	fieldNames map[string]string // proto name → Python name (for message-level)
	imports    map[string]bool   // _proto_types symbols needed
	compVars   map[string]bool   // comprehension iteration variables currently in scope
}

func (t *transpiler) node(e celast.NavigableExpr) (string, error) {
	switch e.Kind() {
	case celast.IdentKind:
		return t.ident(e)
	case celast.LiteralKind:
		return t.literal(e)
	case celast.SelectKind:
		return t.selectExpr(e)
	case celast.CallKind:
		return t.call(e)
	case celast.ListKind:
		return t.list(e)
	case celast.MapKind:
		return t.mapExpr(e)
	case celast.ComprehensionKind:
		return t.comprehension(e)
	default:
		return "", fmt.Errorf("unsupported expr kind %d", e.Kind())
	}
}

func (t *transpiler) ident(e celast.NavigableExpr) (string, error) {
	name := e.AsIdent()

	// Comprehension iteration variables (e.g. "x" in this.all(x, x > 0)).
	if t.compVars[name] {
		return name, nil
	}

	switch name {
	case "this":
		if t.isMsg {
			return "self", nil
		}
		return "v", nil
	case "now":
		t.imports["_cel_now"] = true
		return "_cel_now()", nil
	}
	return "", fmt.Errorf("unsupported ident %q", name)
}

func (t *transpiler) literal(e celast.NavigableExpr) (string, error) {
	v := e.AsLiteral()
	switch val := v.Value().(type) {
	case bool:
		if val {
			return "True", nil
		}
		return "False", nil
	case int64:
		return strconv.FormatInt(val, 10), nil
	case uint64:
		return strconv.FormatUint(val, 10), nil
	case float64:
		return formatPythonFloat(val), nil
	case string:
		return pyQuote(val), nil
	case []byte:
		return fmt.Sprintf("b%s", pyQuote(string(val))), nil
	case structpb.NullValue:
		return "None", nil
	default:
		return "", fmt.Errorf("unsupported literal type %T", v.Value())
	}
}

func (t *transpiler) selectExpr(e celast.NavigableExpr) (string, error) {
	s := e.AsSelect()
	children := e.Children()
	operand, err := t.node(children[0])
	if err != nil {
		return "", err
	}
	fieldName := s.FieldName()

	if s.IsTestOnly() {
		// has(this.field) — presence check
		if !t.isMsg {
			return "", fmt.Errorf("has() only supported at message level")
		}
		pyName := t.pyFieldName(fieldName)
		// No outer parens: "name" in self.model_fields_set  (parens from binaryOp
		// wrapping will be stripped by pycelCondLine at template time)
		return fmt.Sprintf("%q in self.model_fields_set", pyName), nil
	}

	if t.isMsg && operand == "self" {
		pyName := t.pyFieldName(fieldName)
		return fmt.Sprintf("self.%s", pyName), nil
	}
	return fmt.Sprintf("(%s).%s", operand, fieldName), nil
}

func (t *transpiler) pyFieldName(protoName string) string {
	if py, ok := t.fieldNames[protoName]; ok {
		return py
	}
	return protoName
}

func (t *transpiler) call(e celast.NavigableExpr) (string, error) {
	c := e.AsCall()
	children := e.Children()
	fn := c.FunctionName()

	// Index operator: a[b]
	if fn == operators.Index && len(children) == 2 {
		recv, err := t.node(children[0])
		if err != nil {
			return "", err
		}
		idx, err := t.node(children[1])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("(%s)[%s]", recv, idx), nil
	}

	// Binary operators (non-member, 2 children)
	if op, ok := operatorMap[fn]; ok && !c.IsMemberFunction() && len(children) == 2 {
		return t.binaryOp(children, op)
	}

	// Unary: logical not
	if fn == operators.LogicalNot && !c.IsMemberFunction() && len(children) == 1 {
		arg, err := t.node(children[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("not (%s)", arg), nil
	}

	// Unary: negate
	if fn == operators.Negate && !c.IsMemberFunction() && len(children) == 1 {
		arg, err := t.node(children[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("-(%s)", arg), nil
	}

	// Ternary: a ? b : c
	if fn == operators.Conditional && len(children) == 3 {
		cond, err := t.node(children[0])
		if err != nil {
			return "", err
		}
		then_, err := t.node(children[1])
		if err != nil {
			return "", err
		}
		else_, err := t.node(children[2])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("(%s if %s else %s)", then_, cond, else_), nil
	}

	// Member functions: recv.fn(args...)
	if c.IsMemberFunction() {
		target := children[0]
		recv, err := t.node(target)
		if err != nil {
			return "", err
		}
		// Carry the receiver's CEL type name so that overloaded functions
		// (e.g. getHours on Timestamp vs Duration) can dispatch correctly.
		recvTypeName := ""
		if rt := target.Type(); rt != nil {
			recvTypeName = rt.TypeName()
		}
		return t.memberFunc(fn, recv, recvTypeName, children[1:])
	}

	// Global functions
	return t.globalFunc(fn, children)
}

func (t *transpiler) binaryOp(children []celast.NavigableExpr, op string) (string, error) {
	lhs, err := t.node(children[0])
	if err != nil {
		return "", err
	}
	rhs, err := t.node(children[1])
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("(%s %s %s)", lhs, op, rhs), nil
}

func (t *transpiler) memberFunc(fn, recv, recvTypeName string, args []celast.NavigableExpr) (string, error) {
	// ── Timestamp member accessors ──────────────────────────────────────────
	//
	// tsGetterEntry.suffix is appended to the base expression (the receiver,
	// or _cel_ts_in_tz(recv, "tz") for a non-UTC timezone argument).
	// When needsParens is true the whole expression is wrapped in parens.
	type tsGetterEntry struct {
		suffix      string
		needsParens bool
	}
	tsGetters := map[string]tsGetterEntry{
		"getFullYear":     {".year", false},
		"getMonth":        {".month - 1", true},               // CEL 0-indexed
		"getDayOfMonth":   {".day - 1", true},                 // CEL 0-indexed
		"getDate":         {".day", false},                    // CEL 1-indexed convenience alias
		"getDayOfYear":    {".timetuple().tm_yday - 1", true}, // CEL 0-indexed
		"getDayOfWeek":    {".isoweekday() % 7", true},        // Sun=0 … Sat=6
		"getHours":        {".hour", false},
		"getMinutes":      {".minute", false},
		"getSeconds":      {".second", false},
		"getMilliseconds": {".microsecond // 1000", true},
	}
	if info, ok := tsGetters[fn]; ok && recvTypeName == "google.protobuf.Timestamp" {
		base, err := t.tsGetterBase(recv, args)
		if err != nil {
			return "", fmt.Errorf("%s: %w", fn, err)
		}
		result := base + info.suffix
		if info.needsParens {
			return "(" + result + ")", nil
		}
		return result, nil
	}

	// ── Duration member accessors ────────────────────────────────────────────
	//
	// CEL duration getters return TOTAL units (not calendar components):
	//   getHours()        → total hours truncated to int
	//   getMinutes()      → total minutes truncated to int
	//   getSeconds()      → total seconds truncated to int
	//   getMilliseconds() → total milliseconds truncated to int
	if recvTypeName == "google.protobuf.Duration" {
		durGetters := map[string]string{
			"getHours":        "_cel_dur_get_hours",
			"getMinutes":      "_cel_dur_get_minutes",
			"getSeconds":      "_cel_dur_get_seconds",
			"getMilliseconds": "_cel_dur_get_milliseconds",
		}
		if helper, ok := durGetters[fn]; ok {
			if len(args) != 0 {
				return "", fmt.Errorf("%s: expected 0 arguments for duration getter", fn)
			}
			t.imports[helper] = true
			return fmt.Sprintf("%s(%s)", helper, recv), nil
		}
	}

	switch fn {
	case "startsWith":
		if len(args) != 1 {
			return "", fmt.Errorf("startsWith: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("(%s).startswith(%s)", recv, arg), nil

	case "endsWith":
		if len(args) != 1 {
			return "", fmt.Errorf("endsWith: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("(%s).endswith(%s)", recv, arg), nil

	case "contains":
		if len(args) != 1 {
			return "", fmt.Errorf("contains: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("(%s in %s)", arg, recv), nil

	case "matches":
		if len(args) != 1 {
			return "", fmt.Errorf("matches: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		t.imports["_cel_matches"] = true
		return fmt.Sprintf("_cel_matches(%s, %s)", arg, recv), nil

	case "size":
		if len(args) != 0 {
			return "", fmt.Errorf("size: expected 0 args, got %d", len(args))
		}
		return fmt.Sprintf("len(%s)", recv), nil

	case "unique":
		if len(args) != 0 {
			return "", fmt.Errorf("unique: expected 0 args, got %d", len(args))
		}
		t.imports["_is_unique"] = true
		return fmt.Sprintf("_is_unique(%s)", recv), nil

	case "isEmail":
		if len(args) != 0 {
			return "", fmt.Errorf("isEmail: expected 0 args, got %d", len(args))
		}
		t.imports["_is_email"] = true
		return fmt.Sprintf("_is_email(%s)", recv), nil

	case "isIp":
		switch len(args) {
		case 0:
			t.imports["_is_ip"] = true
			return fmt.Sprintf("_is_ip(%s, 0)", recv), nil
		case 1:
			ver, err := t.node(args[0])
			if err != nil {
				return "", err
			}
			t.imports["_is_ip"] = true
			return fmt.Sprintf("_is_ip(%s, %s)", recv, ver), nil
		default:
			return "", fmt.Errorf("isIp: unexpected arg count %d", len(args))
		}

	case "isIpPrefix":
		switch len(args) {
		case 0:
			t.imports["_is_ip_prefix"] = true
			return fmt.Sprintf("_is_ip_prefix(%s, 0)", recv), nil
		case 1:
			ver, err := t.node(args[0])
			if err != nil {
				return "", err
			}
			t.imports["_is_ip_prefix"] = true
			return fmt.Sprintf("_is_ip_prefix(%s, %s)", recv, ver), nil
		case 2:
			ver, err := t.node(args[0])
			if err != nil {
				return "", err
			}
			strict, err := t.node(args[1])
			if err != nil {
				return "", err
			}
			t.imports["_is_ip_prefix"] = true
			return fmt.Sprintf("_is_ip_prefix(%s, %s, strict=%s)", recv, ver, strict), nil
		default:
			return "", fmt.Errorf("isIpPrefix: unexpected arg count %d", len(args))
		}

	case "isHostname":
		if len(args) != 0 {
			return "", fmt.Errorf("isHostname: expected 0 args, got %d", len(args))
		}
		t.imports["_is_hostname"] = true
		return fmt.Sprintf("_is_hostname(%s)", recv), nil

	case "isUri":
		if len(args) != 0 {
			return "", fmt.Errorf("isUri: expected 0 args, got %d", len(args))
		}
		t.imports["_is_uri"] = true
		return fmt.Sprintf("_is_uri(%s)", recv), nil

	case "isUriRef":
		if len(args) != 0 {
			return "", fmt.Errorf("isUriRef: expected 0 args, got %d", len(args))
		}
		t.imports["_is_uri_ref"] = true
		return fmt.Sprintf("_is_uri_ref(%s)", recv), nil

	case "isHostAndPort":
		if len(args) != 1 {
			return "", fmt.Errorf("isHostAndPort: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		t.imports["_is_host_and_port"] = true
		return fmt.Sprintf("_is_host_and_port(%s, %s)", recv, arg), nil

	case "isNan":
		if len(args) != 0 {
			return "", fmt.Errorf("isNan: expected 0 args, got %d", len(args))
		}
		t.imports["_is_nan"] = true
		return fmt.Sprintf("_is_nan(%s)", recv), nil

	case "isInf":
		switch len(args) {
		case 0:
			t.imports["_is_inf"] = true
			return fmt.Sprintf("_is_inf(%s)", recv), nil
		case 1:
			arg, err := t.node(args[0])
			if err != nil {
				return "", err
			}
			t.imports["_is_inf"] = true
			return fmt.Sprintf("_is_inf(%s, %s)", recv, arg), nil
		default:
			return "", fmt.Errorf("isInf: unexpected arg count %d", len(args))
		}

	default:
		return "", fmt.Errorf("unsupported member function %q", fn)
	}
}

func (t *transpiler) globalFunc(fn string, args []celast.NavigableExpr) (string, error) {
	switch fn {
	case "size":
		if len(args) != 1 {
			return "", fmt.Errorf("size: expected 1 arg, got %d", len(args))
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("len(%s)", arg), nil
	case "int":
		if len(args) != 1 {
			return "", fmt.Errorf("int: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("int(%s)", arg), nil
	case "uint":
		if len(args) != 1 {
			return "", fmt.Errorf("uint: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("int(%s)", arg), nil
	case "double":
		if len(args) != 1 {
			return "", fmt.Errorf("double: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("float(%s)", arg), nil
	case "string":
		if len(args) != 1 {
			return "", fmt.Errorf("string: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("str(%s)", arg), nil
	case "bool":
		if len(args) != 1 {
			return "", fmt.Errorf("bool: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("bool(%s)", arg), nil
	case "bytes":
		if len(args) != 1 {
			return "", fmt.Errorf("bytes: expected 1 arg")
		}
		arg, err := t.node(args[0])
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("bytes(%s)", arg), nil
	case "duration":
		if len(args) != 1 {
			return "", fmt.Errorf("duration: expected 1 argument")
		}
		if args[0].Kind() != celast.LiteralKind {
			return "", fmt.Errorf("duration: argument must be a string literal")
		}
		s, ok := args[0].AsLiteral().Value().(string)
		if !ok {
			return "", fmt.Errorf("duration: argument must be a string")
		}
		secs, err := parseCELDuration(s)
		if err != nil {
			return "", fmt.Errorf("duration(%q): %w", s, err)
		}
		t.imports["_cel_duration"] = true
		return fmt.Sprintf("_cel_duration(%s)", formatDurationSecs(secs)), nil
	case "timestamp":
		if len(args) != 1 {
			return "", fmt.Errorf("timestamp: expected 1 argument")
		}
		if args[0].Kind() != celast.LiteralKind {
			return "", fmt.Errorf("timestamp: argument must be a string literal")
		}
		s, ok := args[0].AsLiteral().Value().(string)
		if !ok {
			return "", fmt.Errorf("timestamp: argument must be a string")
		}
		t.imports["_cel_timestamp"] = true
		return fmt.Sprintf("_cel_timestamp(%s)", pyQuote(s)), nil
	case "type":
		return "", fmt.Errorf("type() not supported")
	case "getField":
		return "", fmt.Errorf("getField() not supported")
	default:
		return "", fmt.Errorf("unsupported global function %q", fn)
	}
}

func (t *transpiler) list(e celast.NavigableExpr) (string, error) {
	children := e.Children()
	parts := make([]string, len(children))
	for i, child := range children {
		s, err := t.node(child)
		if err != nil {
			return "", err
		}
		parts[i] = s
	}
	return "[" + joinStrings(parts, ", ") + "]", nil
}

func (t *transpiler) mapExpr(e celast.NavigableExpr) (string, error) {
	children := e.Children()
	if len(children)%2 != 0 {
		return "", fmt.Errorf("map expr has odd number of children")
	}
	var parts []string
	for i := 0; i < len(children); i += 2 {
		k, err := t.node(children[i])
		if err != nil {
			return "", err
		}
		v, err := t.node(children[i+1])
		if err != nil {
			return "", err
		}
		parts = append(parts, k+": "+v)
	}
	return "{" + joinStrings(parts, ", ") + "}", nil
}

// ─── comprehension transpilation ────────────────────────────────────────────

// comprehension recognises the canonical desugaring produced by the five
// CEL macro families (all, exists, exists_one, filter, map) and emits
// equivalent Python generator / comprehension expressions.
//
// CEL children order for ComprehensionKind:
//
//	[0] iterRange  [1] accuInit  [2] loopCondition  [3] loopStep  [4] result
//
// Patterns keyed on accuInit:
//
//	Literal(true)   → all(pred for v in range)
//	Literal(false)  → any(pred for v in range)
//	Literal(0)      → sum(1 for v in range if pred) == 1
//	empty list      → [elem for v in range [if pred]]   (filter / map)
func (t *transpiler) comprehension(e celast.NavigableExpr) (string, error) {
	c := e.AsComprehension()
	iterVar := c.IterVar()

	children := e.Children()
	if len(children) < 5 {
		return "", fmt.Errorf("comprehension: expected 5 children, got %d", len(children))
	}
	iterRangeExpr := children[0]
	accuInitExpr := children[1]
	// children[2] = loopCondition (not used directly)
	loopStepExpr := children[3]
	// children[4] = result (not used for the standard macros)

	// Transpile the range expression before adding iterVar to scope.
	iterRange, err := t.node(iterRangeExpr)
	if err != nil {
		return "", fmt.Errorf("comprehension range: %w", err)
	}

	// Register the iteration variable so the body can reference it.
	if t.compVars == nil {
		t.compVars = make(map[string]bool)
	}
	t.compVars[iterVar] = true
	defer func() { delete(t.compVars, iterVar) }()

	switch {
	case isLiteralBool(accuInitExpr, true):
		// all(x, pred) → all(pred for x in range)
		pred, err := extractAllPred(loopStepExpr)
		if err != nil {
			return "", fmt.Errorf("all() pred: %w", err)
		}
		predStr, err := t.node(pred)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("all(%s for %s in %s)", predStr, iterVar, iterRange), nil

	case isLiteralBool(accuInitExpr, false):
		// exists(x, pred) → any(pred for x in range)
		pred, err := extractExistsPred(loopStepExpr)
		if err != nil {
			return "", fmt.Errorf("exists() pred: %w", err)
		}
		predStr, err := t.node(pred)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("any(%s for %s in %s)", predStr, iterVar, iterRange), nil

	case isLiteralInt(accuInitExpr, 0):
		// exists_one(x, pred) → sum(1 for x in range if pred) == 1
		pred, err := extractExistsOnePred(loopStepExpr)
		if err != nil {
			return "", fmt.Errorf("exists_one() pred: %w", err)
		}
		predStr, err := t.node(pred)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("sum(1 for %s in %s if %s) == 1", iterVar, iterRange, predStr), nil

	case isEmptyList(accuInitExpr):
		// filter(x, pred) or map(x, fn) or map(x, pred, fn)
		return t.comprehensionList(iterVar, iterRange, loopStepExpr)

	default:
		return "", fmt.Errorf("unrecognised comprehension pattern (accuInit kind=%d)", accuInitExpr.Kind())
	}
}

// comprehensionList handles filter and map comprehensions, both of which start
// with an empty-list accumulator. The distinction comes from the loop step:
//
//	plain map  : __result__ + [fn]                 (unconditional Add)
//	filter/map : pred ? __result__ + [elem] : __result__   (Conditional)
func (t *transpiler) comprehensionList(iterVar, iterRange string, loopStep celast.NavigableExpr) (string, error) {
	if loopStep.Kind() != celast.CallKind {
		return "", fmt.Errorf("list comprehension: expected call in loop_step")
	}
	fn := loopStep.AsCall().FunctionName()
	children := loopStep.Children()

	switch fn {
	case operators.Add:
		// plain map(x, transform) → [transform for x in range]
		if len(children) < 2 {
			return "", fmt.Errorf("map loop_step: too few children")
		}
		elem, err := extractSingleListElement(children[1])
		if err != nil {
			return "", fmt.Errorf("map loop_step: %w", err)
		}
		elemStr, err := t.node(elem)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("[%s for %s in %s]", elemStr, iterVar, iterRange), nil

	case operators.Conditional:
		// filter(x, pred) or map(x, pred, fn) → [elem for x in range if pred]
		if len(children) < 3 {
			return "", fmt.Errorf("filter/map loop_step: too few children (got %d)", len(children))
		}
		pred := children[0]
		thenBranch := children[1]

		predStr, err := t.node(pred)
		if err != nil {
			return "", fmt.Errorf("filter/map pred: %w", err)
		}
		// thenBranch = __result__ + [elem]
		elem, err := extractMapThenElem(thenBranch)
		if err != nil {
			return "", fmt.Errorf("filter/map then-branch: %w", err)
		}
		elemStr, err := t.node(elem)
		if err != nil {
			return "", err
		}
		return fmt.Sprintf("[%s for %s in %s if %s]", elemStr, iterVar, iterRange, predStr), nil

	default:
		return "", fmt.Errorf("list comprehension: unexpected loop_step function %q", fn)
	}
}

// ─── pattern helpers ─────────────────────────────────────────────────────────

// isLiteralBool reports whether e is a boolean literal with the given value.
func isLiteralBool(e celast.NavigableExpr, want bool) bool {
	if e.Kind() != celast.LiteralKind {
		return false
	}
	b, ok := e.AsLiteral().Value().(bool)
	return ok && b == want
}

// isLiteralInt reports whether e is an integer literal equal to want.
func isLiteralInt(e celast.NavigableExpr, want int64) bool {
	if e.Kind() != celast.LiteralKind {
		return false
	}
	n, ok := e.AsLiteral().Value().(int64)
	return ok && n == want
}

// isEmptyList reports whether e is a list literal with no elements.
func isEmptyList(e celast.NavigableExpr) bool {
	return e.Kind() == celast.ListKind && len(e.Children()) == 0
}

// extractAllPred extracts the user predicate from the all() loop step.
//
// In cel-go v0.27+, all() desugars to:  __result__ && pred
// The predicate is placed directly as children[1] without the
// @not_strictly_false wrapper that earlier versions used.
func extractAllPred(loopStep celast.NavigableExpr) (celast.NavigableExpr, error) {
	if loopStep.Kind() != celast.CallKind || loopStep.AsCall().FunctionName() != operators.LogicalAnd {
		return nil, fmt.Errorf("expected _&&_ in all loop_step, got kind=%d", loopStep.Kind())
	}
	children := loopStep.Children()
	if len(children) < 2 {
		return nil, fmt.Errorf("all loop_step: too few children")
	}
	return children[1], nil
}

// extractExistsPred extracts the predicate from the exists() loop step.
//
// exists desugars to:  __result__ || pred
// pred is children[1].
func extractExistsPred(loopStep celast.NavigableExpr) (celast.NavigableExpr, error) {
	if loopStep.Kind() != celast.CallKind || loopStep.AsCall().FunctionName() != operators.LogicalOr {
		return nil, fmt.Errorf("expected _||_ in exists loop_step")
	}
	children := loopStep.Children()
	if len(children) < 2 {
		return nil, fmt.Errorf("exists loop_step: too few children")
	}
	return children[1], nil
}

// extractExistsOnePred extracts the predicate from the exists_one() loop step.
//
// exists_one desugars to:  pred ? __result__ + 1 : __result__
// pred is children[0] (the condition of the ternary).
func extractExistsOnePred(loopStep celast.NavigableExpr) (celast.NavigableExpr, error) {
	if loopStep.Kind() != celast.CallKind || loopStep.AsCall().FunctionName() != operators.Conditional {
		return nil, fmt.Errorf("expected ternary in exists_one loop_step")
	}
	children := loopStep.Children()
	if len(children) < 1 {
		return nil, fmt.Errorf("exists_one loop_step: no children")
	}
	return children[0], nil
}

// extractSingleListElement extracts the single element from a list literal [e].
func extractSingleListElement(e celast.NavigableExpr) (celast.NavigableExpr, error) {
	if e.Kind() != celast.ListKind {
		return nil, fmt.Errorf("expected list, got kind=%d", e.Kind())
	}
	elems := e.Children()
	if len(elems) != 1 {
		return nil, fmt.Errorf("expected 1-element list, got %d", len(elems))
	}
	return elems[0], nil
}

// extractMapThenElem extracts the element being appended in the then-branch of
// a filter or map loop step.
//
// then-branch = __result__ + [elem]   so elem lives at children[1].children[0].
func extractMapThenElem(thenBranch celast.NavigableExpr) (celast.NavigableExpr, error) {
	if thenBranch.Kind() != celast.CallKind || thenBranch.AsCall().FunctionName() != operators.Add {
		return nil, fmt.Errorf("expected _+_ in then-branch, got kind=%d", thenBranch.Kind())
	}
	children := thenBranch.Children()
	if len(children) < 2 {
		return nil, fmt.Errorf("then-branch: too few children")
	}
	return extractSingleListElement(children[1])
}

// ─── timestamp getter helper ─────────────────────────────────────────────────

// tsGetterBase returns the Python base expression to which a timestamp getter
// suffix is appended. With no arguments the base is the receiver itself
// (assumed UTC). With a literal "UTC" argument the base is also the receiver.
// With any other literal string argument the base is _cel_ts_in_tz(recv, tz).
func (t *transpiler) tsGetterBase(recv string, args []celast.NavigableExpr) (string, error) {
	switch len(args) {
	case 0:
		return recv, nil
	case 1:
		if args[0].Kind() != celast.LiteralKind {
			return "", fmt.Errorf("timezone argument must be a string literal")
		}
		tz, ok := args[0].AsLiteral().Value().(string)
		if !ok {
			return "", fmt.Errorf("timezone argument must be a string")
		}
		if tz == "UTC" {
			return recv, nil
		}
		t.imports["_cel_ts_in_tz"] = true
		return fmt.Sprintf("_cel_ts_in_tz(%s, %s)", recv, pyQuote(tz)), nil
	default:
		return "", fmt.Errorf("expected 0 or 1 arguments")
	}
}

// ─── temporal helpers ────────────────────────────────────────────────────────

// parseCELDuration converts a CEL/Go duration string (e.g. "1h30m", "300s",
// "1.5s") to total seconds as float64 using Go's time.ParseDuration.
func parseCELDuration(s string) (float64, error) {
	d, err := time.ParseDuration(s)
	if err != nil {
		return 0, err
	}
	return d.Seconds(), nil
}

// formatDurationSecs formats a float64 seconds value as a clean Python numeric
// literal for use in _cel_duration(N).
func formatDurationSecs(secs float64) string {
	return strconv.FormatFloat(secs, 'g', -1, 64)
}

// isCELNullSafeField reports whether field-level CEL validators for fd need a
// "v is None or (...)" guard. This is true for non-repeated message-kind
// fields, which include all WKT types (Timestamp → datetime, Duration →
// timedelta) and are represented as Optional in generated Python.
func isCELNullSafeField(fd protoreflect.FieldDescriptor) bool {
	return !fd.IsList() && !fd.IsMap() && fd.Kind() == protoreflect.MessageKind
}

func joinStrings(parts []string, sep string) string {
	result := ""
	for i, p := range parts {
		if i > 0 {
			result += sep
		}
		result += p
	}
	return result
}

// importList converts the imports map to a sorted slice.
func importList(m map[string]bool) []string {
	if len(m) == 0 {
		return nil
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// sanitiseRuleID replaces non-identifier characters with underscores.
var sanitiseRuleIDRe = regexp.MustCompile(`[^a-zA-Z0-9_]`)

func sanitiseRuleID(id string) string {
	return sanitiseRuleIDRe.ReplaceAllString(id, "_")
}

// extractCelRule reads id/expression/message from a Constraint proto message.
func extractCelRule(m protoreflect.Message) celRule {
	var rule celRule
	m.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		switch string(fd.Name()) {
		case "id":
			rule.ID = v.String()
		case "expression":
			rule.Expression = v.String()
		case "message":
			rule.Message = v.String()
		}
		return true
	})
	return rule
}

// transpileCELField attempts to transpile a single field-level CEL rule.
func transpileCELField(rule celRule, field protoreflect.FieldDescriptor, cache *celEnvCache) (CelValidator, error) {
	env, err := cache.forField(field)
	if err != nil {
		return CelValidator{}, fmt.Errorf("build env: %w", err)
	}

	ast, issues := env.Compile(rule.Expression)
	if issues.Err() != nil {
		return CelValidator{}, issues.Err()
	}

	returnsBool, err := resolveOutputType(ast.OutputType())
	if err != nil {
		return CelValidator{}, err
	}

	nav := celast.NavigateAST(ast.NativeRep())
	t := &transpiler{isMsg: false, imports: map[string]bool{}}
	pyExpr, err := t.node(nav)
	if err != nil {
		return CelValidator{}, err
	}

	return CelValidator{
		RuleID:      sanitiseRuleID(rule.ID),
		Expression:  pyExpr,
		Message:     rule.Message,
		ReturnsBool: returnsBool,
		NullSafe:    isCELNullSafeField(field),
		Imports:     importList(t.imports),
	}, nil
}

// transpileCELMessage attempts to transpile a single message-level CEL rule.
func transpileCELMessage(rule celRule, fieldNameMap map[string]string, cache *celEnvCache) (CelValidator, error) {
	env, err := cache.forMessage()
	if err != nil {
		return CelValidator{}, fmt.Errorf("build env: %w", err)
	}

	ast, issues := env.Compile(rule.Expression)
	if issues.Err() != nil {
		return CelValidator{}, issues.Err()
	}

	returnsBool, err := resolveOutputType(ast.OutputType())
	if err != nil {
		return CelValidator{}, err
	}

	nav := celast.NavigateAST(ast.NativeRep())
	t := &transpiler{isMsg: true, fieldNames: fieldNameMap, imports: map[string]bool{}}
	pyExpr, err := t.node(nav)
	if err != nil {
		return CelValidator{}, err
	}

	return CelValidator{
		RuleID:      sanitiseRuleID(rule.ID),
		Expression:  pyExpr,
		Message:     rule.Message,
		ReturnsBool: returnsBool,
		Imports:     importList(t.imports),
	}, nil
}

// resolveOutputType determines whether the CEL expression returns bool or string.
// DynType satisfies IsAssignableType(BoolType) in cel-go, so it is handled by
// the first branch; no special-case is needed.
func resolveOutputType(outputType *cel.Type) (bool, error) {
	if outputType.IsAssignableType(cel.BoolType) {
		return true, nil
	}
	if outputType.IsAssignableType(cel.StringType) {
		return false, nil
	}
	return false, fmt.Errorf("expression output type %s is not bool or string", outputType.String())
}
