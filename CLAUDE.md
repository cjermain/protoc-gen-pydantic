# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

protoc-gen-pydantic is a `protoc` plugin written in Go that generates Pydantic v2 model definitions from `.proto` files. It reads protobuf descriptors via stdin (protoc plugin protocol) and outputs Python files with type-safe Pydantic models, including support for all proto3 field types, nested messages/enums, well-known types, and comment preservation.

## Architecture

**Seven-file Go plugin** (`package main`):
- `main.go` — entry point + `buildFieldConstraintExt()` / `buildMessageConstraintExt()` for buf.validate extension resolution
- `generator.go` — processing + type resolution: `processFile()` → `processMessage()`/`processEnum()` → `resolveType()`/`resolveBaseType()`/`resolveQualifiedName()`
- `types.go` — domain types (`generator`, `Message`, `Field`, `Enum`, `EnumValue`, `CustomOption`, `OneOf`, `CelValidator`) and data maps (`wellKnownTypes`, `reservedNames`)
- `constraints.go` — buf.validate translation: `extractFieldConstraints()`, `applyConstraintTypeOverrides()`
- `cel_transpile.go` — CEL-to-Python transpiler: `transpileCELField()`, `transpileCELMessage()`, `celEnvCache`, `transpiler` struct with node-dispatch for all supported constructs
- `template.go` — Python template constants (`modelTemplate`) + `buildProtoTypesContent()`
- `format.go` — formatting utilities: `formatFactoryCall()`, `formatLambdaArg()`, `pycelCondLine()`, line-wrapping helpers

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
just lint               # Run all linters (Go + Python + docs + type check)
just lint-go            # Run Go linter
just lint-python        # Run Python linters on test suite
just lint-docs          # Check Python code blocks in docs/*.md pass ruff format
just lint-types         # Run ty type checker on test suite code (tests/ only)
just fix-python         # Auto-fix Python lint issues
just fix-docs           # Auto-fix Python code blocks in docs/*.md
just check-generated    # Verify generated files match committed versions
just clean              # Remove build artifacts and generated files (incl. docs dist/cache)
just docs-install       # Verify mkdocs is installed
just docs-dev           # Local dev server at http://localhost:8000/
just docs-build         # Production build → site/
just docs-preview       # Build docs and preview locally
```

## Project Structure

```
├── main.go                          # Entry point + proto option builders
├── generator.go                     # Processing + type resolution
├── types.go                         # Domain types + data maps (wellKnownTypes, reservedNames)
├── constraints.go                   # buf.validate translation
├── template.go                      # Python template constants + buildProtoTypesContent
├── format.go                        # Formatting utilities
├── go.mod                           # Go module (github.com/cjermain/protoc-gen-pydantic)
├── go.sum                           # Go dependency checksums
├── Justfile                         # Command runner recipes (just)
├── CLAUDE.md                        # Claude Code project instructions
├── buf.yaml                         # Buf workspace config
├── buf.gen.yaml                     # Buf code generation config
├── .goreleaser.yaml                 # Release automation
├── .pre-commit-config.yaml          # Pre-commit hook config
├── mkdocs.yml                       # MkDocs site configuration
├── docs/                            # MkDocs documentation source
│   ├── index.md                     # Landing page
│   ├── guide/                       # Getting-started guides
│   ├── features/                    # Feature reference pages
│   ├── options.md                   # Plugin options reference
│   ├── buf-validate.md              # buf.validate guide
│   ├── contributing.md              # Developer guide
│   └── overrides/                   # MkDocs theme overrides (Lucide icons)
├── .github/
│   ├── workflows/ci.yml             # CI: lint, check-generated, test
│   ├── workflows/docs.yml           # Deploy docs to GitHub Pages
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
    ├── gen_novalidate/               # Generated output, disable_validate=true (committed)
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
| `disable_validate` | `false` | Skip all buf.validate constraint translation |

