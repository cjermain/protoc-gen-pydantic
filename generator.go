package main

import (
	"bytes"
	"fmt"
	"io"
	"path/filepath"
	"sort"
	"strings"

	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
	"google.golang.org/protobuf/types/descriptorpb"
	"google.golang.org/protobuf/types/dynamicpb"
)

type generator struct {
	file            File
	enums           []Enum
	messages        []Message
	externalImports []string
	relativeImports []string
	stdImports      map[string]bool
	runtimeImports  map[string]bool

	customOptionFields []CustomOptionField

	config               GeneratorConfig
	resolver             *protoregistry.Types
	fieldConstraintExt   protoreflect.ExtensionDescriptor
	messageConstraintExt protoreflect.ExtensionDescriptor // buf.validate.message extension
	celEnvCache          *celEnvCache                     // cached CEL environments
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
	for _, msg := range e.messages {
		if messageHasEnumOptions(msg) {
			return true
		}
	}
	return false
}

func messageHasEnumOptions(msg Message) bool {
	for _, enum := range msg.NestedEnums {
		if enum.HasOptions() {
			return true
		}
	}
	for _, nested := range msg.NestedMessages {
		if messageHasEnumOptions(nested) {
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
	if e.stdImports["_ModelValidator"] {
		symbols = append(symbols, "model_validator as _model_validator")
	}
	return formatImportBlock("from pydantic import ", symbols)
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
		enum, err := e.processEnum(ed, ep, sourceCodeInfo, path)
		if err != nil {
			return err
		}
		e.enums = append(e.enums, enum)
	}
	for i := range file.Messages().Len() {
		msgd := file.Messages().Get(i)
		msgp := fdp.GetMessageType()[i]
		path := []int32{4, int32(i)}
		msg, err := e.processMessage(msgd, msgp, sourceCodeInfo, path)
		if err != nil {
			return err
		}
		if msg.Name != "" {
			e.messages = append(e.messages, msg)
		}
	}
	return nil
}

func (e *generator) processEnum(
	enum protoreflect.EnumDescriptor,
	enumProto *descriptorpb.EnumDescriptorProto,
	sourceCodeInfo *descriptorpb.SourceCodeInfo,
	path []int32,
) (Enum, error) {
	def := Enum{
		Name:   string(enum.Name()),
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
	return def, nil
}

func (e *generator) processMessage(
	msg protoreflect.MessageDescriptor,
	msgProto *descriptorpb.DescriptorProto,
	sourceCodeInfo *descriptorpb.SourceCodeInfo,
	path []int32,
) (Message, error) {
	if msg.IsMapEntry() {
		return Message{}, nil
	}

	def := Message{
		Name:   string(msg.Name()),
		Fields: []Field{},
	}
	def.LeadingComments, def.TrailingComments = extractComments(sourceCodeInfo, path)

	// NOTE: Process nested enums and messages before the fields.
	for i, nest := range iter(msg.Enums()) {
		nestPath := append(append([]int32{}, path...), 4, int32(i))
		nestedEnum, err := e.processEnum(nest, msgProto.GetEnumType()[i], sourceCodeInfo, nestPath)
		if err != nil {
			return Message{}, fmt.Errorf("enum %s: %w", string(nest.Name()), err)
		}
		def.NestedEnums = append(def.NestedEnums, nestedEnum)
	}

	for i, nest := range iter(msg.Messages()) {
		nestPath := append(append([]int32{}, path...), 3, int32(i))
		nestedMsg, err := e.processMessage(nest, msgProto.GetNestedType()[i], sourceCodeInfo, nestPath)
		if err != nil {
			return Message{}, fmt.Errorf("message %s: %w", string(nest.Name()), err)
		}
		if nestedMsg.Name != "" {
			def.NestedMessages = append(def.NestedMessages, nestedMsg)
		}
	}

	for i, field := range iter(msg.Fields()) {
		typ, err := e.resolveType(def.Name, field)
		if err != nil {
			return Message{}, fmt.Errorf("field %s.%s: %w", def.Name, field.Name(), err)
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
			Name:       name,
			Alias:      alias,
			Type:       typ,
			NeedsQuote: fieldNeedsQuote(field),
			Optional:   field.HasOptionalKeyword(),
			Default:    e.resolveDefault(field),
			OneOf:      oneOf,
		}
		f.LeadingComments, f.TrailingComments = extractComments(sourceCodeInfo, fieldPath)
		if !e.config.DisableValidate {
			if fp := msgProto.GetField()[i]; fp.GetOptions() != nil {
				f.Constraints = e.extractFieldConstraints(fp.GetOptions(), field)
			}
			e.applyConstraintTypeOverrides(&f)
			isScalar := !field.IsList() && !field.IsMap() &&
				field.Kind() != protoreflect.MessageKind &&
				field.Kind() != protoreflect.EnumKind
			isNotOptional := !field.HasOptionalKeyword() && field.ContainingOneof() == nil
			hasConst := f.Constraints != nil &&
				(f.Constraints.ConstLiteral != nil || f.Constraints.ConstFloatLiteral != nil)
			ignoreZero := f.Constraints != nil && f.Constraints.HasIgnore
			if isScalar && isNotOptional && !hasConst && !ignoreZero &&
				f.Constraints.ZeroValueFails(field.Kind()) {
				f.ConstrainedRequired = true
				f.Default = ""
			}
		}
		def.Fields = append(def.Fields, f)
	}

	// Collect unique oneof groups for validator generation.
	seen := map[string]bool{}
	for _, f := range def.Fields {
		if f.OneOf != nil && !seen[f.OneOf.Name] {
			seen[f.OneOf.Name] = true
			def.OneOfGroups = append(def.OneOfGroups, *f.OneOf)
		}
	}
	if len(def.OneOfGroups) > 0 {
		e.addStdImport("_ModelValidator")
	}

	// Extract message-level CEL constraints.
	if !e.config.DisableValidate {
		if e.messageConstraintExt != nil && msgProto.GetOptions() != nil && e.celEnvCache != nil {
			e.extractMessageCEL(msgProto.GetOptions(), &def)
		}
		if len(def.CelValidators) > 0 {
			e.addStdImport("_ModelValidator")
			for _, cv := range def.CelValidators {
				for _, imp := range cv.Imports {
					e.addRuntimeImport(imp)
				}
			}
		}
	}

	e.addStdImport("_BaseModel")
	e.addStdImport("_Field")
	return def, nil
}

// extractMessageCEL reads buf.validate.message CEL rules from MessageOptions.
// Successful transpilations go to def.CelValidators; failures to def.DroppedCelConstraints.
func (e *generator) extractMessageCEL(opts *descriptorpb.MessageOptions, def *Message) {
	if opts == nil || e.messageConstraintExt == nil {
		return
	}

	raw, err := proto.Marshal(opts)
	if err != nil {
		return
	}
	extType := dynamicpb.NewExtensionType(e.messageConstraintExt)
	resolver := &protoregistry.Types{}
	_ = resolver.RegisterExtension(extType)
	resolved := &descriptorpb.MessageOptions{}
	if err := (proto.UnmarshalOptions{Resolver: resolver}).Unmarshal(raw, resolved); err != nil {
		return
	}

	// Build proto→Python field name map for has() and this.field resolution.
	fieldNameMap := make(map[string]string, len(def.Fields))
	for _, f := range def.Fields {
		if f.Alias != "" {
			fieldNameMap[f.Alias] = f.Name // proto name → Python name (e.g. "float" → "float_")
		} else {
			fieldNameMap[f.Name] = f.Name
		}
	}

	resolved.ProtoReflect().Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		if !fd.IsExtension() || string(fd.Name()) != "message" {
			return true
		}
		v.Message().Range(func(rfd protoreflect.FieldDescriptor, rv protoreflect.Value) bool {
			switch string(rfd.Name()) {
			case "cel":
				list := rv.List()
				for i := 0; i < list.Len(); i++ {
					rule := extractCelRule(list.Get(i).Message())
					cv, cerr := transpileCELMessage(rule, fieldNameMap, e.celEnvCache)
					if cerr != nil {
						def.DroppedCelConstraints = append(def.DroppedCelConstraints,
							fmt.Sprintf("cel id=%q (not translated: %v)", rule.ID, cerr))
					} else {
						def.CelValidators = append(def.CelValidators, cv)
					}
				}
			case "cel_expression":
				// Shorthand form: each string entry is both the id and the expression.
				// The message is also set to the expression so validation errors are
				// self-describing (protovalidate: "message derived from expression").
				list := rv.List()
				for i := 0; i < list.Len(); i++ {
					expr := list.Get(i).String()
					rule := celRule{ID: expr, Expression: expr, Message: expr}
					cv, cerr := transpileCELMessage(rule, fieldNameMap, e.celEnvCache)
					if cerr != nil {
						def.DroppedCelConstraints = append(def.DroppedCelConstraints,
							fmt.Sprintf("cel id=%q (not translated: %v)", rule.ID, cerr))
					} else {
						def.CelValidators = append(def.CelValidators, cv)
					}
				}
			}
			return true
		})
		return false
	})
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
	// For nested types (e.g. "Outer.Inner"), import only the top-level class.
	importName := typeName
	if dot := strings.Index(typeName, "."); dot >= 0 {
		importName = typeName[:dot]
	}
	targetPath := string(targetFile.Path())
	moduleName := strings.TrimSuffix(filepath.Base(targetPath), ".proto") + "_pydantic"
	if string(sourceFile.Package()) == string(targetFile.Package()) {
		e.addRelativeImport(fmt.Sprintf("from .%s import %s", moduleName, importName))
	} else {
		// Use the file path (not package name) to derive the Python module path.
		dir := filepath.Dir(targetPath)
		pyPkg := strings.ReplaceAll(dir, string(filepath.Separator), ".")
		e.addExternalImport(fmt.Sprintf("from %s.%s import %s", pyPkg, moduleName, importName))
	}
	return nil
}

