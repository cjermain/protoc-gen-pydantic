# Plugin Options

Options control how `protoc-gen-pydantic` generates Python output. They are passed via:

- **buf**: `opt:` in `buf.gen.yaml`
- **protoc**: `--pydantic_opt=` flag(s)

## Summary

| Option | Default | Description |
|---|---|---|
| `preserving_proto_field_name` | `true` | Use snake_case proto names instead of camelCase |
| `auto_trim_enum_prefix` | `true` | Remove enum type prefix from value names |
| `use_integers_for_enums` | `false` | Use integer values instead of string names |
| `disable_field_description` | `false` | Omit `description=` from field annotations |
| `use_none_union_syntax_instead_of_optional` | `true` | Use `T \| None` instead of `Optional[T]` |

---

## `preserving_proto_field_name`

Controls whether field names use the proto snake_case name or the camelCase JSON name.

**Default:** `true` (snake_case)

::: code-group

```proto [user.proto]
message User {
  bool   is_active  = 1;
  string first_name = 2;
}
```

```python [true (default)]
class User(_ProtoModel):
    is_active: "bool" = _Field(False)
    first_name: "str" = _Field("")
```

```python [false]
class User(_ProtoModel):
    isActive: "bool" = _Field(False)
    firstName: "str" = _Field("")
```

:::

**buf.gen.yaml:**
```yaml
opt:
  - preserving_proto_field_name=false
```

**protoc:**
```sh
--pydantic_opt=preserving_proto_field_name=false
```

---

## `auto_trim_enum_prefix` {#auto-trim-enum-prefix}

Removes the enum type name prefix (case-insensitive, with trailing `_`) from value names.

**Default:** `true` (trim prefix)

::: code-group

```proto [status.proto]
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_OK          = 1;
  STATUS_ERROR       = 2;
}
```

```python [true (default)]
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    OK = "OK"
    ERROR = "ERROR"
```

```python [false]
class Status(str, _Enum):
    STATUS_UNSPECIFIED = "STATUS_UNSPECIFIED"
    STATUS_OK = "STATUS_OK"
    STATUS_ERROR = "STATUS_ERROR"
```

:::

**buf.gen.yaml:**
```yaml
opt:
  - auto_trim_enum_prefix=false
```

---

## `use_integers_for_enums` {#use-integers-for-enums}

When enabled, enums use `int` as the mixin type and integer values instead of string names.

**Default:** `false` (string values)

::: code-group

```proto [status.proto]
enum Status {
  STATUS_UNSPECIFIED = 0;
  STATUS_OK          = 1;
  STATUS_ERROR       = 2;
}
```

```python [false (default)]
class Status(str, _Enum):
    UNSPECIFIED = "UNSPECIFIED"
    OK = "OK"
    ERROR = "ERROR"
```

```python [true]
class Status(int, _Enum):
    UNSPECIFIED = 0
    OK = 1
    ERROR = 2
```

:::

**buf.gen.yaml:**
```yaml
opt:
  - use_integers_for_enums=true
```

---

## `disable_field_description`

When enabled, omits `description=` from generated `_Field()` calls even when the proto field
has a comment. The inline Python comment is still emitted.

**Default:** `false` (include descriptions)

::: code-group

```proto [user.proto]
message User {
  // The user's display name.
  string name = 1;
}
```

```python [false (default)]
class User(_ProtoModel):
    # The user's display name.
    name: "str" = _Field("", description="The user's display name.")
```

```python [true]
class User(_ProtoModel):
    # The user's display name.
    name: "str" = _Field("")
```

:::

**buf.gen.yaml:**
```yaml
opt:
  - disable_field_description=true
```

---

## `use_none_union_syntax_instead_of_optional`

Controls how nullable types are expressed in annotations.

**Default:** `true` (`T | None` union syntax)

::: code-group

```proto [user.proto]
message User {
  optional string nickname = 1;
}
```

```python [true (default)]
class User(_ProtoModel):
    nickname: "str | None" = _Field(None)
```

```python [false]
from typing import Optional as _Optional


class User(_ProtoModel):
    nickname: "_Optional[str]" = _Field(None)
```

:::

> The `T | None` syntax requires Python 3.10+ for runtime evaluation. Generated files use
> string annotations (`"T | None"`) so they are forward-compatible with Python 3.9.

**buf.gen.yaml:**
```yaml
opt:
  - use_none_union_syntax_instead_of_optional=false
```

---

## Combining options

Multiple options can be specified together:

```yaml
# buf.gen.yaml
plugins:
  - local: protoc-gen-pydantic
    opt:
      - paths=source_relative
      - preserving_proto_field_name=false
      - auto_trim_enum_prefix=false
      - use_integers_for_enums=true
      - disable_field_description=true
    out: gen
```

```sh
# protoc
protoc --pydantic_opt=preserving_proto_field_name=false,auto_trim_enum_prefix=false \
       --pydantic_opt=use_integers_for_enums=true \
       ...
```
