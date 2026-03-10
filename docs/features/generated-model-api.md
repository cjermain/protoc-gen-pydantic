---
icon: lucide/layers
---

# Generated Model API

Every generated `_pydantic.py` file contains a `_ProtoModel` base class that all message
classes in that file inherit from. It overrides `model_dump` and `model_dump_json` to apply
ProtoJSON defaults automatically — no extra setup required.

```python exec="on" session="api"
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from pydantic import BaseModel as _BaseModel, ConfigDict, Field as _Field

from api.v1.known_types_pydantic import WellKnownTypes
from api.v1.scalars_pydantic import Scalars


class _ProtoModel(_BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        ser_json_bytes="base64",
        val_json_bytes="base64",
        ser_json_inf_nan="strings",
    )

    def model_dump(self, **kwargs):
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs):
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("by_alias", True)
        return super().model_dump_json(**kwargs)


class User(_ProtoModel):
    name: str = _Field(default="")
    age: int = _Field(default=0)
    active: bool = _Field(default=False)
```

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

These defaults match proto3 JSON encoding rules so that `model_dump_json()` output is compatible
with proto-aware consumers.

### Serialization methods

#### `model_dump(**kwargs) -> dict`

Serialize to a `dict` using ProtoJSON conventions:

- Omits fields at their **default (zero) value** (`exclude_defaults=True`)
- Uses **original proto field names** (`by_alias=True`)

```python
user = User(name="Alice", age=30, active=False)
user.model_dump()
# {'name': 'Alice', 'age': 30}  ← active omitted (False is the default)
```

You can override either default:

```python
user.model_dump(exclude_defaults=False)  # include zero-value fields
user.model_dump(by_alias=False)  # use Python attribute names
```

#### `model_dump_json(**kwargs) -> str`

Same as `model_dump()` but returns a JSON string:

```python
user.model_dump_json()
# '{"name":"Alice","age":30}'
```

#### Deserialization

Use standard Pydantic class methods — no custom wrappers needed:

```python
user = User.model_validate({"name": "Alice", "age": 30})
user = User.model_validate_json('{"name":"Alice","age":30}')
```

```python exec="on" session="api"
user = User(name="Alice", age=30, active=False)
assert user.model_dump_json() == '{"name":"Alice","age":30}'
assert user.model_dump() == {"name": "Alice", "age": 30}
assert User.model_validate_json('{"name":"Alice","age":30}') == User(name="Alice", age=30)
assert User.model_validate({"name": "Alice", "age": 30}) == User(name="Alice", age=30)
```

### `model_dump()` vs plain Pydantic

`_ProtoModel` overrides `model_dump` and `model_dump_json` so that ProtoJSON defaults apply
everywhere — including when a ProtoModel is **nested inside another model**:

| | `_ProtoModel` (generated) | Plain `BaseModel` |
|---|---|---|
| Zero-value fields | **omitted** by default | included by default |
| Field names | **original proto field names** by default | Python attribute names by default |
| Nested serialization | ProtoJSON defaults apply | standard Pydantic defaults apply |

Override the defaults by passing kwargs explicitly:

```python
user.model_dump(exclude_defaults=False)  # include zero-value fields
user.model_dump(by_alias=False)          # use Python attribute names
```

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

Proto3 encodes `int64`, `sint64`, `sfixed64`, `uint64`, and `fixed64` as **strings**
in JSON (to avoid JavaScript integer overflow). The generated aliases handle this automatically:

| Type alias | Proto types | JSON representation |
|---|---|---|
| `ProtoInt64` | `int64`, `sint64`, `sfixed64` | `"123"` (string) |
| `ProtoUInt64` | `uint64`, `fixed64` | `"123"` (string) |

Both are annotated `int` in Python — arithmetic works normally. The string serialization only
applies in JSON:

```python
from api.v1.scalars_pydantic import Scalars

s = Scalars(int64=9007199254740993)  # larger than JS MAX_SAFE_INTEGER
s.model_dump_json()
# '{"int64":"9007199254740993"}'  ← serialized as string
s.int64 + 1  # arithmetic works normally in Python → 9007199254740994
```

```python exec="on" session="api"
s = Scalars(int64=9007199254740993)
assert s.model_dump_json() == '{"int64":"9007199254740993"}'
assert s.int64 + 1 == 9007199254740994
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
from api.v1.event_pydantic import Event

event = Event(
    occurred=datetime.datetime.now(datetime.timezone.utc),
    duration=datetime.timedelta(hours=1),
)
event.model_dump_json()
# '{"occurred":"2024-01-15T10:30:00Z","duration":"3600s"}'
```

`ProtoTimestamp` accepts both `datetime` objects and ISO 8601 strings (with `Z` suffix) as
input, so you can parse directly from JSON payloads:

```python
Event.model_validate_json('{"occurred":"2024-01-15T10:30:00Z","duration":"3600s"}')
```

```python exec="on" session="api"
wkt = WellKnownTypes(
    wkt_timestamp=datetime.datetime(
        2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
    ),
    wkt_duration=datetime.timedelta(hours=1),
)
json_str = '{"wkt_timestamp":"2024-01-15T10:30:00Z","wkt_duration":"3600s"}'
assert wkt.model_dump_json() == json_str
parsed = WellKnownTypes.model_validate_json(json_str)
assert parsed.wkt_timestamp == datetime.datetime(
    2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
)
assert parsed.wkt_duration == datetime.timedelta(hours=1)
```
