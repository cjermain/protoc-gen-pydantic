---
icon: lucide/shield-check
---

# buf.validate

[buf.validate (protovalidate)](https://github.com/bufbuild/protovalidate) lets you annotate
proto fields with validation rules. `protoc-gen-pydantic` translates these rules into native
Pydantic constructs — no plugin option needed.

```python exec="on" session="validate"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.validate_pydantic import (
    ValidatedConst,
    ValidatedDropped,
    ValidatedFinite,
    ValidatedFormats,
    ValidatedIn,
    ValidatedRequired,
    ValidatedScalars,
    ValidatedStrings,
    ValidatedUnique,
)
```

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
| `string.contains` | `Field(pattern=<substring>)` |
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
| `float.const` / `double.const` | `Annotated[float, AfterValidator(_make_const_validator(value))]` |
| `float.finite` / `double.finite` | `Annotated[float, AfterValidator(_require_finite)]` |
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

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedScalars {
      // Age must be between 0 and 150 exclusive of 0.
      int32 age = 1 [(buf.validate.field).int32.gt = 0, (buf.validate.field).int32.lte = 150];
      // Score must be in [0.0, 100.0].
      double score = 2 [(buf.validate.field).double.gte = 0.0, (buf.validate.field).double.lte = 100.0];
      // Priority must be positive.
      int64 priority = 3 [(buf.validate.field).int64.gt = 0];
      // Ratio must be non-negative and less than 1.
      float ratio = 4 [(buf.validate.field).float.gte = 0.0, (buf.validate.field).float.lt = 1.0];
      // Rank must be in [1, 10].
      uint32 rank = 5 [(buf.validate.field).uint32.gte = 1, (buf.validate.field).uint32.lte = 10];
      // Count must be non-zero (covers uint64 / fixed64 literal formatting).
      optional uint64 count = 6 [(buf.validate.field).uint64.gt = 0];
      // Offset must be non-negative (covers sint32 / sfixed32 literal formatting).
      optional sint32 offset = 7 [(buf.validate.field).sint32.gte = 0];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedScalars).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vs = ValidatedScalars(age=5, score=50.0)
assert vs.age == 5
try:
    ValidatedScalars(age=200)  # exceeds le=150
except ValidationError:
    pass
```

### String constraints

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedStrings {
      // Name must be between 1 and 100 characters.
      string name = 1 [(buf.validate.field).string.min_len = 1, (buf.validate.field).string.max_len = 100];
      // Code must match uppercase letters only.
      string code = 2 [(buf.validate.field).string.pattern = "^[A-Z]+$"];
      // Bio has only a max length.
      string bio = 3 [(buf.validate.field).string.max_len = 500];
      // Tag has only a min length.
      string tag = 4 [(buf.validate.field).string.min_len = 2];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedStrings).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vs = ValidatedStrings(name="Alice", code="ABC", bio="test", tag="ab")
assert vs.name == "Alice"
try:
    ValidatedStrings(
        name="Alice", code="abc", bio="test", tag="ab"
    )  # code must be uppercase
except ValidationError:
    pass
```

### Format validators (email, URI, IP, UUID)

Format validators are translated to `AfterValidator` wrappers. The validators are
generated into `_proto_types.py` alongside the model files.

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedFormats {
      // Email must be a valid email address.
      string email = 1 [(buf.validate.field).string.email = true];
      // Website must be a valid URI.
      string website = 2 [(buf.validate.field).string.uri = true];
      // Address must be a valid IP address.
      string address = 3 [(buf.validate.field).string.ip = true];
      // Ratio must be finite (not inf or NaN).
      float ratio = 4 [(buf.validate.field).float.finite = true];
      // Token must be a valid UUID.
      string token = 5 [(buf.validate.field).string.uuid = true];
      // Host must be a valid IPv4 address.
      string host_v4 = 6 [(buf.validate.field).string.ipv4 = true];
      // Host must be a valid IPv6 address.
      string host_v6 = 7 [(buf.validate.field).string.ipv6 = true];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedFormats).rstrip()}\n```")
    ```

> **Note:** Empty strings skip format validation — this matches proto3 semantics where the
> zero value of a string field is `""`. Use `string.min_len = 1` to require a non-empty value.

