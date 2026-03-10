---
icon: lucide/shield
---

# Reserved Names

Proto field names can clash with Python builtins, keywords, and Pydantic `BaseModel`
attributes. `protoc-gen-pydantic` handles these automatically using a **PEP 8 trailing
underscore alias**.

```python exec="on" session="reserved-names"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.reserved_names_pydantic import BuiltinNames, ReservedFieldNames
```

## How it works

When a proto field name is a reserved word in Python, the generator:

1. Appends `_` to the Python attribute name (e.g. `bool` → `bool_`)
2. Sets `alias="<original_name>"` on the field so JSON / dict serialization still uses
   the original proto name
3. Adds `populate_by_name=True` to `model_config` so you can pass either the alias or
   the Python name when constructing the model

=== ":lucide-file-code: reserved_names.proto"

    ```proto
    message BuiltinNames {
      bool  bool  = 1;
      float float = 2;
      bytes bytes = 3;
      int32 int   = 4;
    }
    ```

=== ":simple-python: reserved_names_pydantic.py"

    ```python exec="on" session="reserved-names"
    print(f"```python\n{inspect.getsource(BuiltinNames).rstrip()}\n```")
    ```

```python exec="on" session="reserved-names"
b = BuiltinNames(bool_=True, float_=3.14)
assert b.bool_ is True
assert b.float_ == 3.14
assert b.model_dump() == {"bool": True, "float": 3.14}
```

## Reserved name categories

The following categories of names trigger the trailing-underscore rename:

**Python builtins**: `bool`, `bytes`, `complex`, `dict`, `float`, `frozenset`, `int`,
`list`, `map`, `object`, `set`, `str`, `tuple`, `type`, …

**Python keywords**: `and`, `as`, `assert`, `async`, `await`, `break`, `class`,
`continue`, `def`, `del`, `elif`, `else`, `except`, `finally`, `for`, `from`,
`global`, `if`, `import`, `in`, `is`, `lambda`, `nonlocal`, `not`, `or`, `pass`,
`raise`, `return`, `try`, `while`, `with`, `yield`, `False`, `None`, `True`

**Pydantic BaseModel attributes**: `model_config`, `model_fields`, `model_dump`,
`model_validate`, `model_json_schema`, and other `model_*` names that would shadow
Pydantic internals

=== ":lucide-file-code: reserved_names.proto"

    ```proto
    message ReservedFieldNames {
      string model_config = 1;
      string model_fields = 2;
      string model_dump   = 3;
    }
    ```

=== ":simple-python: reserved_names_pydantic.py"

    ```python exec="on" session="reserved-names"
    print(f"```python\n{inspect.getsource(ReservedFieldNames).rstrip()}\n```")
    ```

```python exec="on" session="reserved-names"
r = ReservedFieldNames(model_config_="cfg", model_fields_="flds")
assert r.model_config_ == "cfg"
assert r.model_dump() == {"model_config": "cfg", "model_fields": "flds"}
```

## Using the aliased fields

Because `populate_by_name=True` is set, you can use either the Python name or the proto alias:

```python
# Using the Python name (trailing underscore)
b = BuiltinNames(bool_=True, float_=3.14)

# Using the original proto alias
b = BuiltinNames(**{"bool": True, "float": 3.14})

# Serialization always uses the proto name (no trailing underscore)
print(b.model_dump())
# {"bool": True, "float": 3.14}
```

```python exec="on" session="reserved-names"
b1 = BuiltinNames(bool_=True, float_=3.14)
b2 = BuiltinNames(**{"bool": True, "float": 3.14})
assert b1 == b2
assert b1.model_dump() == {"bool": True, "float": 3.14}
```

## buf.validate + reserved names

When a reserved field also carries `buf.validate` constraints, both the `alias=` and the
constraint kwargs are emitted in a single `_Field()` call:

```proto
message ValidatedReserved {
  float float = 1 [(buf.validate.field).float.gt = 0.0];
}
```

```python
class ValidatedReserved(_ProtoModel):
    model_config = _ConfigDict(populate_by_name=True, ...)

    float_: "float" = _Field(0.0, alias="float", gt=0.0)
```
