# protoc-gen-pydantic

`protoc-gen-pydantic` is a `protoc` plugin that automatically generates [Pydantic v2](https://docs.pydantic.dev/) model definitions from `.proto` files. This tool helps developers seamlessly integrate protobuf-defined models with Pydantic, a powerful data validation and settings management library for Python.

> Forked from [ornew/protoc-gen-pydantic](https://github.com/ornew/protoc-gen-pydantic), originally created by [Arata Furukawa](https://github.com/ornew).

## Features

- Supports all standard `proto3` field types.
- Handles nested messages and enums.
- Generates Pydantic models with type annotations and field descriptions.
- Supports `oneof`, `optional`, `repeated`, and `map` fields.
- Retains comments from `.proto` files as docstrings in the generated models.
- Maps well-known types to native Python types (e.g. `Timestamp` → `datetime`, `Struct` → `dict[str, Any]`).
- Handles Python builtin/keyword shadowing with PEP 8 trailing underscore aliases.
- Cross-package message references.
- Preserves enum value options (built-in `deprecated`/`debug_redact` and custom extensions) as accessible metadata on enum members.

## Installation

You can download the binaries from GitHub [Releases](https://github.com/cjermain/protoc-gen-pydantic/releases).

### Build from Source

You first need to have Go installed. If you don't have Go installed, you can download it from the Go downloads page.

Clone the repository and build the plugin:

```sh
git clone https://github.com/cjermain/protoc-gen-pydantic
cd protoc-gen-pydantic
go build -o protoc-gen-pydantic main.go
```

## Usage

To generate Pydantic model definitions, use `protoc` with your `.proto` files specifying `--pydantic_out`:

```sh
protoc --plugin=protoc-gen-pydantic=./protoc-gen-pydantic \
       --pydantic_out=./gen \
       --proto_path=./proto_files \
       ./api/example.proto
```

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
  - directory: api
```

```sh
buf config init
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

Running `protoc` will generate a Pydantic model like this:

```python
from enum import Enum as _Enum
from typing import Optional as _Optional

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
| `preserving_proto_field_name` | `false` | Use the proto field naming for the output field name. If `false`, it will be in camelCase according to `protojson` rules. |
| `auto_trim_enum_prefix` | `true` | Automatically remove prefixes from enum fields. |
| `use_integers_for_enums` | `false` | Use integers for enum values instead of enum names. |
| `disable_field_description` | `false` | Disable generating the field description. |
| `use_none_union_syntax_instead_of_optional` | `false` | Use `T \| None` instead of `Optional[T]`. |

### `auto_trim_enum_prefix`

```proto
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_OK = 1;
  STATUS_ERROR = 2;
}
```

If `auto_trim_enum_prefix` is `false`:

```python
class Status(str, _Enum):
    STATUS_UNSPECIFIED = "UNSPECIFIED"
    STATUS_OK = "OK"
    STATUS_ERROR = "ERROR"
```

If `auto_trim_enum_prefix` is `true` (default):

```python
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    OK = "OK"
    ERROR = "ERROR"
```

### `use_integers_for_enums`

If `use_integers_for_enums` is `false`:

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

If `disable_field_description` is `true`:

```proto
message User {
    // User name
    string name = 1;
}
```

```python
class User(_BaseModel):
    # User name
    name: str = _Field(..., description="User name")
```

If `disable_field_description` is `false`:

```python
class User(_BaseModel):
    # User name
    name: str = _Field(...)
```

### `use_none_union_syntax_instead_of_optional`

If `use_none_union_syntax_instead_of_optional` is `true`: `T | None`
If `use_none_union_syntax_instead_of_optional` is `false`: `Optional[T]`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your changes.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for more details.

## Acknowledgments

This project was originally created by [Arata Furukawa](https://github.com/ornew) ([ornew/protoc-gen-pydantic](https://github.com/ornew/protoc-gen-pydantic)).