buf.validate field constraints are **not** controlled by a plugin option by default. They
are read automatically from the proto descriptor whenever
`buf/validate/validate.proto` is imported. Use `disable_validate=true` to suppress all
constraint translation. See the buf.validate section in Key Implementation Details below.

## Key Implementation Details

### Python Builtin Shadowing
Proto fields named `bool`, `float`, `bytes` etc. shadow Python builtins. The generator renames these with a PEP 8 trailing underscore (e.g., `bool_`) and adds `Field(alias="bool")` with `ConfigDict(populate_by_name=True)`. The `reservedNames` map in types.go controls which names trigger this (Python builtins, keywords, and Pydantic BaseModel attributes).

### Well-Known Types
Protobuf WKTs are mapped to native Python types (not raw `_pb2` classes):
- `Timestamp` → `datetime.datetime`, `Duration` → `datetime.timedelta`
- `Struct` → `dict[str, Any]`, `Value` → `Any`, `ListValue` → `list[Any]`
- Wrapper types (`BoolValue`, `Int32Value`, etc.) → native Python equivalents
- `Empty` → `None`, `FieldMask` → `list[str]`, `Any` → `Any`

The `wellKnownTypes` map in types.go defines these mappings.

### buf.validate / protovalidate
`buf.validate` field constraints are translated to Pydantic constructs.
`buildFieldConstraintExt()` / `buildMessageConstraintExt()` in `main.go` resolve the extension
descriptors; `extractFieldConstraints()` and `applyConstraintTypeOverrides()` in `constraints.go`
perform the predefined-rule translation; `cel_transpile.go` handles CEL.

Supported predefined-rule translations:
- Numeric `gt`/`ge`/`lt`/`le` → `Field(gt=..., ge=..., lt=..., le=...)`
- `string.min_len`/`max_len`/`len`, `repeated.min_items`/`max_items`, `map.min_pairs`/`max_pairs` → `Field(min_length=..., max_length=...)`
- `string.pattern` → `Field(pattern=...)`
- `string.prefix`/`suffix` → `Field(pattern=...)` (anchored regex; conflicts with `pattern` → dropped comment)
- `string.contains` → `Field(pattern=...)` (dropped if conflicts with prefix/suffix pattern)
- `string.not_contains` → `Annotated[str, AfterValidator(_make_not_contains_validator("s"))]`
- `string.min_bytes` → `Annotated[str, AfterValidator(_make_min_bytes_validator(N))]`
- `string.max_bytes` → `Annotated[str, AfterValidator(_make_max_bytes_validator(N))]`
- `string.len_bytes` → `Annotated[str, AfterValidator(_make_len_bytes_validator(N))]` (exact byte count)
- `field.example` → `Field(examples=[...])`
- `string.const`/`int.const`/`bool.const` → `Literal[value]` type + matching default
- `float.const`/`double.const` → `Annotated[float, AfterValidator(_make_const_validator(v))]` (Literal[float] is invalid per PEP 586)
- `float.finite`/`double.finite` → `Annotated[float, AfterValidator(_require_finite)]`
- `string.in`/`int.in`/`float.in`/etc. → `Annotated[T, AfterValidator(_make_in_validator(frozenset({...})))]`
- `string.not_in`/etc. → `Annotated[T, AfterValidator(_make_not_in_validator(frozenset({...})))]`
- `repeated.unique` → `Annotated[list[T], AfterValidator(_require_unique)]`
- `repeated.items` → per-element `list[Annotated[T, ...]]` wrapping via `buildItemAnnotation`
- `map.keys` → per-key `dict[Annotated[K, ...], V]` via `buildItemAnnotation` + `splitDictType`
- `map.values` → per-value `dict[K, Annotated[V, ...]]` via `buildItemAnnotation` + `splitDictType`
- `string.email`/`uri`/`ip`/`ipv4`/`ipv6`/`uuid` → `Annotated[str, AfterValidator(_validate_*)]`
- `string.hostname`/`uri_ref`/`address`/`tuuid`/`ulid`/`ip_with_prefixlen`/`ipv4_with_prefixlen`/`ipv6_with_prefixlen`/`ip_prefix`/`ipv4_prefix`/`ipv6_prefix`/`host_and_port` → `Annotated[str, AfterValidator(_validate_*)]`
- `string.well_known_regex = HTTP_HEADER_NAME/HTTP_HEADER_VALUE` → `Annotated[str, AfterValidator(_validate_http_header_name/_validate_http_header_value)]`; `strict=false` → dropped comment
- `bytes.uuid` → `Annotated[bytes, AfterValidator(_validate_bytes_uuid)]` (16-byte check)
- `bytes.ip` → `Annotated[bytes, AfterValidator(_validate_bytes_ip)]` (4 or 16 bytes)
- `bytes.ipv4` → `Annotated[bytes, AfterValidator(_validate_bytes_ipv4)]` (exactly 4 bytes)
- `bytes.ipv6` → `Annotated[bytes, AfterValidator(_validate_bytes_ipv6)]` (exactly 16 bytes)

