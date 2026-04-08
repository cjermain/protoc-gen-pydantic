package main

import (
	"flag"
	"fmt"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"text/template"

	"google.golang.org/protobuf/compiler/protogen"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
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

func init() {
	tmpl = template.Must(template.New("pydantic").Funcs(template.FuncMap{
		"pyQuote": pyQuote,
		"dict": func(args ...interface{}) map[string]interface{} {
			m := make(map[string]interface{}, len(args)/2)
			for i := 0; i < len(args); i += 2 {
				m[args[i].(string)] = args[i+1]
			}
			return m
		},
		// pyOneofSetLine returns a ruff-formatted "_set = [...]" assignment line for a
		// oneof validator. bi is the class-body indent; the method body adds 4 more
		// spaces. Three forms are tried in order to stay within ruff's 88-char limit:
		//  1. Entire expression on one line.
		//  2. Brackets split but comprehension body on one inner line.
		//  3. f / for / if each on their own line (ruff's fallback for long tuples).
		"pyOneofSetLine": func(bi string, fieldNames []string) string {
			bodyIndent := bi + "    "
			innerIndent := bi + "        "
			parts := make([]string, len(fieldNames))
			for i, n := range fieldNames {
				parts[i] = fmt.Sprintf("%q", n)
			}
			tuple := "(" + strings.Join(parts, ", ")
			if len(fieldNames) == 1 {
				tuple += ","
			}
			tuple += ")"
			// Case 1: entire expression fits on one line.
			single := bodyIndent + "_set = [f for f in " + tuple + " if getattr(self, f) is not None]"
			if len(single) <= 88 {
				return single
			}
			// Case 2: body fits on one line inside the brackets.
			bodyLine := innerIndent + "f for f in " + tuple + " if getattr(self, f) is not None"
			if len(bodyLine) <= 88 {
				return bodyIndent + "_set = [\n" +
					bodyLine + "\n" +
					bodyIndent + "]"
			}
			// Case 3: f / for / if on separate lines.
			return bodyIndent + "_set = [\n" +
				innerIndent + "f\n" +
				innerIndent + "for f in " + tuple + "\n" +
				innerIndent + "if getattr(self, f) is not None\n" +
				bodyIndent + "]"
		},
		// pycelCondLine returns the ruff-stable `if not (expr):` line for a
		// message-level bool-returning CEL validator. Outer parens on the
		// expression are stripped and long conditions are split at boolean
		// operators using ruff's binary-operator continuation style.
		"pycelCondLine": pycelCondLine,
		// pyRaiseOneof returns a ruff-formatted raise ValueError(...) statement for a
		// oneof validator. The single-line form is used when it fits within 88
		// characters; otherwise the argument is placed on its own indented line.
		"pyRaiseOneof": func(bi string, name string) string {
			raiseIndent := bi + "        "
			single := raiseIndent + `raise ValueError(f"oneof '` + name + `': only one field may be set, got {_set!r}")`
			if len(single) <= 88 {
				return single
			}
			argIndent := bi + "            "
			return raiseIndent + "raise ValueError(\n" +
				argIndent + `f"oneof '` + name + `': only one field may be set, got {_set!r}"` + "\n" +
				raiseIndent + ")"
		},
	}).Parse(modelTemplate))
}

func main() {
	var flags flag.FlagSet
	preservingProtoFieldName := flags.Bool("preserving_proto_field_name", true, "")
	autoTrimEnumPrefix := flags.Bool("auto_trim_enum_prefix", true, "")
	useIntegersForEnums := flags.Bool("use_integers_for_enums", false, "")
	disableFieldDescription := flags.Bool("disable_field_description", false, "")
	useNoneUnionSyntaxInsteadOfOptional := flags.Bool("use_none_union_syntax_instead_of_optional", true, "")
	disableValidate := flags.Bool("disable_validate", false, "")

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
			DisableValidate:                     *disableValidate,
		})
		e.resolver = buildEnumValueOptionsResolver(gen)
		e.customOptionFields = buildCustomOptionFields(gen)
		e.fieldConstraintExt = buildFieldConstraintExt(gen)
		e.messageConstraintExt = buildMessageConstraintExt(gen)
		e.celEnvCache = newCelEnvCache()

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

// buildMessageConstraintExt scans gen.Files for the buf.validate.message extension
// on google.protobuf.MessageOptions. Returns nil when buf.validate is not imported.
func buildMessageConstraintExt(gen *protogen.Plugin) protoreflect.ExtensionDescriptor {
	for _, f := range gen.Files {
		exts := f.Desc.Extensions()
		for i := 0; i < exts.Len(); i++ {
			ext := exts.Get(i)
			if ext.ContainingMessage().FullName() == "google.protobuf.MessageOptions" &&
				string(ext.Name()) == "message" &&
				string(ext.ParentFile().Package()) == "buf.validate" {
				return ext
			}
		}
	}
	return nil
}
