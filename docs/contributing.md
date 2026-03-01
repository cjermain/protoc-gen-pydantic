---
icon: lucide/git-pull-request
---

# Contributing

Contributions are welcome! This page describes how to set up the development environment,
run tests, and submit changes.

## Prerequisites

This project uses [mise](https://mise.jdx.dev/) to manage tool versions. Install it first:

```sh
curl https://mise.run | sh
```

Then install all pinned tools (buf, just, uv, protoc, golangci-lint, pre-commit):

```sh
mise install
```

> **Without mise:** install `go`, `buf`, `protoc`, `uv`, `golangci-lint`, `just`, and
> `pre-commit` manually, then run `just init`.

## Setup

After installing tools, set up the project (sync the Python virtualenv, install pre-commit hooks):

```sh
just init
```

## Development workflow

```sh
just dev       # Full cycle: build → generate → test
just build     # Build the Go binary
just generate  # Build + regenerate Python models from test protos
just test      # Run Python tests only
just lint      # Run all linters (Go + Python + type check)
```

Run `just --list` to see all available recipes.

## Project structure

```
├── main.go                          # All Go plugin code (single file)
├── go.mod / go.sum
├── Justfile                         # just command runner recipes
├── buf.yaml / buf.gen.yaml          # Buf workspace and codegen config
└── test/
    ├── proto/api/v1/*.proto         # Test proto definitions
    ├── gen/api/v1/*_pydantic.py     # Generated output (committed)
    ├── gen_options/                 # Generated output with non-default options
    └── tests/                      # Pytest test suite
```

## Architecture

The entire plugin lives in `main.go`. Key components:

- **`processFile()`** — iterates messages and enums in a proto file
- **`processMessage()`** — builds `Message` structs with fields, nested types, constraints
- **`resolveType()`** / **`resolveBaseType()`** — maps proto types to Python types
- **`resolveQualifiedName()`** — returns the dotted path for nested type references
- **`extractFieldConstraints()`** — reads buf.validate field options via `dynamicpb`
- **`buildProtoTypesContent()`** — assembles `_proto_types.py` conditionally per directory
- **`modelTemplate`** — Go `text/template` constant that renders the Python output

## Adding a new feature

### Adding a field type mapping

Edit the `wellKnownTypes` map in `main.go` to add a new WKT → Python type mapping.

### Adding a plugin option

1. Add a field to the `GeneratorConfig` struct
2. Parse the option in the flag setup section of `main()`
3. Pass it through to the template context
4. Use it in the `modelTemplate`

### Adding buf.validate support

1. Add constraint extraction logic in `extractFieldConstraints()`
2. Apply type overrides (if needed) in `applyConstraintTypeOverrides()`
3. Add any new helper functions to the `protoTypes*` constants in `main.go`
4. Update `buildProtoTypesContent()` to conditionally include new helpers

## Adding tests

1. **Add proto definitions** to `test/proto/api/v1/*.proto` (or `test/proto/partial/v1/`
   for buf.validate subset tests)

2. **Rebuild and regenerate:**
   ```sh
   just generate
   ```

3. **Add pytest functions** to the matching test file in `test/tests/`
   (e.g. `test_scalars.py`, `test_validate.py`)

4. **Run tests:**
   ```sh
   just test
   ```

### Test conventions

- Use plain pytest functions, not `class Test...` wrappers
- Use `@pytest.mark.parametrize` for multiple similar cases
- Use fixtures for shared setup
- Generated files are checked by `test_ruff_format` (ruff) and `test_ty` (type checker) —
  run `just test` to catch format/type issues in generated output

### Verifying generated files

The CI checks that generated files match what's committed. After any change to `main.go`,
regenerate and commit the updated output:

```sh
just generate
git add test/gen/ test/gen_options/
```

You can verify locally with:

```sh
just check-generated
```

## Linting

```sh
just lint          # All linters
just lint-go       # Go: golangci-lint (uses goimports)
just lint-python   # Python: ruff on test suite
just lint-types    # Python: ty type checker on tests/ only
just fix-python    # Auto-fix Python lint issues
```

To auto-fix Go imports:

```sh
golangci-lint run --fix
```

## Submitting changes

1. Fork the repository and create a branch from `main`
2. Make your changes
3. Ensure `just dev` passes (build + generate + test)
4. Ensure `just lint` passes
5. Commit the updated generated files alongside your code changes
6. Open a pull request with a clear description of what changed and why

## Reporting issues

Please [open an issue](https://github.com/cjermain/protoc-gen-pydantic/issues) with:

- The proto file(s) involved
- The expected generated output
- The actual generated output
- Your `protoc-gen-pydantic` version (`protoc-gen-pydantic --version`)
