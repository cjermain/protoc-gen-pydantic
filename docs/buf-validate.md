# buf.validate

[buf.validate (protovalidate)](https://github.com/bufbuild/protovalidate) lets you annotate
proto fields with validation rules. `protoc-gen-pydantic` translates these rules into native
Pydantic constructs — no plugin option needed.

## Setup

Add the BSR dependency to `buf.yaml`:

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
deps:
  - buf.build/bufbuild/protovalidate
```

Lock the dependency:

```sh
buf dep update
```

Import the validate file in your proto:

```proto
import "buf/validate/validate.proto";
```

## Constraint translations

| buf.validate rule | Generated Pydantic construct |
|---|---|
| Numeric `gt` | `Field(gt=...)` |
| Numeric `gte` | `Field(ge=...)` |
| Numeric `lt` | `Field(lt=...)` |
| Numeric `lte` | `Field(le=...)` |
| `string.min_len` | `Field(min_length=...)` |
| `string.max_len` | `Field(max_length=...)` |
| `string.len` | `Field(min_length=N, max_length=N)` |
| `string.pattern` | `Field(pattern=...)` |
| `string.prefix` | `Field(pattern=^prefix.*)` |
| `string.suffix` | `Field(pattern=.*suffix$)` |
| `string.prefix` + `string.suffix` | `Field(pattern=^prefix.*suffix$)` |
| `repeated.min_items` | `Field(min_length=...)` |
| `repeated.max_items` | `Field(max_length=...)` |
| `map.min_pairs` | `Field(min_length=...)` |
| `map.max_pairs` | `Field(max_length=...)` |
| `bytes.min_len` | `Field(min_length=...)` |
| `bytes.max_len` | `Field(max_length=...)` |
| `bytes.len` | `Field(min_length=N, max_length=N)` |
| `field.example` | `Field(examples=[...])` |
| `string.const` / `int.const` / `bool.const` | `Literal[value]` type + matching default |
| `string.in` / `int.in` / etc. | `Annotated[T, AfterValidator(_make_in_validator(frozenset({...})))]` |
| `string.not_in` / etc. | `Annotated[T, AfterValidator(_make_not_in_validator(frozenset({...})))]` |
| `repeated.unique` | `Annotated[list[T], AfterValidator(_require_unique)]` |
| `string.email` | `Annotated[str, AfterValidator(_validate_email)]` |
| `string.uri` | `Annotated[str, AfterValidator(_validate_uri)]` |
| `string.ip` | `Annotated[str, AfterValidator(_validate_ip)]` |
| `string.ipv4` | `Annotated[str, AfterValidator(_validate_ipv4)]` |
| `string.ipv6` | `Annotated[str, AfterValidator(_validate_ipv6)]` |
| `string.uuid` | `Annotated[str, AfterValidator(_validate_uuid)]` |

## Examples

### Numeric bounds

=== "validated.proto"

    ```proto
    message ValidatedScalars {
      // Age must be between 1 and 150 inclusive.
      int32 age = 1 [
        (buf.validate.field).int32.gt  = 0,
        (buf.validate.field).int32.lte = 150
      ];
      // Score must be in [0.0, 100.0].
      double score = 2 [
        (buf.validate.field).double.gte = 0.0,
        (buf.validate.field).double.lte = 100.0
      ];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedScalars(_ProtoModel):
        # Age must be between 1 and 150 inclusive.
        age: "int" = _Field(
            0,
            gt=0,
            le=150,
            description="Age must be between 1 and 150 inclusive.",
        )

        # Score must be in [0.0, 100.0].
        score: "float" = _Field(
            0.0,
            ge=0.0,
            le=100.0,
            description="Score must be in [0.0, 100.0].",
        )
    ```

### String constraints

=== "validated.proto"

    ```proto
    message ValidatedStrings {
      // Username: 1–50 chars, alphanumeric.
      string username = 1 [
        (buf.validate.field).string.min_len = 1,
        (buf.validate.field).string.max_len = 50,
        (buf.validate.field).string.pattern = "^[a-zA-Z0-9_]+$"
      ];
      // Country code: exactly 2 uppercase letters.
      string country_code = 2 [(buf.validate.field).string.len = 2];
      // URL must start with https://.
      string website = 3 [(buf.validate.field).string.prefix = "https://"];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedStrings(_ProtoModel):
        username: "str" = _Field("", min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
        country_code: "str" = _Field("", min_length=2, max_length=2)
        website: "str" = _Field("", pattern="^https://.*")
    ```

### Format validators (email, URI, IP, UUID)

Format validators are translated to `AfterValidator` wrappers. The validators are
generated into `_proto_types.py` alongside the model files.

=== "validated.proto"

    ```proto
    message ValidatedFormats {
      string email   = 1 [(buf.validate.field).string.email = true];
      string website = 2 [(buf.validate.field).string.uri   = true];
      string address = 3 [(buf.validate.field).string.ip    = true];
      string token   = 4 [(buf.validate.field).string.uuid  = true];
    }
    ```

=== "validated_pydantic.py"

    ```python
    from ._proto_types import _validate_email, _validate_ip, _validate_uri, _validate_uuid


    class ValidatedFormats(_ProtoModel):
        email: "_Annotated[str, _AfterValidator(_validate_email)]" = _Field("")
        website: "_Annotated[str, _AfterValidator(_validate_uri)]" = _Field("")
        address: "_Annotated[str, _AfterValidator(_validate_ip)]" = _Field("")
        token: "_Annotated[str, _AfterValidator(_validate_uuid)]" = _Field("")
    ```

> **Note:** Empty strings skip format validation — this matches proto3 semantics where the
> zero value of a string field is `""`. Use `string.min_len = 1` to require a non-empty value.

The `string.email` validator requires the [`email-validator`](https://pypi.org/project/email-validator/)
package (`pip install email-validator` or add to your project dependencies).

### Set membership (`in` / `not_in`)

=== "validated.proto"

    ```proto
    message ValidatedIn {
      string status   = 1 [(buf.validate.field) = {string: {in: ["active", "inactive"]}}];
      int32  priority = 2 [(buf.validate.field) = {int32: {in: [1, 2, 3]}}];
      string code     = 3 [(buf.validate.field) = {string: {not_in: ["deleted", "archived"]}}];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedIn(_ProtoModel):
        status: "_Annotated[str, _AfterValidator(_make_in_validator(frozenset({'active', 'inactive'})))]" = _Field(
            "",
        )
        priority: "_Annotated[int, _AfterValidator(_make_in_validator(frozenset({1, 2, 3})))]" = _Field(
            0,
        )
        code: "_Annotated[str, _AfterValidator(_make_not_in_validator(frozenset({'deleted', 'archived'})))]" = _Field(
            "",
        )
    ```

### Unique elements in repeated fields

=== "validated.proto"

    ```proto
    message ValidatedUnique {
      repeated string tags   = 1 [(buf.validate.field).repeated.unique = true];
      repeated int32  scores = 2 [(buf.validate.field).repeated.unique = true];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedUnique(_ProtoModel):
        tags: "_Annotated[list[str], _AfterValidator(_require_unique)]" = _Field(
            default_factory=list,
        )
        scores: "_Annotated[list[int], _AfterValidator(_require_unique)]" = _Field(
            default_factory=list,
        )
    ```

### Const (fixed values)

`string.const`, `int.const`, and `bool.const` translate to `Literal[value]` type with a
matching default — the field is essentially fixed at that value:

=== "validated.proto"

    ```proto
    message ValidatedConst {
      string tag    = 1 [(buf.validate.field).string.const = "fixed"];
      int32  count  = 2 [(buf.validate.field).int32.const  = 42];
      bool   active = 3 [(buf.validate.field).bool.const   = true];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedConst(_ProtoModel):
        tag: "_Literal['fixed']" = _Field("fixed")
        count: "_Literal[42]" = _Field(42)
        active: "_Literal[True]" = _Field(True)
    ```

> `float.const` and `double.const` are **not** translated — `Literal[float]` is invalid per
> PEP 586. They emit a `# buf.validate: float.const (not translated)` comment instead.

### Required (proto3 optional + required)

`required = true` on a `proto3 optional` scalar field strips `| None` from the type,
making the field required at the Pydantic level:

=== "validated.proto"

    ```proto
    message ValidatedRequired {
      optional string name  = 1 [(buf.validate.field).required = true];
      optional int32  score = 2 [
        (buf.validate.field).required = true,
        (buf.validate.field).int32.gt = 0
      ];
    }
    ```

=== "validated_pydantic.py"

    ```python
    class ValidatedRequired(_ProtoModel):
        # required strips | None → field has no default
        name: "str" = _Field(...)
        score: "int" = _Field(..., gt=0)
    ```

## The `_proto_types.py` file

Format validators (`_validate_email`, `_validate_uri`, etc.) and set validators
(`_make_in_validator`, `_make_not_in_validator`, `_require_unique`) live in a generated
`_proto_types.py` file that is placed alongside the model files.

This file is **conditional** — only helpers actually used by the proto files in that
directory are included. Unused imports (e.g. `ipaddress`, `AnyUrl`) are omitted.

```
gen/
└── api/v1/
    ├── user_pydantic.py
    ├── order_pydantic.py
    └── _proto_types.py        # generated helpers (only what's needed)
```

## Constraints not translated

The following constraints have no direct Pydantic equivalent and are emitted as comments
inside `_Field()` so they remain visible to developers:

| Constraint | Reason |
|---|---|
| `required` on message-typed or plain scalar fields | No Pydantic equivalent for proto3 plain scalars |
| CEL expressions | Arbitrary CEL cannot be expressed as a Pydantic validator |
| `float.const` / `double.const` | `Literal[float]` is invalid per PEP 586 |
| `bytes.const` | `Literal[bytes]` is not supported |
| `duration.gt` / `timestamp.lte` / etc. | Message-typed bounds have no Field() equivalent |

Example of a dropped constraint comment:

```python
class ValidatedDropped(_ProtoModel):
    name: "str" = _Field(
        "",
        # buf.validate: required (not translated)
    )
```

## `enum.defined_only`

`enum.defined_only = true` is a no-op in generated Python — Python enums already enforce
this natively by only accepting defined member values.
