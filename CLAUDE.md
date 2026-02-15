# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

protoc-gen-pydantic is a `protoc` plugin written in Go that generates Pydantic v2 model definitions from `.proto` files. It reads protobuf descriptors via stdin (protoc plugin protocol) and outputs Python files with type-safe Pydantic models, including support for all proto3 field types, nested messages/enums, well-known types, and comment preservation.

## Architecture

**Single-file Go plugin** (`main.go`, ~725 lines):
- Reads `CodeGeneratorRequest` from stdin, writes `CodeGeneratorResponse` to stdout
- Uses Go `text/template` to render Python code
- Key types: `generator`, `Message`, `Field`, `Enum`, `EnumValue`, `OneOf`
- Key functions: `processFile()` → `processMessage()`/`processEnum()` → `resolveType()`/`resolveBaseType()`

**Code generation flow:**
1. Parse plugin options from protoc/buf
2. Iterate proto files → process each message and enum
3. Resolve protobuf types to Python types (including WKT mappings)
4. Render Python via `modelTemplate` constant
5. Output generated `_pydantic.py` files

## Dev Commands

This project uses [just](https://github.com/casey/just) as a command runner. Run `just --list` to see all recipes.

```bash
just build              # Build the Go binary
just generate           # Build + generate Python models from test protos
just test               # Run Python tests
just dev                # Full rebuild + generate + test cycle
just lint               # Run all linters (Go + Python)
just lint-go            # Run Go linter
just lint-python        # Run Python linters on test suite
just fix-python         # Auto-fix Python lint issues
just check-generated    # Verify generated files match committed versions
just clean              # Remove build artifacts and generated files

# Install pre-commit hooks (one-time setup)
pre-commit install
```

## Project Structure

```
├── main.go                          # All Go plugin code
├── go.mod / go.sum                  # Go module (github.com/cjermain/protoc-gen-pydantic)
├── buf.yaml                         # Buf workspace config
├── buf.gen.yaml                     # Buf code generation config
├── .goreleaser.yaml                 # Release automation
└── test/
    ├── pyproject.toml               # Python project config (uv + pydantic)
    ├── proto/                       # Proto source files
    │   ├── buf.yaml                 # Buf module config
    │   ├── api/v1/*.proto           # Proto definitions for testing
    │   └── foo/bar/v1/*.proto       # Cross-package proto definitions
    ├── gen/                         # Generated output, default options (committed)
    │   ├── api/v1/*_pydantic.py
    │   └── foo/bar/v1/*_pydantic.py
    ├── gen_options/                  # Generated output, all non-default options (committed)
    │   ├── api/v1/*_pydantic.py
    │   └── foo/bar/v1/*_pydantic.py
    └── tests/                       # Pytest suite
```

## Plugin Options

Passed via `opt:` in buf.gen.yaml or `--pydantic_opt=` with protoc:

| Option | Default | Description |
|--------|---------|-------------|
| `preserving_proto_field_name` | `false` | Use snake_case proto names instead of camelCase |
| `auto_trim_enum_prefix` | `true` | Remove enum type prefix from value names |
| `use_integers_for_enums` | `false` | Use int values instead of string names |
| `disable_field_description` | `false` | Skip field descriptions from comments |
| `use_none_union_syntax_instead_of_optional` | `false` | Use `T \| None` instead of `Optional[T]` |

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

Test coverage includes: enums, scalar fields, optional/repeated/map fields, oneof, builtin alias handling, well-known types, and JSON/dict roundtrips.

### Adding Tests
1. Add proto definitions to `test/proto/api/v1/*.proto`
2. Rebuild and regenerate: `just generate`
3. Add pytest functions to `test/tests/test_generated_models.py`
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
- All tests use modern pytest style: plain functions, fixtures, parametrize
- Python package management uses uv (not pip/rye)
