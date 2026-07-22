---
icon: lucide/sliders
---

# Plugin Options

Options control how `protoc-gen-pydantic` generates Python output. They are passed via:

- **buf**: `opt:` in `buf.gen.yaml`
- **protoc**: `--pydantic_opt=` flag(s)

## Summary

| Option | Default | Description |
|---|---|---|
| `preserving_proto_field_name` | `true` | Use snake_case proto names instead of camelCase |
| `camel_case_alias` | `true` | Add a camelCase JSON `alias=` to every field, independent of attribute casing |
| `auto_trim_enum_prefix` | `true` | Remove enum type prefix from value names |
| `use_integers_for_enums` | `false` | Use integer values instead of string names |
| `disable_field_description` | `false` | Omit `description=` from field annotations |
| `use_none_union_syntax_instead_of_optional` | `true` | Use `T \| None` instead of `Optional[T]` |
| `disable_validate` | `false` | Omit all buf.validate constraints and CEL validators from generated models |

---

## `preserving_proto_field_name`

Controls whether the **Python attribute name** uses the proto snake_case name or the camelCase
JSON name. This is independent of the wire/JSON name, which [`camel_case_alias`](#camel_case_alias)
controls — see that option for how the two combine.

**Default:** `true` (snake_case attribute)

=== ":lucide-file-code: user.proto"

    ```proto
    message User {
      bool   is_active  = 1;
      string first_name = 2;
    }
    ```

=== "true (default)"

    ```python
    class User(_ProtoModel):
        model_config = _ConfigDict(populate_by_name=True, ...)

        is_active: "bool" = _Field(default=False, alias="isActive")
        first_name: "str" = _Field(default="", alias="firstName")
    ```

=== "false"

    ```python
    class User(_ProtoModel):
        isActive: "bool" = _Field(default=False)
        firstName: "str" = _Field(default="")
    ```

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

## `camel_case_alias` {#camel_case_alias}

Adds `alias="<camelCase JSON name>"` to every field whose wire name would otherwise differ
from its Python attribute name, and enables `populate_by_name=True` on the message. This keeps
the Python attribute governed solely by `preserving_proto_field_name` while making the JSON/dict
wire format default to camelCase — the canonical proto3 JSON encoding used by most
cross-language protobuf tooling (grpc-gateway, Envoy, TypeScript/JS clients, etc).

Both spellings are always accepted on input regardless of this option's value: the Python
attribute name (via `populate_by_name=True`) and, when set, the alias.

**Default:** `true` (camelCase wire alias)

=== ":lucide-file-code: user.proto"

    ```proto
    message User {
      string first_name = 1;
    }
    ```

=== "true (default)"

    ```python
    class User(_ProtoModel):
        model_config = _ConfigDict(populate_by_name=True, ...)

        first_name: "str" = _Field(default="", alias="firstName")
    ```

=== "false"

    ```python
    class User(_ProtoModel):
        first_name: "str" = _Field(default="")
    ```

```python
User(first_name="Ada")  # Python attribute name — always works
User(**{"firstName": "Ada"})  # camelCase alias — only when camel_case_alias=true

# By default, serialization uses the alias:
User(first_name="Ada").model_dump()  # {"firstName": "Ada"}
User(first_name="Ada").model_dump(by_alias=False)  # {"first_name": "Ada"}
```

**buf.gen.yaml:**
```yaml
opt:
  - camel_case_alias=false
```

**protoc:**
```sh
--pydantic_opt=camel_case_alias=false
```

---

## `auto_trim_enum_prefix` {#auto-trim-enum-prefix}

Removes the enum type name prefix (case-insensitive, with trailing `_`) from value names.

**Default:** `true` (trim prefix)

=== ":lucide-file-code: status.proto"

    ```proto
    enum Status {
      STATUS_UNSPECIFIED = 0;
      STATUS_OK          = 1;
      STATUS_ERROR       = 2;
    }
    ```

=== "true (default)"

    ```python
    class Status(_ProtoEnum):
        UNSPECIFIED = ("UNSPECIFIED", 0)
        OK = ("OK", 1)
        ERROR = ("ERROR", 2)
    ```

=== "false"

    ```python
    class Status(_ProtoEnum):
        STATUS_UNSPECIFIED = ("STATUS_UNSPECIFIED", 0)
        STATUS_OK = ("STATUS_OK", 1)
        STATUS_ERROR = ("STATUS_ERROR", 2)
    ```

**buf.gen.yaml:**
```yaml
opt:
  - auto_trim_enum_prefix=false
```

---

## `use_integers_for_enums` {#use-integers-for-enums}

When enabled, enums use `int` as the mixin type and integer values instead of string names.

**Default:** `false` (string values)

=== ":lucide-file-code: status.proto"

    ```proto
    enum Status {
      STATUS_UNSPECIFIED = 0;
      STATUS_OK          = 1;
      STATUS_ERROR       = 2;
    }
    ```

=== "false (default)"

    ```python
    class Status(_ProtoEnum):
        UNSPECIFIED = ("UNSPECIFIED", 0)
        OK = ("OK", 1)
        ERROR = ("ERROR", 2)
    ```

=== "true"

    ```python
    class Status(_ProtoEnum):
        UNSPECIFIED = 0
        OK = 1
        ERROR = 2
    ```

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

=== ":lucide-file-code: user.proto"

    ```proto
    message User {
      // The user's display name.
      string name = 1;
    }
    ```

=== "false (default)"

    ```python
    class User(_ProtoModel):
        # The user's display name.
        name: "str" = _Field(default="", description="The user's display name.")
    ```

=== "true"

    ```python
    class User(_ProtoModel):
        # The user's display name.
        name: "str" = _Field(default="")
    ```

**buf.gen.yaml:**
```yaml
opt:
  - disable_field_description=true
```

---

## `use_none_union_syntax_instead_of_optional`

Controls how nullable types are expressed in annotations.

**Default:** `true` (`T | None` union syntax)

=== ":lucide-file-code: user.proto"

    ```proto
    message User {
      optional string nickname = 1;
    }
    ```

=== "true (default)"

    ```python
    class User(_ProtoModel):
        nickname: "str | None" = _Field(default=None)
    ```

=== "false"

    ```python
    from typing import Optional as _Optional


    class User(_ProtoModel):
        nickname: "_Optional[str]" = _Field(default=None)
    ```

> The `T | None` syntax requires Python 3.10+ for runtime evaluation. Generated files use
> string annotations (`"T | None"`) so they are forward-compatible with Python 3.9.

**buf.gen.yaml:**
```yaml
opt:
  - use_none_union_syntax_instead_of_optional=false
```

---

## `disable_validate` {#disable-validate}

When enabled, all `buf.validate` constraints and CEL validators are omitted from the generated
output. The result is identical to what would be produced if the proto files had no
`import "buf/validate/validate.proto"` and no `(buf.validate.field)` or
`(buf.validate.message)` options.

Fields that would otherwise be required due to constraints (e.g., a `string.email` field with
no valid zero value) revert to their proto3 zero-value defaults (`""`, `0`, `false`, etc.).

**Default:** `false` (include buf.validate constraints)

=== ":lucide-file-code: user.proto"

    ```proto
    import "buf/validate/validate.proto";

    message User {
      string email = 1 [(buf.validate.field).string.email = true];
    }
    ```

=== "false (default)"

    ```python
    class User(_ProtoModel):
        email: _Annotated[str, _AfterValidator(_validate_email)]
    ```

=== "true"

    ```python
    class User(_ProtoModel):
        email: str = _Field(default="")
    ```

**buf.gen.yaml:**
```yaml
opt:
  - disable_validate=true
```

**protoc:**
```sh
--pydantic_opt=disable_validate=true
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
      - camel_case_alias=false
      - auto_trim_enum_prefix=false
      - use_integers_for_enums=true
      - disable_field_description=true
    out: gen
```

```sh
# protoc
protoc --pydantic_opt=preserving_proto_field_name=false,camel_case_alias=false,auto_trim_enum_prefix=false \
       --pydantic_opt=use_integers_for_enums=true \
       ...
```
