---
icon: lucide/table
---

# Field Types

`protoc-gen-pydantic` supports all standard proto3 field types and generates correct Pydantic
annotations with appropriate defaults.

## Scalar fields

All proto3 scalar types map to native Python types:

| Proto type | Python type | Default |
|---|---|---|
| `string` | `str` | `""` |
| `bool` | `bool` | `False` |
| `int32`, `sint32`, `sfixed32` | `int` | `0` |
| `uint32`, `fixed32` | `int` | `0` |
| `int64`, `sint64`, `sfixed64` | `ProtoInt64` | `0` |
| `uint64`, `fixed64` | `ProtoUInt64` | `0` |
| `float` | `float` | `0.0` |
| `double` | `float` | `0.0` |
| `bytes` | `bytes` | `b""` |

`ProtoInt64` and `ProtoUInt64` are type aliases for `int` that carry JSON serialization semantics
(proto3 encodes 64-bit integers as strings in JSON).

=== ":lucide-file-code: scalars.proto"

    ```proto
    message Person {
      string name   = 1;
      int32  age    = 2;
      bool   active = 3;
      double score  = 4;
      bytes  avatar = 5;
    }
    ```

=== ":simple-python: scalars_pydantic.py"

    ```python
    class Person(_ProtoModel):
        name: "str" = _Field("")
        age: "int" = _Field(0)
        active: "bool" = _Field(False)
        score: "float" = _Field(0.0)
        bytes_: "bytes" = _Field(b"", alias="bytes")
    ```

## Optional fields

`optional` fields use `T | None` with a default of `None`, distinguishing "field not set"
from the zero value:

=== ":lucide-file-code: optional.proto"

    ```proto
    message SearchRequest {
      optional string query           = 1;
      optional int32  page_size       = 2;
      optional bool   include_deleted = 3;
    }
    ```

=== ":simple-python: optional_pydantic.py"

    ```python
    class SearchRequest(_ProtoModel):
        query: "str | None" = _Field(None)
        page_size: "int | None" = _Field(None)
        include_deleted: "bool | None" = _Field(None)
    ```

## Repeated fields

`repeated` fields generate `list[T]` with `default_factory=list`:

=== ":lucide-file-code: repeated.proto"

    ```proto
    message TaggedItem {
      string          name   = 1;
      repeated string tags   = 2;
      repeated int32  scores = 3;
    }
    ```

=== ":simple-python: repeated_pydantic.py"

    ```python
    class TaggedItem(_ProtoModel):
        name: "str" = _Field("")
        tags: "list[str]" = _Field(default_factory=list)
        scores: "list[int]" = _Field(default_factory=list)
    ```

## Map fields

`map<K, V>` fields generate `dict[K, V]` with `default_factory=dict`:

=== ":lucide-file-code: map.proto"

    ```proto
    message Config {
      map<string, string> labels   = 1;
      map<string, int32>  counters = 2;
    }
    ```

=== ":simple-python: map_pydantic.py"

    ```python
    class Config(_ProtoModel):
        labels: "dict[str, str]" = _Field(default_factory=dict)
        counters: "dict[str, int]" = _Field(default_factory=dict)
    ```

## Oneof fields

`oneof` groups generate one field per variant, all typed as `T | None = None`.
At most one may be non-`None` at a time (proto3 semantics).

=== ":lucide-file-code: oneof.proto"

    ```proto
    message Payment {
      oneof method {
        string credit_card = 1;
        string paypal      = 2;
        string bank_iban   = 3;
      }
    }
    ```

=== ":simple-python: oneof_pydantic.py"

    ```python
    class Payment(_ProtoModel):
        credit_card: "str | None" = _Field(None)
        paypal: "str | None" = _Field(None)
        bank_iban: "str | None" = _Field(None)
    ```

## Message fields

Message-typed fields default to `None` (not an empty sub-message):

=== ":lucide-file-code: message_field.proto"

    ```proto
    message Order {
      string  order_id = 1;
      Address address  = 2;
    }

    message Address {
      string street = 1;
      string city   = 2;
    }
    ```

=== ":simple-python: message_field_pydantic.py"

    ```python
    class Order(_ProtoModel):
        order_id: "str" = _Field("")
        address: "Address | None" = _Field(None)


    class Address(_ProtoModel):
        street: "str" = _Field("")
        city: "str" = _Field("")
    ```

## Enum fields

Enum-typed fields also default to `None`. See the [Enums page](./enums.md) for full details.

=== ":lucide-file-code: enum_field.proto"

    ```proto
    message Task {
      string status_label = 1;
      Status status       = 2;

      enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_OPEN        = 1;
        STATUS_DONE        = 2;
      }
    }
    ```

=== ":simple-python: enum_field_pydantic.py"

    ```python
    class Task(_ProtoModel):
        class Status(str, _Enum):
            UNSPECIFIED = "UNSPECIFIED"
            OPEN = "OPEN"
            DONE = "DONE"

        status_label: "str" = _Field("")
        status: "Task.Status | None" = _Field(None)
    ```
