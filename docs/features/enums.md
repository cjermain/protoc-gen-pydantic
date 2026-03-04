---
icon: lucide/list-tree
---

# Enums

Proto3 enums become Python `Enum` subclasses. The generator supports string-valued enums
(default), integer-valued enums (opt-in), enum value options, and the well-known
`auto_trim_enum_prefix` behaviour.

```python exec="on" session="enums"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.enums_pydantic import Hue, Shape
from api.v1.enum_options_pydantic import Status
from api.v1.custom_options_pydantic import Currency
```

## Basic enum

By default, enums use `str` as the mixin type and string names as values:

=== ":lucide-file-code: enums.proto"

    ```proto
    enum Hue {
      HUE_UNSPECIFIED = 0;
      HUE_RED         = 1;
      HUE_BLUE        = 2;
    }
    ```

=== ":simple-python: enums_pydantic.py"

    ```python exec="on" session="enums"
    print(f"```python\n{inspect.getsource(Hue).rstrip()}\n```")
    ```

```python exec="on" session="enums"
assert Hue.RED == "RED"
assert Hue.BLUE == "BLUE"
assert isinstance(Hue.RED, str)
```

## Prefix trimming (`auto_trim_enum_prefix`)

The default `auto_trim_enum_prefix=true` removes the enum type name prefix from value names.
The prefix match is case-insensitive and strips a trailing `_`:

```
HUE_UNSPECIFIED → UNSPECIFIED
HUE_RED         → RED
```

With `auto_trim_enum_prefix=false` the full name is kept:

```python
class Hue(str, _Enum):
    HUE_UNSPECIFIED = "HUE_UNSPECIFIED"
    HUE_RED = "HUE_RED"
    HUE_BLUE = "HUE_BLUE"
```

See [Plugin Options](../options.md#auto-trim-enum-prefix) for details.

## Integer enums (`use_integers_for_enums`)

With `use_integers_for_enums=true`, the mixin type becomes `int` and values are integers:

```python
class Hue(int, _Enum):
    UNSPECIFIED = 0
    RED = 1
    BLUE = 2
```

See [Plugin Options](../options.md#use-integers-for-enums) for details.

## Top-level vs. nested enums

Enums defined at the file level become top-level classes. Enums defined inside a message
become nested classes of that message:

=== ":lucide-file-code: enums.proto"

    ```proto
    // Top-level enum
    enum Hue {
      HUE_UNSPECIFIED = 0;
      HUE_RED         = 1;
      HUE_BLUE        = 2;
    }

    message Shape {
      // Nested enum
      enum Kind {
        KIND_UNSPECIFIED = 0;
        KIND_CIRCLE      = 1;
        KIND_SQUARE      = 2 [deprecated = true];
      }

      Hue  color = 1;
      Kind kind  = 2;
    }
    ```

=== ":simple-python: enums_pydantic.py"

    ```python exec="on" session="enums"
    hue_src = inspect.getsource(Hue).rstrip()
    shape_src = inspect.getsource(Shape).rstrip()
    print(f"```python\n{hue_src}\n\n\n{shape_src}\n```")
    ```

```python exec="on" session="enums"
assert Shape.Kind.CIRCLE == "CIRCLE"
shape = Shape(color=Hue.RED, kind=Shape.Kind.CIRCLE)
assert shape.color == "RED"
assert shape.kind == "CIRCLE"
```

> **Note:** `KIND_SQUARE` carries `[deprecated = true]`, so `Shape.Kind` is generated as
> `_ProtoEnum` with value tuples instead of plain `str, _Enum`. See
> [Enum value options](#enum-value-options) below.

## Enum value options

Proto3 enum values can carry options (built-in or custom). These are preserved as accessible
metadata on the Python enum members.

### Built-in: `deprecated` and `debug_redact`

```proto
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_ACTIVE      = 1;
  STATUS_INACTIVE    = 2;
  STATUS_ARCHIVED    = 3 [deprecated = true, debug_redact = true];
}
```

=== ":simple-python: enum_options_pydantic.py"

    ```python exec="on" session="enums"
    print(f"```python\n{inspect.getsource(Status).rstrip()}\n```")
    ```

When any enum value in a file carries options, the generator switches from plain `str, _Enum`
to `_ProtoEnum` (a thin subclass) and stores options as a second tuple element. Each member's
options are accessible via the `.options` property.

```python exec="on" session="enums"
assert Status.ARCHIVED.options.deprecated is True
assert Status.ARCHIVED.options.debug_redact is True
assert Status.ACTIVE.options.deprecated is False
```

### Custom extensions

Custom enum value options are also preserved:

=== ":simple-python: custom_options_pydantic.py"

    ```python exec="on" session="enums"
    print(f"```python\n{inspect.getsource(Currency).rstrip()}\n```")
    ```

```python exec="on" session="enums"
assert Currency.USD.options.display_name == "US Dollar"
assert Currency.EUR.options.display_name == "Euro"
assert Currency.GBP.options.display_name == "British Pound"
assert Currency.USD.options.is_default is True
assert Currency.USD.options.priority == 1
```

## Enum in JSON / dict

Because enum values default to string names (with `auto_trim_enum_prefix=true`), they serialize
to ProtoJSON-compatible strings:

```python
import json

from enums_pydantic import Hue

print(json.dumps({"hue": Hue.RED}))
# {"hue": "RED"}
```

```python exec="on" session="enums"
import json

assert json.dumps({"hue": Hue.RED}) == '{"hue": "RED"}'
```
