---
icon: lucide/star
---

# Well-Known Types

Google's Protocol Buffers ships with a set of "well-known types" (WKTs) for common value
shapes. `protoc-gen-pydantic` maps them to the most natural Python equivalents instead of
wrapping raw `_pb2` objects.

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

=== ":lucide-file-code: event.proto"

    ```proto
    syntax = "proto3";

    import "google/protobuf/duration.proto";
    import "google/protobuf/field_mask.proto";
    import "google/protobuf/struct.proto";
    import "google/protobuf/timestamp.proto";
    import "google/protobuf/wrappers.proto";

    message Event {
      string                    id          = 1;
      google.protobuf.Timestamp occurred    = 2;
      google.protobuf.Duration  duration    = 3;
      google.protobuf.Struct    metadata    = 4;
      google.protobuf.FieldMask update_mask = 5;
      google.protobuf.Int32Value retry_count = 6;
    }
    ```

=== ":simple-python: event_pydantic.py"

    ```python
    from typing import Any as _Any

    from pydantic import Field as _Field

    from ._proto_types import ProtoDuration, ProtoTimestamp


    class Event(_ProtoModel):
        id: "str" = _Field("")
        occurred: "ProtoTimestamp | None" = _Field(None)
        duration: "ProtoDuration | None" = _Field(None)
        metadata: "dict[str, _Any] | None" = _Field(None)
        update_mask: "list[str] | None" = _Field(None)
        retry_count: "int | None" = _Field(None)
    ```

## Timestamp and Duration

`ProtoTimestamp` and `ProtoDuration` are type aliases for `datetime.datetime` and
`datetime.timedelta` respectively. They are defined in the generated `_proto_types.py`
alongside format validators.

```python
import datetime

from gen.event_pydantic import Event

event = Event(
    id="evt-123",
    occurred=datetime.datetime.now(datetime.timezone.utc),
    duration=datetime.timedelta(seconds=5),
)
```

## Struct and Value

`google.protobuf.Struct` maps to `dict[str, Any]`, so you can pass arbitrary dictionaries:

```python
event = Event(
    metadata={"source": "sensor-42", "readings": [1.1, 2.2, 3.3]},
)
```

## Wrapper types

Wrapper types (`BoolValue`, `Int32Value`, etc.) exist in proto to distinguish "field not set"
from the zero value. They map to their underlying Python type with `| None`:

```python
# retry_count is None → "not set"
event = Event(id="evt-1")
assert event.retry_count is None

# retry_count is 0 → explicitly set to zero
event = Event(id="evt-2", retry_count=0)
assert event.retry_count == 0
```