Emitted as `# buf.validate: X (not translated)` comments: `required`, `bytes.const`,
message-typed bounds (duration, timestamp). `enum.defined_only` is a no-op (Python enums
enforce this natively).

**CEL transpilation** (`cel_transpile.go`): `(buf.validate.field).cel` and its shorthand
`(buf.validate.field).cel_expression` (field 29 of `FieldRules`), as well as
`option (buf.validate.message).cel` and its shorthand `option (buf.validate.message).cel_expression`
(field 5 of `MessageRules`), are all transpiled to Python at code-generation time using `cel-go`.
No runtime CEL dependency is added to generated files.

The `cel_expression` shorthand is handled in `extractFieldConstraints` (`constraints.go`) and
`extractMessageCEL` (`generator.go`) by constructing `celRule{ID: expr, Expression: expr}` for
each string entry and routing it through the identical transpilation path as full `cel` rules.
Untranslatable `cel_expression` entries emit the same `# buf.validate: cel id="…" (not translated: reason)`
comment as full `cel` rules.

- **Field-level**: transpiled expression becomes `_AfterValidator(_make_cel_validator(lambda v: expr, "msg"))` (bool-returning) or `_AfterValidator(_make_cel_str_validator(lambda v: expr))` (string-returning).
- **Message-level**: each rule becomes a `@model_validator(mode="after")` method. `has(this.field)` presence checks use `"field" in self.model_fields_set`.
- **Comprehensions**: `all`, `exists`, `exists_one`, `filter`, `map` → Python `all()`, `any()`, `sum(…)==1`, list comprehensions. Nested comprehensions (e.g. `map().all()`) work via recursive dispatch.
- **Temporal**: `now` → `_cel_now()`, `duration("1h30m")` → `_cel_duration(5400)`, `timestamp("2020-01-01T00:00:00Z")` → `_cel_timestamp("2020-01-01T00:00:00Z")`. Non-repeated WKT message fields (`Timestamp`, `Duration`) wrap lambdas as `lambda v: v is None or (...)` to match protovalidate's skip-if-absent semantics.
- **Timestamp accessors**: `this.getFullYear()` → `v.year`, `this.getMonth()` → `(v.month - 1)` (0-indexed), `this.getDayOfWeek()` → `(v.isoweekday() % 7)` (Sun=0), `this.getHours()` → `v.hour`, etc. All accept an optional IANA timezone string arg; non-UTC tz → `_cel_ts_in_tz(v, "tz")`.
- **Duration accessors**: `this.getHours()` → `_cel_dur_get_hours(v)` = `(v.days * 86400 + v.seconds) // 3600`, etc. (all return TOTAL units, matching CEL semantics).
- **Boolean format helpers**: `this.isEmail()` → `_is_email(v)`, `this.isIp()` → `_is_ip(v)`, `this.isUri()` → `_is_uri(v)`, etc. (mapped to the same `_proto_types.py` helpers used by predefined format validators).
- **Dropped**: CEL expressions containing unsupported constructs (`rules` ident, `getField()`, `ext.Strings()` member functions, two-variable map comprehensions, non-literal `duration()`/`timestamp()` args) are emitted as `# buf.validate: cel id="…" (not translated: reason)` comments.

