---
icon: lucide/star
---

# Well-Known Types

Google's Protocol Buffers ships with a set of "well-known types" (WKTs) for common value
shapes. `protoc-gen-pydantic` maps them to the most natural Python equivalents instead of
wrapping raw `_pb2` objects.

```python exec="on" session="wkt"
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.known_types_pydantic import Event, WellKnownTypes
```

## Type mappings

| Protobuf WKT | Python type | Notes |
|---|---|---|
| `google.protobuf.Timestamp` | `datetime.datetime` | UTC; use `datetime.now(timezone.utc)` |
| `google.protobuf.Duration` | `datetime.timedelta` | |
| `google.protobuf.Struct` | `dict[str, Any]` | Arbitrary JSON object |
| `google.protobuf.Value` | `Any` | Any JSON value |
| `google.protobuf.ListValue` | `list[Any]` | JSON array |
| `google.protobuf.Empty` | `None` | Unit type; field defaults to `None` |
| `google.protobuf.FieldMask` | `list[str]` | List of field path strings |
| `google.protobuf.Any` | `Any` | Arbitrary serialized message |
| `google.protobuf.BoolValue` | `bool \| None` | Nullable bool wrapper |
| `google.protobuf.Int32Value` | `int \| None` | Nullable int32 wrapper |
| `google.protobuf.Int64Value` | `ProtoInt64 \| None` | Nullable int64 wrapper |
| `google.protobuf.UInt32Value` | `int \| None` | Nullable uint32 wrapper |
| `google.protobuf.UInt64Value` | `ProtoUInt64 \| None` | Nullable uint64 wrapper |
| `google.protobuf.FloatValue` | `float \| None` | Nullable float wrapper |
| `google.protobuf.DoubleValue` | `float \| None` | Nullable double wrapper |
| `google.protobuf.StringValue` | `str \| None` | Nullable string wrapper |
| `google.protobuf.BytesValue` | `bytes \| None` | Nullable bytes wrapper |

## Example

=== ":lucide-file-code: known_types.proto"

    ```proto
    message Event {
      string                     id          = 1;
      google.protobuf.Timestamp  occurred    = 2;
      google.protobuf.Duration   duration    = 3;
      google.protobuf.Struct     metadata    = 4;
      google.protobuf.FieldMask  update_mask = 5;
      google.protobuf.Int32Value retry_count = 6;
    }
    ```

=== ":simple-python: known_types_pydantic.py"

    ```python exec="on" session="wkt"
    import inspect

    print(f"```python\n{inspect.getsource(Event).rstrip()}\n```")
    ```

```python exec="on" session="wkt"
event = Event(id_="evt-1")
assert event.id_ == "evt-1"
assert event.occurred is None
assert event.retry_count is None

event2 = Event(id_="evt-2", retry_count=0)
assert event2.retry_count == 0
```

## Timestamp and Duration

`ProtoTimestamp` and `ProtoDuration` are type aliases for `datetime.datetime` and
`datetime.timedelta` respectively. They are defined in the generated `_proto_types.py`
alongside format validators.

```python
import datetime

from known_types_pydantic import Event

event = Event(
    id_="evt-123",
    occurred=datetime.datetime.now(datetime.timezone.utc),
    duration=datetime.timedelta(seconds=5),
)
```

```python exec="on" session="wkt"
wkt = WellKnownTypes(
    wkt_timestamp=datetime.datetime(
        2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
    ),
    wkt_duration=datetime.timedelta(hours=1),
)
json_str = '{"wktTimestamp":"2024-01-15T10:30:00Z","wktDuration":"3600s"}'
assert wkt.model_dump_json() == json_str
parsed = WellKnownTypes.model_validate_json(json_str)
assert parsed.wkt_timestamp == datetime.datetime(
    2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
)
assert parsed.wkt_duration == datetime.timedelta(hours=1)
```

## Struct and Value

`google.protobuf.Struct` maps to `dict[str, Any]`, so you can pass arbitrary dictionaries:

```python
event = Event(
    metadata={"source": "sensor-42", "readings": [1.1, 2.2, 3.3]},
)
```

```python exec="on" session="wkt"
event = Event(metadata={"source": "sensor-42", "readings": [1.1, 2.2, 3.3]})
assert event.metadata["source"] == "sensor-42"
```

## Wrapper types

Wrapper types (`BoolValue`, `Int32Value`, etc.) exist in proto to distinguish "field not set"
from the zero value. They map to their underlying Python type with `| None`:

```python
# retry_count is None → "not set"
event = Event(id_="evt-1")
assert event.retry_count is None

# retry_count is 0 → explicitly set to zero
event = Event(id_="evt-2", retry_count=0)
assert event.retry_count == 0
```
