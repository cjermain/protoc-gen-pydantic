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
    ValidatedFloatIn,
    ValidatedFormats,
    ValidatedFormatsExtended,
    ValidatedIgnore,
    ValidatedIn,
    ValidatedNotContains,
    ValidatedRequired,
    ValidatedScalars,
    ValidatedStrings,
    ValidatedUnique,
    ValidatedWellKnownRegex,
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
| `string.hostname` | `Annotated[str, AfterValidator(_validate_hostname)]` |
| `string.uri_ref` | `Annotated[str, AfterValidator(_validate_uri_ref)]` |
| `string.address` | `Annotated[str, AfterValidator(_validate_address)]` |
| `string.tuuid` | `Annotated[str, AfterValidator(_validate_tuuid)]` |
| `string.ulid` | `Annotated[str, AfterValidator(_validate_ulid)]` |
| `string.ip_with_prefixlen` | `Annotated[str, AfterValidator(_validate_ip_with_prefixlen)]` |
| `string.ipv4_with_prefixlen` | `Annotated[str, AfterValidator(_validate_ipv4_with_prefixlen)]` |
| `string.ipv6_with_prefixlen` | `Annotated[str, AfterValidator(_validate_ipv6_with_prefixlen)]` |
| `string.ip_prefix` | `Annotated[str, AfterValidator(_validate_ip_prefix)]` |
| `string.ipv4_prefix` | `Annotated[str, AfterValidator(_validate_ipv4_prefix)]` |
| `string.ipv6_prefix` | `Annotated[str, AfterValidator(_validate_ipv6_prefix)]` |
| `string.host_and_port` | `Annotated[str, AfterValidator(_validate_host_and_port)]` |
| `string.well_known_regex = KNOWN_REGEX_HTTP_HEADER_NAME` | `Annotated[str, AfterValidator(_validate_http_header_name)]` |
| `string.well_known_regex = KNOWN_REGEX_HTTP_HEADER_VALUE` | `Annotated[str, AfterValidator(_validate_http_header_value)]` |
| `string.not_contains` | `Annotated[str, AfterValidator(_make_not_contains_validator(...))]` |
| `bytes.uuid` | `Annotated[bytes, AfterValidator(_validate_bytes_uuid)]` |

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

vs = ValidatedScalars(age=5, score=50.0, priority=1, rank=5)
assert vs.age == 5
try:
    ValidatedScalars(age=200, priority=1, rank=5)  # exceeds le=150
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

### Format validators

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

