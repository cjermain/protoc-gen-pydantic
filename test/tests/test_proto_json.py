"""Tests for proto-compatible JSON serialization via to/from_proto_json helpers.

Verifies that:
- to_proto_json/to_proto_dict omit proto3 default values
- Aliased fields use original proto names
- from_proto_dict/from_proto_json deserialize correctly
- Roundtrips preserve data
"""

import datetime
import json

from api.v1.collections_pydantic import Collections
from api.v1.enums_pydantic import Enum
from api.v1.known_types_pydantic import WellKnownTypes
from api.v1.messages_pydantic import Message
from api.v1.scalars_pydantic import Scalars

from conftest import make_scalars


def test_to_proto_json_omits_defaults():
    """to_proto_json omits fields with proto3 zero values."""
    m = Message()
    result = json.loads(m.to_proto_json())
    assert result == {}


def test_to_proto_dict_omits_defaults():
    """to_proto_dict omits fields with proto3 zero values."""
    m = Message()
    assert m.to_proto_dict() == {}


def test_to_proto_json_includes_non_defaults():
    """to_proto_json includes fields with non-default values."""
    m = Message(first_name="John")
    result = json.loads(m.to_proto_json())
    assert result == {"first_name": "John"}


def test_to_proto_dict_includes_non_defaults():
    m = Message(first_name="John", last_name="Doe")
    assert m.to_proto_dict() == {"first_name": "John", "last_name": "Doe"}


def test_to_proto_json_uses_alias():
    """to_proto_json uses aliases for fields with reserved names."""
    s = Scalars(bool_=True, float_=1.5, bytes_=b"hello")
    result = json.loads(s.to_proto_json())
    # Aliased fields should use the original proto name
    assert "bool" in result
    assert "float" in result
    assert "bytes" in result
    # Python attribute names should not appear
    assert "bool_" not in result
    assert "float_" not in result
    assert "bytes_" not in result


def test_to_proto_dict_uses_alias():
    s = Scalars(bool_=True)
    result = s.to_proto_dict()
    assert "bool" in result
    assert "bool_" not in result


def test_to_proto_json_empty_model():
    """A default-constructed model produces empty JSON."""
    s = Scalars()
    assert json.loads(s.to_proto_json()) == {}


def test_to_proto_json_scalars():
    """Scalar fields with non-zero values are included."""
    s = Scalars(int32=42, string="hello", double=3.14)
    result = json.loads(s.to_proto_json())
    assert result["int32"] == 42
    assert result["string"] == "hello"
    assert result["double"] == 3.14


def test_to_proto_json_nested_message():
    """Nested messages are serialized when set."""
    msg = Message(first_name="John", last_name="Doe")
    s = Scalars(message=msg)
    result = json.loads(s.to_proto_json())
    assert result["message"] == {"first_name": "John", "last_name": "Doe"}


def test_to_proto_json_repeated():
    """Non-empty repeated fields are included."""
    c = Collections(int32_repeated=[1, 2, 3])
    result = json.loads(c.to_proto_json())
    assert result["int32_repeated"] == [1, 2, 3]


def test_to_proto_json_enum():
    """Enum fields are included when set."""
    s = Scalars(enum=Enum.ACTIVE)
    result = json.loads(s.to_proto_json())
    assert result["enum"] == "ACTIVE"


def test_to_proto_json_override_exclude_defaults():
    """Callers can override exclude_defaults=False to include all fields."""
    m = Message()
    result = json.loads(m.to_proto_json(exclude_defaults=False))
    assert "first_name" in result
    assert result["first_name"] == ""


def test_to_proto_dict_override_by_alias():
    """Callers can override by_alias=False to get Python attribute names."""
    s = Scalars(bool_=True)
    result = s.to_proto_dict(by_alias=False)
    assert "bool_" in result
    assert "bool" not in result


def test_from_proto_dict():
    """from_proto_dict deserializes a dict into a model."""
    m = Message.from_proto_dict({"first_name": "John", "last_name": "Doe"})
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_from_proto_json():
    """from_proto_json deserializes a JSON string into a model."""
    m = Message.from_proto_json('{"first_name": "John", "last_name": "Doe"}')
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_from_proto_dict_roundtrip():
    """to_proto_dict → from_proto_dict roundtrip preserves data."""
    original = Message(first_name="John", last_name="Doe")
    restored = Message.from_proto_dict(original.to_proto_dict())
    assert restored == original


def test_from_proto_json_roundtrip():
    """to_proto_json → from_proto_json roundtrip preserves data."""
    original = Message(first_name="John", last_name="Doe")
    restored = Message.from_proto_json(original.to_proto_json())
    assert restored == original


# --- Expanded coverage: complex types ---


def test_to_proto_json_wkt_timestamp():
    """WKT timestamp serializes as RFC 3339 in proto JSON."""
    wkt = WellKnownTypes(
        wkt_timestamp=datetime.datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
        wkt_duration=datetime.timedelta(seconds=5),
    )
    result = json.loads(wkt.to_proto_json())
    assert result["wkt_timestamp"] == "2024-01-15T10:30:00Z"
    assert result["wkt_duration"] == "5s"


def test_to_proto_json_nested_message_in_collections():
    """Repeated messages serialize correctly in proto JSON."""
    c = Collections(
        message_repeated=[
            Message(first_name="John", last_name="Doe"),
            Message(first_name="Jane", last_name="Doe"),
        ]
    )
    result = json.loads(c.to_proto_json())
    assert len(result["message_repeated"]) == 2
    assert result["message_repeated"][0]["first_name"] == "John"


def test_to_proto_json_map_with_message_values():
    """Map fields with message values serialize correctly."""
    c = Collections(
        message_map_value={"user1": Message(first_name="John", last_name="Doe")}
    )
    result = json.loads(c.to_proto_json())
    assert result["message_map_value"]["user1"]["first_name"] == "John"


def test_to_proto_json_scalars_roundtrip():
    """Full roundtrip with Scalars message via proto JSON."""
    s = make_scalars()
    json_str = s.to_proto_json()
    restored = Scalars.from_proto_json(json_str)
    assert restored.int32 == s.int32
    assert restored.string == s.string
    assert restored.enum == s.enum


def test_to_proto_json_collections_roundtrip():
    """Full roundtrip with Collections message via proto JSON."""
    c = Collections(
        int32_repeated=[1, 2, 3],
        string_map_key={"a": "b"},
    )
    json_str = c.to_proto_json()
    restored = Collections.from_proto_json(json_str)
    assert restored.int32_repeated == [1, 2, 3]
    assert restored.string_map_key == {"a": "b"}
