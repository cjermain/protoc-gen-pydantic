"""Cross-library round-trip tests between Pydantic models and protobuf library.

Verifies that:
- JSON produced by protobuf library can be parsed by Pydantic models
- Proto-compatible JSON from Pydantic can be parsed by protobuf library
- Full roundtrip preserves data
"""

import datetime
import json
import sys
from pathlib import Path

# Extend the api.v1 namespace to include gen_pb2/ so pb2 modules are importable
# alongside pydantic modules from gen/.
_gen_pb2_path = str(Path(__file__).resolve().parent.parent / "gen_pb2")
if _gen_pb2_path not in sys.path:
    sys.path.insert(0, _gen_pb2_path)

import api  # noqa: E402
import api.v1  # noqa: E402

api.__path__.append(str(Path(_gen_pb2_path) / "api"))
api.v1.__path__.append(str(Path(_gen_pb2_path) / "api" / "v1"))

from api.v1.known_types_pb2 import WellKnownTypes as ProtoWKT  # noqa: E402
from api.v1.types_pb2 import Message as ProtoMessage  # noqa: E402
from google.protobuf import wrappers_pb2  # noqa: E402
from google.protobuf.duration_pb2 import Duration  # noqa: E402
from google.protobuf.json_format import MessageToJson, Parse  # noqa: E402
from google.protobuf.timestamp_pb2 import Timestamp  # noqa: E402

from api.v1.types_pydantic import Message as PydanticMessage  # noqa: E402


# --- Protobuf → Pydantic (via JSON format strings) ---


def test_protobuf_json_parseable_by_pydantic_message():
    """Parse JSON from protobuf library into Pydantic model."""
    proto_msg = ProtoMessage()
    proto_msg.first_name = "John"
    proto_msg.last_name = "Doe"
    json_str = MessageToJson(proto_msg)
    pydantic_msg = PydanticMessage.model_validate_json(json_str)
    assert pydantic_msg.firstName == "John"
    assert pydantic_msg.lastName == "Doe"


def test_protobuf_timestamp_format_parseable_by_pydantic():
    """Protobuf's RFC 3339 timestamp format is accepted by Pydantic."""
    proto_wkt = ProtoWKT()
    proto_wkt.wkt_timestamp.CopyFrom(Timestamp(seconds=1705314600))
    json_str = MessageToJson(proto_wkt)
    # Extract the timestamp value protobuf produced
    data = json.loads(json_str)
    ts_str = data["wktTimestamp"]
    assert "2024" in ts_str
    # Verify our Pydantic type can parse this format
    from api.v1._proto_types import ProtoTimestamp
    from pydantic import TypeAdapter

    adapter = TypeAdapter(ProtoTimestamp)
    parsed = adapter.validate_python(ts_str)
    assert isinstance(parsed, datetime.datetime)
    assert parsed.year == 2024


def test_protobuf_duration_format_parseable_by_pydantic():
    """Protobuf's duration string format is accepted by Pydantic."""
    proto_wkt = ProtoWKT()
    proto_wkt.wkt_duration.CopyFrom(Duration(seconds=3, nanos=500000000))
    json_str = MessageToJson(proto_wkt)
    data = json.loads(json_str)
    dur_str = data["wktDuration"]
    from api.v1._proto_types import ProtoDuration
    from pydantic import TypeAdapter

    adapter = TypeAdapter(ProtoDuration)
    parsed = adapter.validate_python(dur_str)
    assert parsed == datetime.timedelta(seconds=3, milliseconds=500)


def test_protobuf_int64_wrapper_format_parseable_by_pydantic():
    """Protobuf's string-encoded int64 wrapper is accepted by Pydantic."""
    proto_wkt = ProtoWKT()
    proto_wkt.wkt_int64.CopyFrom(wrappers_pb2.Int64Value(value=9007199254740993))
    json_str = MessageToJson(proto_wkt)
    data = json.loads(json_str)
    # protobuf serializes int64 wrappers as strings
    assert data["wktInt64"] == "9007199254740993"
    from api.v1._proto_types import ProtoInt64
    from pydantic import TypeAdapter

    adapter = TypeAdapter(ProtoInt64)
    parsed = adapter.validate_python("9007199254740993")
    assert parsed == 9007199254740993


# --- Pydantic → Protobuf ---


def test_pydantic_json_dict_parseable_by_protobuf():
    """Proto-compatible dict from Pydantic can be parsed by protobuf."""
    pydantic_msg = PydanticMessage(firstName="John", lastName="Doe")
    data = pydantic_msg.model_dump(mode="json")
    json_str = json.dumps(data)
    proto_msg = Parse(json_str, ProtoMessage())
    assert proto_msg.first_name == "John"
    assert proto_msg.last_name == "Doe"


def test_pydantic_timestamp_json_parseable_by_protobuf():
    """Pydantic RFC 3339 timestamp can be parsed by protobuf."""
    data = {"wktTimestamp": "2024-01-15T10:30:00Z"}
    json_str = json.dumps(data)
    proto_wkt = Parse(json_str, ProtoWKT())
    assert proto_wkt.wkt_timestamp.seconds == 1705314600


def test_pydantic_duration_json_parseable_by_protobuf():
    """Pydantic duration string can be parsed by protobuf."""
    data = {"wktDuration": "3.5s"}
    json_str = json.dumps(data)
    proto_wkt = Parse(json_str, ProtoWKT())
    assert proto_wkt.wkt_duration.seconds == 3
    assert proto_wkt.wkt_duration.nanos == 500000000


def test_pydantic_int64_wrapper_json_parseable_by_protobuf():
    """Pydantic int64 wrapper string values can be parsed by protobuf."""
    data = {"wktInt64": "9007199254740993", "wktUint64": "9007199254740993"}
    json_str = json.dumps(data)
    proto_wkt = Parse(json_str, ProtoWKT())
    assert proto_wkt.wkt_int64.value == 9007199254740993
    assert proto_wkt.wkt_uint64.value == 9007199254740993


# --- Full roundtrip ---


def test_message_pydantic_to_protobuf_roundtrip():
    """Pydantic → JSON → protobuf → JSON → Pydantic roundtrip."""
    pydantic_msg = PydanticMessage(firstName="John", lastName="Doe")
    json_str = pydantic_msg.model_dump_json()
    proto_msg = Parse(json_str, ProtoMessage())
    assert proto_msg.first_name == "John"
    json_str2 = MessageToJson(proto_msg)
    pydantic_msg2 = PydanticMessage.model_validate_json(json_str2)
    assert pydantic_msg2.firstName == "John"
    assert pydantic_msg2.lastName == "Doe"
