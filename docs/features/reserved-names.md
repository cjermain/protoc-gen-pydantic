# Reserved Names

Proto field names can clash with Python builtins, keywords, and Pydantic `BaseModel`
attributes. `protoc-gen-pydantic` handles these automatically using a **PEP 8 trailing
underscore alias**.

## How it works

When a proto field name is a reserved word in Python, the generator:

1. Appends `_` to the Python attribute name (e.g. `bool` → `bool_`)
2. Sets `alias="<original_name>"` on the field so JSON / dict serialization still uses
   the original proto name
3. Adds `populate_by_name=True` to `model_config` so you can pass either the alias or
   the Python name when constructing the model

=== "reserved.proto"

    ```proto
    message Scalars {
      bool  bool  = 1;
      float float = 2;
      bytes bytes = 3;
      int   int   = 4;   // 'int' is also reserved
    }
    ```

=== "reserved_pydantic.py"

    ```python
    class Scalars(_ProtoModel):
        model_config = _ConfigDict(populate_by_name=True, ...)

        bool_: "bool" = _Field(False, alias="bool")
        float_: "float" = _Field(0.0, alias="float")
        bytes_: "bytes" = _Field(b"", alias="bytes")
        int_: "int" = _Field(0, alias="int")
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

## Using the aliased fields

Because `populate_by_name=True` is set, you can use either the Python name or the proto alias:

```python
# Using the Python name (trailing underscore)
s = Scalars(bool_=True, float_=3.14)

# Using the original proto alias
s = Scalars(**{"bool": True, "float": 3.14})

# Serialization always uses the proto name (no trailing underscore)
print(s.model_dump())
# {"bool": True, "float": 3.14, "bytes": b"", "int": 0}
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
