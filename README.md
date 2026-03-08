# protoc-gen-pydantic

[![CI](https://github.com/cjermain/protoc-gen-pydantic/actions/workflows/ci.yml/badge.svg)](https://github.com/cjermain/protoc-gen-pydantic/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/cjermain/protoc-gen-pydantic/branch/main/graph/badge.svg)](https://codecov.io/gh/cjermain/protoc-gen-pydantic)
[![Go Report Card](https://goreportcard.com/badge/github.com/cjermain/protoc-gen-pydantic)](https://goreportcard.com/report/github.com/cjermain/protoc-gen-pydantic)
[![Go Reference](https://pkg.go.dev/badge/github.com/cjermain/protoc-gen-pydantic.svg)](https://pkg.go.dev/github.com/cjermain/protoc-gen-pydantic)
[![Release](https://img.shields.io/github/v/release/cjermain/protoc-gen-pydantic)](https://github.com/cjermain/protoc-gen-pydantic/releases/latest)
[![Go version](https://img.shields.io/github/go-mod/go-version/cjermain/protoc-gen-pydantic)](go.mod)
[![License](https://img.shields.io/github/license/cjermain/protoc-gen-pydantic)](LICENSE)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-blue)](https://docs.pydantic.dev/)
[![buf](https://img.shields.io/badge/buf-compatible-blue)](https://buf.build/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://cjermain.github.io/protoc-gen-pydantic/)

`protoc-gen-pydantic` is a `protoc` plugin that generates [Pydantic v2](https://docs.pydantic.dev/) model
definitions from `.proto` files — so your schema stays the single source of truth.

If you work with Protobuf APIs in Python, the usual tradeoff is: use raw `_pb2` classes (no validation,
no editor support) or hand-write parallel Pydantic models and keep them in sync forever.
`protoc-gen-pydantic` eliminates that tradeoff: run `buf generate` once and get type-safe, validated
Python models automatically.

**Full documentation:** [cjermain.github.io/protoc-gen-pydantic](https://cjermain.github.io/protoc-gen-pydantic/)

> Forked from [ornew/protoc-gen-pydantic](https://github.com/ornew/protoc-gen-pydantic) by [Arata Furukawa](https://github.com/ornew), which provided the initial plugin structure and plugin options. This fork adds well-known type mappings, Python builtin/keyword alias handling, cross-package references, enum value options, ProtoJSON-compatible output, conditional imports, and a test suite.

## How it works

Run `buf generate` (or `protoc`) once. The plugin reads your `.proto` files and writes ready-to-use
Python files alongside them. No runtime dependency on the plugin — only on Pydantic.

```
.proto  →  buf generate  →  *_pydantic.py + _proto_types.py  →  import and use
```

## Features

- Supports all standard `proto3` field types
- Generates true Python nested classes for nested messages and enums (e.g. `Foo.NestedMessage`)
- Generates Pydantic models with type annotations and field descriptions
- Supports `oneof`, `optional`, `repeated`, and `map` fields; `oneof` exclusivity is enforced at runtime via a generated `@model_validator`
- Retains comments from `.proto` files as docstrings in the generated models
- Maps well-known types to native Python types (e.g. `Timestamp` → `datetime`, `Struct` → `dict[str, Any]`)
- Handles Python builtin/keyword shadowing with PEP 8 trailing underscore aliases
- Resolves cross-package message references
- Preserves enum value options (built-in `deprecated`/`debug_redact` and custom extensions) as accessible metadata on enum members
- Translates [buf.validate (protovalidate)](https://github.com/bufbuild/protovalidate) field constraints to native Pydantic constructs

## Installation

You can download the binaries from GitHub [Releases](https://github.com/cjermain/protoc-gen-pydantic/releases).

### Install with Go

```sh
go install github.com/cjermain/protoc-gen-pydantic@latest
```

### Build from Source

Clone the repository and build the plugin:

```sh
git clone https://github.com/cjermain/protoc-gen-pydantic
cd protoc-gen-pydantic
go build -o protoc-gen-pydantic .
```

## Usage

To generate Pydantic model definitions, use `protoc` with your `.proto` files specifying `--pydantic_out`:

```sh
protoc --pydantic_out=./gen \
       --proto_path=./proto \
       ./proto/example.proto
```

If the binary is not on your `PATH`, specify it explicitly with `--plugin=protoc-gen-pydantic=./protoc-gen-pydantic`.

If you use [buf](https://buf.build/):

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: go run github.com/cjermain/protoc-gen-pydantic@latest
    opt:
      - paths=source_relative
    out: gen
inputs:
  - directory: proto
```

```sh
buf generate
```

## Example

### With validation constraints

Add `buf.validate` constraints to your proto fields and the generator translates them
directly into Pydantic validation:

```proto
syntax = "proto3";

package example;

import "buf/validate/validate.proto";

// A user account.
message ValidatedUser {
  // Display name (1–50 characters).
  string name = 1 [
    (buf.validate.field).string.min_len = 1,
    (buf.validate.field).string.max_len = 50
  ];

  // Age in years.
  int32 age = 2 [(buf.validate.field).int32.gte = 0];

  // Contact email address.
  string email = 3 [(buf.validate.field).string.email = true];

  enum Role {
    ROLE_UNSPECIFIED = 0;
    ROLE_VIEWER = 1;
    ROLE_EDITOR = 2;
    ROLE_ADMIN = 3;
  }

  Role role = 4;
}
```

The generated model:

```python
class ValidatedUser(_ProtoModel):
    """
    A user account.
    """

    class Role(str, _Enum):
        UNSPECIFIED = "UNSPECIFIED"  # 0
        VIEWER = "VIEWER"  # 1
        EDITOR = "EDITOR"  # 2
        ADMIN = "ADMIN"  # 3

    # Display name (1–50 characters).
    name: str = _Field(
        description="Display name (1–50 characters).",
        min_length=1,
        max_length=50,
    )
    # Age in years.
    age: int = _Field(
        default=0,
        description="Age in years.",
        ge=0,
    )
    # Contact email address.
    email: _Annotated[str, _AfterValidator(_validate_email)] = _Field(
        description="Contact email address.",
    )
    role: "ValidatedUser.Role | None" = _Field(default=None)
```

Use it like any Pydantic model:

```python
from user_pydantic import ValidatedUser
from pydantic import ValidationError

# Construct and validate
user = ValidatedUser(name="Alice", age=30, email="alice@example.com", role=ValidatedUser.Role.EDITOR)

# Serialize (ProtoJSON — omits zero values, uses original proto field names)
print(user.to_proto_json())
# {"name":"Alice","age":30,"email":"alice@example.com","role":"EDITOR"}

# Validation errors are raised immediately
ValidatedUser(name="", age=-1)  # raises ValidationError (3 validation errors)
```

## Options

Passed via `opt:` in buf.gen.yaml or `--pydantic_opt=` with protoc:

| Option | Default | Description |
|--------|---------|-------------|
| `preserving_proto_field_name` | `true` | Keep snake_case proto field names instead of camelCase |
| `auto_trim_enum_prefix` | `true` | Remove enum type name prefix from value names |
| `use_integers_for_enums` | `false` | Use integer values for enums instead of string names |
| `disable_field_description` | `false` | Omit `description=` from generated fields |
| `use_none_union_syntax_instead_of_optional` | `true` | Use `T \| None` instead of `Optional[T]` |

See [Plugin Options](https://cjermain.github.io/protoc-gen-pydantic/options/) for full details.

## buf.validate

Field constraints from [buf.validate (protovalidate)](https://github.com/bufbuild/protovalidate)
are translated to Pydantic `Field()` kwargs automatically — no plugin option
required. Add the dependency to `buf.yaml` and run `buf dep update`:

```yaml
# buf.yaml
version: v2
modules:
  - path: .
deps:
  - buf.build/bufbuild/protovalidate
```

See [buf.validate guide](https://cjermain.github.io/protoc-gen-pydantic/buf-validate/) for the full constraint reference.

## Development

This project uses [mise](https://mise.jdx.dev/) to manage tool versions and
[just](https://github.com/casey/just) as a command runner.

After cloning, install all required tools with mise:

```sh
mise install
```

Then set up the project (sync Python venv, install pre-commit hooks):

```sh
just init
```

Other useful commands:

```sh
just dev    # Full rebuild + generate + test cycle
just lint   # Run all linters (Go + Python + type check)
just test   # Run Python tests only
```

Run `just --list` to see all available recipes.

> **Without mise**: install `go`, `buf`, `protoc`, `uv`, `golangci-lint`, `just`, and
> `pre-commit` manually, then run `just init`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your changes.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more details.