// fieldNeedsQuote reports whether the resolved Python type for the given
// protobuf field descriptor contains a user-defined class name (message or
// enum) and therefore requires a quoted forward-reference annotation.
func fieldNeedsQuote(field protoreflect.FieldDescriptor) bool {
	candidate := field
	if field.IsMap() {
		candidate = field.MapValue()
	}
	switch candidate.Kind() {
	case protoreflect.EnumKind:
		return true
	case protoreflect.MessageKind:
		_, isWKT := wellKnownTypes[string(candidate.Message().FullName())]
		return !isWKT
	}
	return false
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
		typeName := resolveQualifiedName(enum)
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

	typeName := resolveQualifiedName(msg)
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
		return "default=None"
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
		return "default=None"
	}

	// Scalar defaults.
	switch field.Kind() {
	case protoreflect.BoolKind:
		return "default=False"
	case protoreflect.Int32Kind, protoreflect.Uint32Kind, protoreflect.Fixed32Kind,
		protoreflect.Sint32Kind, protoreflect.Sfixed32Kind,
		protoreflect.Int64Kind, protoreflect.Sint64Kind, protoreflect.Sfixed64Kind,
		protoreflect.Uint64Kind, protoreflect.Fixed64Kind:
		return "default=0"
	case protoreflect.DoubleKind, protoreflect.FloatKind:
		return "default=0.0"
	case protoreflect.StringKind:
		return `default=""`
	case protoreflect.BytesKind:
		return `default=b""`
	default:
		return "default=None"
	}
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