The `celEnvCache` (keyed by field type signature including WKT full names) caches `cel.Env`
instances. The `transpiler` struct carries `isMsg bool`, `fieldNames map[string]string`,
`imports map[string]bool`, and `compVars map[string]bool` (comprehension scope).
`recvTypeName` (from `NavigableExpr.Type().TypeName()`) is passed to `memberFunc` to dispatch
timestamp vs. duration overloads for `getHours()` etc.

The `CelValidator` struct in `types.go` holds `RuleID`, `Expression`, `Message`,
`ReturnsBool`, `NullSafe`, and `Imports`. `Field.CelValidators` and `Message.CelValidators`
accumulate successfully transpiled rules; failures go to `DroppedConstraints` /
`Message.DroppedCelConstraints`.

**Zero-value validation (ConstrainedRequired)**: Non-optional scalar fields whose constraints
reject the proto3 zero value (`""`, `0`, `false`, `b""`) become required Pydantic fields (no
default). Detection logic in `generator.go` (after `applyConstraintTypeOverrides`): checks
`isScalar && isNotOptional && !hasConst && !ignoreZero && f.Constraints.ZeroValueFails(kind)`.
Sets `f.ConstrainedRequired = true; f.Default = ""`. Affected constraint types: format
validators, `gt` (N≥0), `gte` (N>0), `min_len` (N>0), `min_bytes` (N>0), `len_bytes` (N>0),
`pattern` (any), `in` (zero not in set).
**Not** ConstrainedRequired: AfterValidator-only constraints with Pydantic-unvalidated defaults
(not_in, not_contains, finite, unique, const-float, max_bytes-only), dropped constraints (required),
CEL-only fields (lambdas bypass default validation), repeated/map fields, optional fields, oneof
members, enum fields.

`ignore = IGNORE_IF_ZERO_VALUE` (or any non-zero `ignore` enum value) opts a field out —
sets `IgnoreZero = true` in `FieldConstraints` (parsed in `constraints.go` top-level Range
switch). The field keeps its zero default; validators only run for explicitly-set values
(Pydantic does not validate defaults by default).

Key types added to `types.go`: `IgnoreZero bool` on `FieldConstraints`, `ConstrainedRequired
bool` on `Field`, `HasConstraintKwargs() bool`, `ZeroValueFails(kind) bool`,
`zeroLiteralForKind(kind)`, `inValuesContainZero(kind) bool`, `NeedsMultilineDefault(bi) bool`,
`TypeAnnotationFormattedBare(bi) string`. Template uses `HasConstraintKwargs` (not
`HasConstraints`) for the outer multi-line `_Field()` branch, and `NeedsMultilineDefault` to
catch long `= _Field(Default)` lines that need multi-line form despite no constraint kwargs.

Format and set validator helpers, plus `_EnumValueOptions` and `_ProtoEnum`, live in
`_proto_types.py` (generated alongside model files). `buildProtoTypesContent(needed
map[string]bool, config GeneratorConfig, dirCustomOptionFields []CustomOptionField)`
assembles the file conditionally — only imports and definitions actually used by the
directory's proto files are emitted. `_ProtoEnum` and (when any enum has options)
`_EnumValueOptions` are imported from `._proto_types` by generated model files.
`protoTypeDirs` in `main()` is `map[string]map[string]bool` accumulating runtime import
names per directory.

`test/proto/buf.yaml` declares the `buf.build/bufbuild/protovalidate` dep;
`_has_bsr_imports()` in conftest.py excludes BSR protos from the standalone
`protoc` compilation.

