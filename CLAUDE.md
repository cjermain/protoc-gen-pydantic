# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

protoc-gen-pydantic is a `protoc` plugin written in Go that generates Pydantic v2 model definitions from `.proto` files. It reads protobuf descriptors via stdin (protoc plugin protocol) and outputs Python files with type-safe Pydantic models, including support for all proto3 field types, nested messages/enums, well-known types, and comment preservation.

## Architecture

**Single-file Go plugin** (`main.go`):
- Reads `CodeGeneratorRequest` from stdin, writes `CodeGeneratorResponse` to stdout
- Uses Go `text/template` to render Python code
- Key types: `generator`, `Message`, `Field`, `Enum`, `EnumValue`, `CustomOption`, `OneOf`
- Key functions: `processFile()` → `processMessage()`/`processEnum()` → `resolveType()`/`resolveBaseType()`

**Code generation flow:**
1. Parse plugin options from protoc/buf
2. Iterate proto files → process each message and enum
3. Resolve protobuf types to Python types (including WKT mappings)
4. Render Python via `modelTemplate` constant
5. Output generated `_pydantic.py` files

## Dev Commands

This project uses [mise](https://mise.jdx.dev/) to manage tool versions and [just](https://github.com/casey/just) as a command runner. Run `mise install` first, then `just --list` to see all recipes.

```bash
mise install            # Install all pinned tools (buf, just, uv, protoc, golangci-lint, pre-commit)
just init               # Check dependencies, install pre-commit hooks, sync Python venv
just build              # Build the Go binary
just generate           # Build + generate Python models from test protos
just test               # Run Python tests
just dev                # Full rebuild + generate + test cycle
just lint               # Run all linters (Go + Python + type check)
just lint-go            # Run Go linter
just lint-python        # Run Python linters on test suite
just lint-types         # Run ty type checker on test suite code (tests/ only)
just fix-python         # Auto-fix Python lint issues
just check-generated    # Verify generated files match committed versions
just clean              # Remove build artifacts and generated files
```

## Project Structure

```
├── main.go                          # All Go plugin code
├── go.mod                           # Go module (github.com/cjermain/protoc-gen-pydantic)
├── go.sum                           # Go dependency checksums
├── Justfile                         # Command runner recipes (just)
├── CLAUDE.md                        # Claude Code project instructions
├── buf.yaml                         # Buf workspace config
├── buf.gen.yaml                     # Buf code generation config
├── .goreleaser.yaml                 # Release automation
├── .pre-commit-config.yaml          # Pre-commit hook config
├── .github/
│   ├── workflows/ci.yml             # CI: lint, check-generated, test
│   ├── workflows/release.yml        # Release via goreleaser on tag push
│   └── dependabot.yml               # Dependency update automation
└── test/
    ├── pyproject.toml               # Python project config (uv + pydantic)
    ├── proto/                       # Proto source files
    │   ├── buf.yaml                 # Buf module config (includes buf.validate dep)
    │   ├── buf.lock                 # Pinned buf dependency commits
    │   ├── api/v1/*.proto           # Proto definitions for testing
    │   ├── foo/bar/v1/*.proto       # Cross-package proto definitions
    │   └── partial/v1/*.proto       # Partial buf.validate subset (email+uuid only)
    ├── gen/                         # Generated output, default options (committed)
    │   ├── api/v1/*_pydantic.py
    │   ├── foo/bar/v1/*_pydantic.py
    │   └── partial/v1/*_pydantic.py
    ├── gen_options/                  # Generated output, all non-default options (committed)
    │   ├── api/v1/*_pydantic.py
    │   ├── foo/bar/v1/*_pydantic.py
    │   └── partial/v1/*_pydantic.py
    └── tests/                       # Pytest suite
```

## Plugin Options

Passed via `opt:` in buf.gen.yaml or `--pydantic_opt=` with protoc:

| Option | Default | Description |
|--------|---------|-------------|
| `preserving_proto_field_name` | `true` | Use snake_case proto names instead of camelCase |
| `auto_trim_enum_prefix` | `true` | Remove enum type prefix from value names |
| `use_integers_for_enums` | `false` | Use int values instead of string names |
| `disable_field_description` | `false` | Skip field descriptions from comments |
| `use_none_union_syntax_instead_of_optional` | `true` | Use `T \| None` instead of `Optional[T]` |

buf.validate field constraints are **not** controlled by a plugin option. They
are read automatically from the proto descriptor whenever
`buf/validate/validate.proto` is imported. See the buf.validate section in Key
Implementation Details below.

## Key Implementation Details

### Python Builtin Shadowing
Proto fields named `bool`, `float`, `bytes` etc. shadow Python builtins. The generator renames these with a PEP 8 trailing underscore (e.g., `bool_`) and adds `Field(alias="bool")` with `ConfigDict(populate_by_name=True)`. The `reservedNames` map in main.go controls which names trigger this (Python builtins, keywords, and Pydantic BaseModel attributes).

### Well-Known Types
Protobuf WKTs are mapped to native Python types (not raw `_pb2` classes):
- `Timestamp` → `datetime.datetime`, `Duration` → `datetime.timedelta`
- `Struct` → `dict[str, Any]`, `Value` → `Any`, `ListValue` → `list[Any]`
- Wrapper types (`BoolValue`, `Int32Value`, etc.) → native Python equivalents
- `Empty` → `None`, `FieldMask` → `list[str]`, `Any` → `Any`

The `wellKnownTypes` map in main.go defines these mappings.

### buf.validate / protovalidate
`buf.validate` field constraints are translated to Pydantic constructs using
the same `dynamicpb` extension-resolution pattern as enum value options; see
`buildFieldConstraintExt()` and `extractFieldConstraints()` in main.go.

Supported translations:
- Numeric `gt`/`ge`/`lt`/`le` → `Field(gt=..., ge=..., lt=..., le=...)`
- `string.min_len`/`max_len`/`len`, `repeated.min_items`/`max_items`, `map.min_pairs`/`max_pairs` → `Field(min_length=..., max_length=...)`
- `string.pattern` → `Field(pattern=...)`
- `string.prefix`/`suffix` → `Field(pattern=...)` (anchored regex; conflicts with `pattern` → dropped comment)
- `field.example` → `Field(examples=[...])`
- `string.const`/`int.const`/`bool.const` → `Literal[value]` type + matching default (float/double/bytes excluded — not valid in `Literal[]`)
- `string.in`/`int.in`/etc. → `Annotated[T, AfterValidator(_make_in_validator(frozenset({...})))]`
- `string.not_in`/etc. → `Annotated[T, AfterValidator(_make_not_in_validator(frozenset({...})))]`
- `repeated.unique` → `Annotated[list[T], AfterValidator(_require_unique)]`
- `string.email`/`uri`/`ip`/`ipv4`/`ipv6`/`uuid` → `Annotated[str, AfterValidator(_validate_*)]`

Emitted as `# buf.validate: X (not translated)` comments: `required`, CEL,
float/double/bytes `const`, message-typed bounds (duration, timestamp).
`enum.defined_only` is a no-op (Python enums enforce this natively).

Format and set validator helpers live in `_proto_types.py` (generated
alongside model files). `buildProtoTypesContent(needed map[string]bool)`
assembles the file conditionally — only imports and functions actually used by
the directory's proto files are emitted. `protoTypeDirs` in `main()` is
`map[string]map[string]bool` accumulating runtime import names per directory.

`test/proto/buf.yaml` declares the `buf.build/bufbuild/protovalidate` dep;
`_has_bsr_imports()` in conftest.py excludes BSR protos from the standalone
`protoc` compilation.

### Generated Python Conventions
- Standard library imports are aliased with `_` prefix to avoid conflicts: `_BaseModel`, `_Field`, `_Enum`, `_Optional`, `_Any`
- Nested types use `Parent_Child` naming: `Foo_NestedMessage`, `Foo_NestedEnum`
- Proto comments become docstrings and `Field(description=...)` values
- Forward references use string annotations: `"Message"` instead of `Message`

## Tests

Tests use pytest with fixtures and `@pytest.mark.parametrize`. Do not use unittest classes.

```bash
# Run all tests
just test

# Run specific test
cd test && uv run pytest -v -k test_wkt_timestamp
```

Test coverage includes:
- Proto field types: enums, scalars, optional/repeated/map, oneof, well-known types
- Builtin alias handling (`bool_`, `float_`, `bytes_`)
- Enum value options (built-in and custom), buf.validate field constraints
- JSON/dict roundtrips
- `test_ruff_format`: ruff format compliance of all generated files
- `test_ty`: ty type checking of all generated files
- `test_proto_types`: structural and content tests for conditional `_proto_types.py` generation (presence/absence of format-validator imports per directory)

Format/type issues in generated files are caught by `just test`, not `just lint`. `just lint-types` covers `tests/` only. False-positive ty rules (Pydantic alias mechanics, `**kwargs` spreading, dynamic imports) are suppressed globally in `[tool.ty.rules]` in `test/pyproject.toml`.

### Adding Tests
1. Add proto definitions to `test/proto/api/v1/*.proto` (or `test/proto/partial/v1/` for buf.validate subset tests)
2. Rebuild and regenerate: `just generate`
3. Add pytest functions to the matching test file in `test/tests/` (e.g. `test_scalars.py`, `test_collections.py`, `test_enums.py`, `test_validate.py`, `test_proto_types.py`)
4. Run: `just test`

## Code Style

### Go (main.go)
- All code lives in a single `main.go` file
- Template rendering uses Go `text/template` with the `modelTemplate` constant
- Add new type mappings to the appropriate map (`wellKnownTypes`, `reservedNames`)
- New plugin options: add to `GeneratorConfig` struct, parse in flag setup, wire through template

### Python (generated output)
- Generated files start with `# DO NOT EDIT. Generated by protoc-gen-pydantic.`
- Generated code must pass `ruff format --check` (enforced by `test_ruff_format` in the test suite)
- All tests use modern pytest style: plain functions, fixtures, parametrize. Do not use test classes (`class Test...`)
- Python package management uses uv (not pip/rye)
