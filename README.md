# protoc-gen-pydantic

[![CI](https://github.com/cjermain/protoc-gen-pydantic/actions/workflows/ci.yml/badge.svg)](https://github.com/cjermain/protoc-gen-pydantic/actions/workflows/ci.yml)
[![Go Reference](https://pkg.go.dev/badge/github.com/cjermain/protoc-gen-pydantic.svg)](https://pkg.go.dev/github.com/cjermain/protoc-gen-pydantic)
[![Release](https://img.shields.io/github/v/release/cjermain/protoc-gen-pydantic)](https://github.com/cjermain/protoc-gen-pydantic/releases/latest)

`protoc-gen-pydantic` is a `protoc` plugin that generates [Pydantic v2](https://docs.pydantic.dev/) model definitions from `.proto` files.

> Forked from [ornew/protoc-gen-pydantic](https://github.com/ornew/protoc-gen-pydantic) by [Arata Furukawa](https://github.com/ornew), which provided the initial plugin structure and plugin options. This fork adds well-known type mappings, Python builtin/keyword alias handling, cross-package references, enum value options, ProtoJSON-compatible output, conditional imports, and a test suite.

## Features

- Supports all standard `proto3` field types
- Handles nested messages and enums
- Generates Pydantic models with type annotations and field descriptions
- Supports `oneof`, `optional`, `repeated`, and `map` fields
- Retains comments from `.proto` files as docstrings in the generated models
- Maps well-known types to native Python types (e.g. `Timestamp` → `datetime`, `Struct` → `dict[str, Any]`)
- Handles Python builtin/keyword shadowing with PEP 8 trailing underscore aliases
- Resolves cross-package message references
- Preserves enum value options (built-in `deprecated`/`debug_redact` and custom extensions) as accessible metadata on enum members
- Translates [buf.validate (protovalidate)](https://github.com/bufbuild/protovalidate) field constraints to native Pydantic `Field()` kwargs — numeric bounds, string/list lengths, and regex patterns — with no extra runtime dependency

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
  - local: protoc-gen-pydantic
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

Given a simple `.proto` file:

```proto
syntax = "proto3";

package example;

// User model representing the example.User message.
message User {
  string name = 1;
  int32 age = 2;
  repeated string emails = 3;
  bool is_active = 4;
}
```

The generated Pydantic model will look like this:

```python
from pydantic import BaseModel as _BaseModel, Field as _Field

class User(_BaseModel):
    """
    User model representing the example.User message.
    """
    name: str = _Field(...)
    age: int = _Field(...)
    emails: list[str] = _Field(...)
    is_active: bool = _Field(...)
```

## Options

Passed via `opt:` in buf.gen.yaml or `--pydantic_opt=` with protoc:

| Option | Default | Description |
|--------|---------|-------------|
| `preserving_proto_field_name` | `true` | Keep snake_case proto field names instead of camelCase |
| `auto_trim_enum_prefix` | `true` | Remove enum type name prefix from value names |
| `use_integers_for_enums` | `false` | Use integer values for enums instead of string names |
| `disable_field_description` | `false` | Omit `description=` from generated fields |
| `use_none_union_syntax_instead_of_optional` | `false` | Use `T \| None` instead of `Optional[T]` |

### `preserving_proto_field_name`

```proto
message User {
  bool is_active = 1;
}
```

If `preserving_proto_field_name` is `true` (default):

```python
class User(_BaseModel):
    is_active: bool = _Field(...)
```

If `preserving_proto_field_name` is `false`:

```python
class User(_BaseModel):
    isActive: bool = _Field(...)
```

### `auto_trim_enum_prefix`

```proto
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_OK = 1;
  STATUS_ERROR = 2;
}
```

If `auto_trim_enum_prefix` is `true` (default):

```python
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    OK = "OK"
    ERROR = "ERROR"
```

If `auto_trim_enum_prefix` is `false`:

```python
class Status(str, _Enum):
    STATUS_UNSPECIFIED = "UNSPECIFIED"
    STATUS_OK = "OK"
    STATUS_ERROR = "ERROR"
```

### `use_integers_for_enums`

```proto
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_OK = 1;
  STATUS_ERROR = 2;
}
```

If `use_integers_for_enums` is `false` (default):

```python
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    OK = "OK"
    ERROR = "ERROR"
```

If `use_integers_for_enums` is `true`:

```python
class Status(int, _Enum):
    UNSPECIFIED = 0
    OK = 1
    ERROR = 2
```

### `disable_field_description`

```proto
message User {
    // User name
    string name = 1;
}
```

If `disable_field_description` is `false` (default):

```python
class User(_BaseModel):
    # User name
    name: str = _Field(..., description="User name")
```

If `disable_field_description` is `true`:

```python
class User(_BaseModel):
    # User name
    name: str = _Field(...)
```

### `use_none_union_syntax_instead_of_optional`

If `use_none_union_syntax_instead_of_optional` is `false` (default):

```python
class User(_BaseModel):
    name: _Optional[str] = _Field(...)
```

If `use_none_union_syntax_instead_of_optional` is `true`:

```python
class User(_BaseModel):
    name: str | None = _Field(...)
```

### buf.validate

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

| buf.validate rule | `Field()` kwarg |
|---|---|
| Numeric `gt` / `gte` / `lt` / `lte` | `gt=` / `ge=` / `lt=` / `le=` |
| `string.min_len` / `string.max_len` | `min_length=` / `max_length=` |
| `string.pattern` | `pattern=` |
| `repeated.min_items` / `repeated.max_items` | `min_length=` / `max_length=` |

```proto
import "buf/validate/validate.proto";

message CreateUser {
  string username = 1 [(buf.validate.field).string.min_len = 1, (buf.validate.field).string.max_len = 50];
  int32 age = 2 [(buf.validate.field).int32.gte = 18, (buf.validate.field).int32.lte = 120];
}
```

```python
class CreateUser(_ProtoModel):
    username: "str" = _Field(
        "",
        min_length=1,
        max_length=50,
    )
    age: "int" = _Field(
        0,
        ge=18,
        le=120,
    )
```

Constraints without a direct Pydantic equivalent (`required`, `const`, CEL expressions) are not translated.

## Development

This project uses [just](https://github.com/casey/just) as a command runner. After cloning, run:

```sh
just init
```

This checks that all required tools are installed (`go`, `buf`, `protoc`, `uv`, `golangci-lint`), syncs the Python virtual environment, and installs pre-commit hooks.

Other useful commands:

```sh
just dev    # Full rebuild + generate + test cycle
just lint   # Run all linters (Go + Python + type check)
just test   # Run Python tests only
```

Run `just --list` to see all available recipes.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your changes.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more details.