The `string.email` validator requires the [`email-validator`](https://pypi.org/project/email-validator/)
package (`pip install email-validator` or add to your project dependencies).

```python exec="on" session="validate"
vf = ValidatedFormats()  # empty strings are allowed (proto3 zero value)
assert vf.email == ""
assert vf.website == ""
```

### Finite float / double

`float.finite = true` and `double.finite = true` reject `inf` and `NaN` values:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedFinite {
      // Ratio must be finite (not inf or NaN).
      float ratio = 1 [(buf.validate.field).float.finite = true];
      // Value must be finite (not inf or NaN).
      double value = 2 [(buf.validate.field).double.finite = true];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedFinite).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vf = ValidatedFinite(ratio=0.5, value=1.0)
assert vf.ratio == 0.5
try:
    ValidatedFinite(ratio=float("inf"))
except ValidationError:
    pass
```

### Set membership (`in` / `not_in`)

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedIn {
      string status   = 1 [(buf.validate.field) = {string: {in: ["active", "inactive"]}}];
      string code     = 2 [(buf.validate.field) = {string: {not_in: ["deleted", "archived"]}}];
      int32  priority = 3 [(buf.validate.field) = {int32: {in: [1, 2, 3]}}];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedIn).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vi = ValidatedIn(status="active")
assert vi.status == "active"
try:
    ValidatedIn(status="pending")  # not in allowed set
except ValidationError:
    pass
```

### Unique elements in repeated fields

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedUnique {
      repeated string tags   = 1 [(buf.validate.field).repeated.unique = true];
      repeated int32  scores = 2 [(buf.validate.field).repeated.unique = true];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedUnique).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vu = ValidatedUnique(tags=["a", "b"])
assert vu.tags == ["a", "b"]
try:
    ValidatedUnique(tags=["a", "a"])  # duplicates not allowed
except ValidationError:
    pass
```

### Const (fixed values)

`string.const`, `int.const`, and `bool.const` translate to `Literal[value]` type with a
matching default — the field is essentially fixed at that value. `float.const` and
`double.const` use `AfterValidator(_make_const_validator(value))` since `Literal[float]`
is invalid per PEP 586:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedConst {
      string tag    = 1 [(buf.validate.field).string.const  = "fixed"];
      int32  count  = 2 [(buf.validate.field).int32.const   = 42];
      bool   active = 3 [(buf.validate.field).bool.const    = true];
      double score  = 4 [(buf.validate.field).double.const  = 3.14];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedConst).rstrip()}\n```")
    ```

```python exec="on" session="validate"
vc = ValidatedConst()
assert vc.tag == "fixed"
assert vc.count == 42
assert vc.active is True
```

### Required (proto3 optional + required)

`required = true` behaves differently depending on the field type:

- **`proto3 optional` scalar**: strips `| None` from the type — the field becomes
  required at the Pydantic level (no default).
- **`proto3 optional` scalar + additional constraint**: same stripping, constraint also applied.
- **Message-typed optional**: cannot be translated — emits a `# buf.validate: required (not translated)` comment.
- **Plain proto3 scalar**: cannot be translated (already has a zero default) — emits a dropped comment.

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedRequired {
      // required on proto3 optional scalar: | None stripped, field becomes required.
      optional string required_name = 1 [(buf.validate.field).required = true];
      // required on proto3 optional scalar with an additional constraint.
      optional int32 required_score = 2 [
        (buf.validate.field).required = true,
        (buf.validate.field).int32.gt = 0
      ];
      // required on message-typed optional: not translated, emits dropped comment.
      optional Detail required_detail = 3 [(buf.validate.field).required = true];
      // required on plain proto3 scalar: not translated, emits dropped comment.
      string plain_name = 4 [(buf.validate.field).required = true];

      message Detail {
        string value = 1;
      }
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedRequired).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vr = ValidatedRequired(required_name="Alice", required_score=5)
assert vr.required_name == "Alice"
try:
    ValidatedRequired(required_score=5)  # required_name is required
except ValidationError:
    pass
```

## The `_proto_types.py` file

Format validators (`_validate_email`, `_validate_uri`, etc.), set validators
(`_make_in_validator`, `_make_not_in_validator`, `_require_unique`), and other helpers
(`_require_finite`, `_make_const_validator`) live in a generated `_proto_types.py` file
that is placed alongside the model files.

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
| `bytes.const` | `Literal[bytes]` is not supported |
| `duration.gt` / `timestamp.lte` / etc. | Message-typed bounds have no Field() equivalent |

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedDropped {
      // Name is required; the required constraint is not translated.
      string name = 1 [(buf.validate.field).required = true];
      // Blob has a bytes.const constraint which is not translated (bytes kind unsupported).
      bytes blob = 2 [(buf.validate.field).bytes.const = "\x01"];
      // Score must be positive; required is also set but not translated.
      int32 score = 3 [(buf.validate.field).required = true, (buf.validate.field).int32.gt = 0];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedDropped).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vd = ValidatedDropped(score=1)  # score gt=0 is still enforced
assert vd.score == 1
try:
    ValidatedDropped(score=0)  # score must be > 0
except ValidationError:
    pass
```

## `enum.defined_only`

`enum.defined_only = true` is a no-op in generated Python — Python enums already enforce
this natively by only accepting defined member values.