### Generated Python Conventions
- Standard library imports are aliased with `_` prefix to avoid conflicts: `_BaseModel`, `_Field`, `_Optional`, `_Any`
- Nested types are true Python nested classes: `Foo.NestedMessage`, `Foo.NestedEnum` (accessible via dotted attribute access)
- Cross-file imports name only the top-level class: `from .scalars_pydantic import Scalars`; dotted access (`Scalars.NestedEnum`) resolves at runtime
- `resolveQualifiedName(d)` returns the dotted path from the file root (e.g. `Outer.Inner.Deepest`) used for type annotations; `string(d.Name())` is the leaf name used for the class definition itself
- Proto comments become docstrings and `Field(description=...)` values
- Forward references use string annotations: `"Message"` instead of `Message`
- Each `oneof` group generates a `@_model_validator(mode="after")` method named `_validate_oneof_<name>` that raises `ValueError` if more than one field in the group is non-`None`; the `pyOneofSetLine` FuncMap function formats the `_set = [...]` comprehension as single-line or ruff-compatible multi-line depending on the 88-char limit

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
- Enum value options (built-in and custom), buf.validate predefined field constraints
- CEL transpilation: field-level and message-level `.cel` rules and `cel_expression` shorthand, comprehensions, temporal expressions, timestamp/duration member accessors, boolean format helpers, drop path (field and message level)
- JSON/dict roundtrips
- `test_ruff_format`: ruff format compliance of all generated files
- `test_ty`: ty type checking of all generated files
- `test_proto_types`: structural and content tests for conditional `_proto_types.py` generation (presence/absence of format-validator imports per directory)
- `test_disable_validate`: verifies `disable_validate=true` output — no `_AfterValidator`, no `_proto_types` import, no dropped-constraint comments, and ConstrainedRequired fields revert to zero-value defaults

Format/type issues in generated files are caught by `just test`, not `just lint`. `just lint-types` covers `tests/` only. False-positive ty rules (Pydantic alias mechanics, `**kwargs` spreading, dynamic imports) are suppressed globally in `[tool.ty.rules]` in `test/pyproject.toml`.

### Adding Tests
1. Add proto definitions to `test/proto/api/v1/*.proto` (or `test/proto/partial/v1/` for buf.validate subset tests)
2. Rebuild and regenerate: `just generate`
3. Add pytest functions to the matching test file in `test/tests/` (e.g. `test_scalars.py`, `test_collections.py`, `test_enums.py`, `test_validate.py`, `test_proto_types.py`)
4. Run: `just test`

## Code Style

### Go
- Template rendering uses Go `text/template` with the `modelTemplate` constant in `template.go`
- Add new type mappings to the appropriate map (`wellKnownTypes`, `reservedNames`) in `types.go`
- Add new buf.validate constraint translations to `extractRuleField()` / `applyConstraintTypeOverrides()` in `constraints.go`
- New plugin options: add to `GeneratorConfig` struct, parse in flag setup, wire through template

### Python (generated output)
- Generated files start with `# DO NOT EDIT. Generated by protoc-gen-pydantic.`
- Generated code must pass `ruff format --check` (enforced by `test_ruff_format` in the test suite)
- All tests use modern pytest style: plain functions, fixtures, parametrize. Do not use test classes (`class Test...`)
- Python package management uses uv (not pip/rye)

## Documentation Site

The docs site lives in `docs/` and is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) (config: `mkdocs.yml` at project root, `docs_dir: docs`, output goes to `site/`).
Use `just docs-dev` to develop locally at `http://localhost:8000/` and `just docs-build` to verify a production build.
Deployed automatically to GitHub Pages on push to `main` via `.github/workflows/docs.yml`.

Lucide icons used in frontmatter and content tabs are committed as SVG files in `docs/overrides/.icons/lucide/` (fetched from `https://unpkg.com/lucide-static@latest/icons/<name>.svg`). When new Lucide icons are needed, download and commit the SVG the same way.

Python code blocks in docs pages are checked and auto-fixed with `just lint-docs` / `just fix-docs`.
The pre-commit hook `ruff-format-docs` runs this automatically on staged docs files.
