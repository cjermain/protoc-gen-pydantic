---
icon: lucide/layers
---

# Generated Model API

Every generated `_pydantic.py` file contains a `_ProtoModel` base class that all message
classes in that file inherit from. It adds ProtoJSON-aware serialization on top of standard
Pydantic — no extra setup required.

## `_ProtoModel`

```python
class _ProtoModel(_BaseModel):
    """Base class for generated Pydantic models with ProtoJSON helpers."""
```

`_ProtoModel` is generated automatically. You never write or import it directly — you just use
the message classes that inherit from it.

### Default `model_config`

`_ProtoModel` sets several Pydantic config options to match proto3 / ProtoJSON semantics:

| Config key | Value | Effect |
|---|---|---|
| `use_enum_values` | `True` | Enum values (strings or ints) are stored, not enum members |
| `ser_json_bytes` | `"base64"` | `bytes` fields serialize to Base64 in JSON |
| `val_json_bytes` | `"base64"` | `bytes` fields are decoded from Base64 when parsing JSON |
| `ser_json_inf_nan` | `"strings"` | `inf` / `NaN` float values serialize as strings, not JSON `null` |

These defaults match proto3 JSON encoding rules so that `to_proto_json()` output is compatible
with proto-aware consumers.

### Serialization methods

#### `to_proto_json(**kwargs) -> str`

Serialize to a JSON string using ProtoJSON conventions:

- Omits fields at their **default (zero) value** (`exclude_defaults=True`)
- Uses **original proto field names** / camelCase aliases (`by_alias=True`)

```python
user = User(name="Alice", age=30, active=False)
user.to_proto_json()
# '{"name":"Alice","age":30}'  ← active omitted (False is the default)
```

You can override either default:

```python
user.to_proto_json(exclude_defaults=False)  # include zero-value fields
user.to_proto_json(by_alias=False)  # use Python attribute names
```

#### `to_proto_dict(**kwargs) -> dict`

Same as `to_proto_json()` but returns a Python `dict` instead of a JSON string:

```python
user.to_proto_dict()
# {'name': 'Alice', 'age': 30}
```

#### `from_proto_json(cls, json_str, **kwargs)`

Parse a JSON string into a model instance. Accepts both proto field names and Python names:

```python
user = User.from_proto_json('{"name":"Alice","age":30}')
```

#### `from_proto_dict(cls, data, **kwargs)`

Parse a `dict` into a model instance:

```python
user = User.from_proto_dict({"name": "Alice", "age": 30})
```

### `to_proto_json()` vs `model_dump_json()`

Both methods produce valid JSON, but they differ in defaults:

| | `to_proto_json()` | `model_dump_json()` |
|---|---|---|
| Zero-value fields | **omitted** | included |
| Field names | **proto / camelCase aliases** | Python attribute names |
| Proto compatibility | ✓ | requires `by_alias=True, exclude_defaults=True` |

Use `to_proto_json()` when the JSON will be consumed by a proto-aware service or stored in a
proto-compatible format. Use `model_dump_json()` (plain Pydantic) when you need full control
over inclusion of zero-value fields or are working in a purely Python context.

---

## `_proto_types.py`

Alongside each `_pydantic.py` file, the generator writes `_proto_types.py`. This file contains
type aliases and helper functions used by the generated models. It is **conditional** — only
helpers actually needed by the proto files in that directory are included.

```
gen/
└── api/v1/
    ├── user_pydantic.py
    ├── order_pydantic.py
    └── _proto_types.py        ← generated alongside model files
```

### 64-bit integer types

Proto3 encodes `int64`, `sint64`, `sfixed64`, `uint64`, `fixed64`, and `uint64` as **strings**
in JSON (to avoid JavaScript integer overflow). The generated aliases handle this automatically:

| Type alias | Proto types | JSON representation |
|---|---|---|
| `ProtoInt64` | `int64`, `sint64`, `sfixed64` | `"123"` (string) |
| `ProtoUInt64` | `uint64`, `fixed64`, `uint64` | `"123"` (string) |

Both are annotated `int` in Python — arithmetic works normally. The string serialization only
applies in JSON:

```python
from gen.api.v1.scalars_pydantic import Scalars

s = Scalars(int64=9007199254740993)  # larger than JS MAX_SAFE_INTEGER
s.to_proto_json()
# '{"int64":"9007199254740993"}'  ← serialized as string
s.int64 + 1  # arithmetic works normally in Python → 9007199254740994
```

### Timestamp and Duration

`google.protobuf.Timestamp` and `google.protobuf.Duration` map to Python's `datetime.datetime`
and `datetime.timedelta` respectively, with proto-wire-format JSON serialization:

| Type alias | Python type | JSON format |
|---|---|---|
| `ProtoTimestamp` | `datetime.datetime` | RFC 3339 / ISO 8601 with `Z` suffix |
| `ProtoDuration` | `datetime.timedelta` | `"<seconds>s"` string (e.g. `"3600s"`) |

```python
import datetime
from gen.api.v1.event_pydantic import Event

event = Event(
    occurred=datetime.datetime.now(datetime.timezone.utc),
    duration=datetime.timedelta(hours=1),
)
event.to_proto_json()
# '{"occurred":"2024-01-15T10:30:00Z","duration":"3600s"}'
```

`ProtoTimestamp` accepts both `datetime` objects and ISO 8601 strings (with `Z` suffix) as
input, so you can parse directly from JSON payloads:

```python
Event.from_proto_json('{"occurred":"2024-01-15T10:30:00Z","duration":"3600s"}')
```
