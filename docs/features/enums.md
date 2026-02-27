---
icon: lucide/list-tree
---

# Enums

Proto3 enums become Python `Enum` subclasses. The generator supports string-valued enums
(default), integer-valued enums (opt-in), enum value options, and the well-known
`auto_trim_enum_prefix` behaviour.

## Basic enum

By default, enums use `str` as the mixin type and string names as values:

=== ":lucide-file-code: status.proto"

    ```proto
    enum Status {
      STATUS_UNSPECIFIED = 0;
      STATUS_ACTIVE      = 1;
      STATUS_INACTIVE    = 2;
    }
    ```

=== ":simple-python: status_pydantic.py"

    ```python
    class Status(str, _Enum):
        UNSPECIFIED = "UNSPECIFIED"
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"
    ```

## Prefix trimming (`auto_trim_enum_prefix`)

The default `auto_trim_enum_prefix=true` removes the enum type name prefix from value names.
The prefix match is case-insensitive and strips a trailing `_`:

```
STATUS_UNSPECIFIED → UNSPECIFIED
STATUS_ACTIVE      → ACTIVE
```

With `auto_trim_enum_prefix=false` the full name is kept:

```python
class Status(str, _Enum):
    STATUS_UNSPECIFIED = "STATUS_UNSPECIFIED"
    STATUS_ACTIVE = "STATUS_ACTIVE"
    STATUS_INACTIVE = "STATUS_INACTIVE"
```

See [Plugin Options](../options#auto-trim-enum-prefix) for details.

## Integer enums (`use_integers_for_enums`)

With `use_integers_for_enums=true`, the mixin type becomes `int` and values are integers:

```python
class Status(int, _Enum):
    UNSPECIFIED = 0
    ACTIVE = 1
    INACTIVE = 2
```

See [Plugin Options](../options#use-integers-for-enums) for details.

## Top-level vs. nested enums

Enums defined at the file level become top-level classes. Enums defined inside a message
become nested classes of that message:

=== ":lucide-file-code: mixed.proto"

    ```proto
    // Top-level enum
    enum Color {
      COLOR_UNSPECIFIED = 0;
      COLOR_RED         = 1;
      COLOR_BLUE        = 2;
    }

    message Shape {
      // Nested enum
      enum Kind {
        KIND_UNSPECIFIED = 0;
        KIND_CIRCLE      = 1;
        KIND_SQUARE      = 2;
      }

      Color color = 1;
      Kind  kind  = 2;
    }
    ```

=== ":simple-python: mixed_pydantic.py"

    ```python
    class Color(str, _Enum):
        UNSPECIFIED = "UNSPECIFIED"
        RED = "RED"
        BLUE = "BLUE"


    class Shape(_ProtoModel):
        class Kind(str, _Enum):
            UNSPECIFIED = "UNSPECIFIED"
            CIRCLE = "CIRCLE"
            SQUARE = "SQUARE"

        color: "Color | None" = _Field(None)
        kind: "Shape.Kind | None" = _Field(None)
    ```

## Enum value options

Proto3 enum values can carry options (built-in or custom). These are preserved as accessible
metadata on the Python enum members.

### Built-in: `deprecated`

```proto
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_ACTIVE      = 1;
  STATUS_LEGACY      = 2 [deprecated = true];
}
```

```python
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    ACTIVE = "ACTIVE"
    LEGACY = "LEGACY"


# Access the deprecated option
print(Status.LEGACY.deprecated)  # True
```

### Built-in: `debug_redact`

```proto
enum Sensitivity {
  SENSITIVITY_UNSPECIFIED = 0;
  SENSITIVITY_PUBLIC      = 1;
  SENSITIVITY_SECRET      = 2 [(google.api.field_behavior) = OUTPUT_ONLY];
}
```

### Custom extensions

Custom enum value options are also preserved:

```proto
extend google.protobuf.EnumValueOptions {
  string display_name = 50001;
}

enum Color {
  COLOR_UNSPECIFIED = 0;
  COLOR_RED         = 1 [(display_name) = "Red"];
  COLOR_BLUE        = 2 [(display_name) = "Blue"];
}
```

```python
print(Color.RED.display_name)  # Red
print(Color.BLUE.display_name)  # Blue
```

## Enum in JSON / dict

Because enum values default to string names (with `auto_trim_enum_prefix=true`), they serialize
to ProtoJSON-compatible strings:

```python
from gen.status_pydantic import Status

msg = MyMessage(status=Status.ACTIVE)
print(msg.model_dump_json())  # {"status": "ACTIVE"}
```