> **Note:** Non-optional proto3 scalar fields with format validators become **required** in the
> generated model — the empty string (proto3 zero value) would fail format validation. To allow
> empty strings, mark the field `optional` in proto3 or annotate it with
> `ignore = IGNORE_IF_ZERO_VALUE` (see [Zero-value validation](#zero-value-validation)).

The `string.email` validator requires the [`email-validator`](https://pypi.org/project/email-validator/)
package (`pip install email-validator` or add to your project dependencies).

```python exec="on" session="validate"
from pydantic import ValidationError

try:
    ValidatedFormats()  # email, website, address, token, host_v4, host_v6 are required
except ValidationError:
    pass
vf = ValidatedFormats(
    email="user@example.com",
    website="https://example.com",
    address="1.2.3.4",
    token="550e8400-e29b-41d4-a716-446655440000",
    host_v4="1.2.3.4",
    host_v6="::1",
)
assert vf.email == "user@example.com"
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

vi = ValidatedIn(status="active", priority=1, limit=10)
assert vi.status == "active"
try:
    ValidatedIn(status="pending", priority=1, limit=10)  # "pending" not in allowed set
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

`string.const`, integer `const` (int32, uint32, etc.), and `bool.const` translate to
`Literal[value]` type with a matching default — the field is essentially fixed at that
value. `float.const` and `double.const` use `AfterValidator(_make_const_validator(value))`
since `Literal[float]` is invalid per PEP 586:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedConst {
      string tag      = 1 [(buf.validate.field).string.const  = "fixed"];
      int32  count    = 2 [(buf.validate.field).int32.const   = 42];
      bool   active   = 3 [(buf.validate.field).bool.const    = true];
      double score    = 4 [(buf.validate.field).double.const  = 3.14];
      uint32 code     = 5 [(buf.validate.field).uint32.const  = 100];
      bool   inactive = 6 [(buf.validate.field).bool.const    = false];
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
assert vc.inactive is False
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

### Extended format validators

In addition to the core six (`email`, `uri`, `ip`, `ipv4`, `ipv6`, `uuid`), the following
string format constraints are also translated to `AfterValidator` wrappers:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedFormatsExtended {
      // Hostname must be a valid DNS hostname.
      string hostname = 1 [(buf.validate.field).string.hostname = true];
      // UriRef must be a valid URI reference (absolute or relative).
      string uri_ref = 2 [(buf.validate.field).string.uri_ref = true];
      // Addr must be a valid IP address or hostname.
      string addr = 3 [(buf.validate.field).string.address = true];
      // Tuuid must be a trimmed UUID (32 hex chars, no dashes).
      string tuuid = 4 [(buf.validate.field).string.tuuid = true];
      // Ulid must be a valid ULID.
      string ulid = 5 [(buf.validate.field).string.ulid = true];
      // Cidr must be a valid IP address with prefix length (host address).
      string cidr = 6 [(buf.validate.field).string.ip_with_prefixlen = true];
      // CidrV4 must be a valid IPv4 address with prefix length.
      string cidr_v4 = 7 [(buf.validate.field).string.ipv4_with_prefixlen = true];
      // CidrV6 must be a valid IPv6 address with prefix length.
      string cidr_v6 = 8 [(buf.validate.field).string.ipv6_with_prefixlen = true];
      // IpNet must be a valid IP network (host bits must be zero).
      string ip_net = 9 [(buf.validate.field).string.ip_prefix = true];
      // Ipv4Net must be a valid IPv4 network (host bits must be zero).
      string ipv4_net = 10 [(buf.validate.field).string.ipv4_prefix = true];
      // Ipv6Net must be a valid IPv6 network (host bits must be zero).
      string ipv6_net = 11 [(buf.validate.field).string.ipv6_prefix = true];
      // Endpoint must be a valid host:port pair.
      string endpoint = 12 [(buf.validate.field).string.host_and_port = true];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedFormatsExtended).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

try:
    ValidatedFormatsExtended()  # all format fields are required
except ValidationError:
    pass
vfe = ValidatedFormatsExtended(
    hostname="example.com",
    uri_ref="https://example.com",
    addr="example.com",
    tuuid="550e8400e29b41d4a716446655440000",
    ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    cidr="192.168.0.1/24",
    cidr_v4="192.168.0.1/24",
    cidr_v6="::1/128",
    ip_net="192.168.0.0/24",
    ipv4_net="192.168.0.0/24",
    ipv6_net="2001:db8::/32",
    endpoint="example.com:80",
)
assert vfe.hostname == "example.com"
assert vfe.endpoint == "example.com:80"
```

### `well_known_regex` (HTTP header names and values)

`string.well_known_regex` validates HTTP header names and values per RFC 7230:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedWellKnownRegex {
      // HeaderName must be a valid HTTP header name.
      string header_name = 1 [(buf.validate.field).string.well_known_regex = KNOWN_REGEX_HTTP_HEADER_NAME];
      // HeaderValue must be a valid HTTP header value.
      string header_value = 2 [(buf.validate.field).string.well_known_regex = KNOWN_REGEX_HTTP_HEADER_VALUE];
      // LooseHeader uses well_known_regex with strict=false (strict is not translated).
      string loose_header = 3 [(buf.validate.field).string = {
        well_known_regex: KNOWN_REGEX_HTTP_HEADER_NAME,
        strict: false
      }];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedWellKnownRegex).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vwkr = ValidatedWellKnownRegex(
    header_name="Content-Type",
    header_value="application/json",
    loose_header="Content-Type",
)
assert vwkr.header_name == "Content-Type"
try:
    ValidatedWellKnownRegex(
        header_name="Invalid Header\x00",
        header_value="application/json",
        loose_header="Content-Type",
    )  # header_name contains invalid character
except ValidationError:
    pass
```

> **Note:** `strict=false` (which loosens HTTP header validation) is not translated — the
> strict validator is always applied.

### String `not_contains`

`string.not_contains` rejects strings that include a given substring:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedNotContains {
      // Username must not contain "admin".
      string username = 1 [(buf.validate.field).string.not_contains = "admin"];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedNotContains).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vnc = ValidatedNotContains(username="alice")
assert vnc.username == "alice"
try:
    ValidatedNotContains(username="superadmin")  # contains "admin"
except ValidationError:
    pass
```

### Float / double `in` and `not_in`

`float.in`, `double.in`, `float.not_in`, and `double.not_in` work the same as their
integer and string counterparts:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedFloatIn {
      // Ratio must be one of the allowed values.
      float ratio = 1 [(buf.validate.field) = {float: {in: [0.25, 0.5, 0.75, 1.0]}}];
      // Score must not be a negative sentinel value.
      double score = 2 [(buf.validate.field) = {double: {not_in: [-1.0, -2.0]}}];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedFloatIn).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

vfi = ValidatedFloatIn(ratio=0.5, score=0.0)
assert vfi.ratio == 0.5
try:
    ValidatedFloatIn(ratio=0.3)  # not in allowed set
except ValidationError:
    pass
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

## Zero-value validation

In proto3, non-optional scalar fields always have a zero value (`""` for strings, `0` for
integers and floats, `false` for booleans, `b""` for bytes). If a field's constraints reject
that zero value, the generator makes the field **required** in the generated Pydantic model —
construction without an explicit value raises `ValidationError`.

This affects fields with:

- Format validators (`string.email`, `string.uri`, `string.ip`, etc.)
- `gt = N` where N ≥ 0, or `gte = N` where N > 0
- `string.min_len = N` where N > 0
- `string.pattern` (any pattern rejects the empty string)
- `in` constraints where the zero value is not a member of the allowed set

Fields with `const` constraints, repeated/map fields, `optional` proto3 fields, and oneof
members are not affected.

### Opting out with `ignore = IGNORE_IF_ZERO_VALUE`

To allow the zero value even when constraints would reject it, annotate the field with
`ignore = IGNORE_IF_ZERO_VALUE`. The generated field keeps its zero default, and validators
only run for explicitly-provided values:

=== ":lucide-file-code: validate.proto"

    ```proto
    message ValidatedIgnore {
      // Email allows empty string via ignore (not required).
      string email = 1 [
        (buf.validate.field).string.email = true,
        (buf.validate.field).ignore = IGNORE_IF_ZERO_VALUE
      ];
      // Age allows zero via ignore (not required).
      int32 age = 2 [
        (buf.validate.field).int32.gt = 0,
        (buf.validate.field).ignore = IGNORE_IF_ZERO_VALUE
      ];
    }
    ```

=== ":simple-python: validate_pydantic.py"

    ```python exec="on" session="validate"
    print(f"```python\n{inspect.getsource(ValidatedIgnore).rstrip()}\n```")
    ```

```python exec="on" session="validate"
from pydantic import ValidationError

# Zero values are allowed — construction without arguments works
vi = ValidatedIgnore()
assert vi.email == ""
assert vi.age == 0

# Non-zero values are still validated
try:
    ValidatedIgnore(email="not-an-email")
except ValidationError:
    pass
```

## `enum.defined_only`

`enum.defined_only = true` is a no-op in generated Python — Python enums already enforce
this natively by only accepting defined member values.
