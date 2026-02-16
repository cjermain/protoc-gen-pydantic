import pytest

from api.v1.enums_pydantic import Enum
from api.v1.types_pydantic import Empty, Foo, Foo_NestedEnum, Foo_NestedMessage, Message


def test_empty_model():
    e = Empty()
    assert e is not None
    assert len(Empty.model_fields) == 0


def test_message_valid():
    m = Message(first_name="John", last_name="Doe")
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_message_zero_value_defaults():
    """Proto3 messages can be constructed with no arguments; fields take zero values."""
    m = Message()
    assert m.first_name == ""
    assert m.last_name == ""


def test_message_field_descriptions():
    assert Message.model_fields["first_name"].description is not None


def test_nested_message_valid():
    m = Foo_NestedMessage(first_name="Jane", last_name="Doe")
    assert m.first_name == "Jane"


def test_nested_message_zero_value_defaults():
    """Nested messages also support proto3 zero-value defaults."""
    m = Foo_NestedMessage()
    assert m.first_name == ""
    assert m.last_name == ""


def test_foo_required_scalars(foo):
    assert foo.int32 == 1
    assert foo.int64 == 2
    assert foo.uint32 == 3
    assert foo.string == "hello"
    assert foo.bytes_ == b"world"
    assert foo.bool_ is True
    assert foo.float_ == 1.5
    assert foo.double == 2.5
    assert foo.enum == Enum.ACTIVE
    assert foo.nested_enum == Foo_NestedEnum.ACTIVE
    assert foo.message.first_name == "John"
    assert foo.nested_message.first_name == "Jane"


def test_foo_alias_construction_by_alias(timestamp, message, nested_message):
    """Fields with aliases can be constructed using the original proto name."""
    foo = Foo(
        int32=1,
        int64=2,
        uint32=3,
        uint64=4,
        fixed32=5,
        fixed64=6,
        sint32=7,
        sint64=8,
        sfixed32=9,
        sfixed64=10,
        double=2.5,
        string="hello",
        enum=Enum.ACTIVE,
        nested_enum=Foo_NestedEnum.ACTIVE,
        message=message,
        nested_message=nested_message,
        wkt_timestamp=timestamp,
        # Use alias names (original proto names) instead of Python attr names
        **{"bool": True, "float": 1.5, "bytes": b"world"},
        int32_repeated=[],
        int64_repeated=[],
        uint32_repeated=[],
        uint64_repeated=[],
        fixed32_repeated=[],
        fixed64_repeated=[],
        sint32_repeated=[],
        sint64_repeated=[],
        sfixed32_repeated=[],
        sfixed64_repeated=[],
        bool_repeated=[],
        float_repeated=[],
        double_repeated=[],
        string_repeated=[],
        bytes_repeated=[],
        enum_repeated=[],
        nested_enum_repeated=[],
        message_repeated=[],
        nested_message_repeated=[],
        wkt_timestamp_repeated=[],
        int32_map_key={},
        int64_map_key={},
        uint32_map_key={},
        uint64_map_key={},
        fixed32_map_key={},
        fixed64_map_key={},
        sint32_map_key={},
        sint64_map_key={},
        sfixed32_map_key={},
        sfixed64_map_key={},
        bool_map_key={},
        string_map_key={},
        int32_map_value={},
        int64_map_value={},
        uint32_map_value={},
        uint64_map_value={},
        fixed32_map_value={},
        fixed64_map_value={},
        sint32_map_value={},
        sint64_map_value={},
        sfixed32_map_value={},
        sfixed64_map_value={},
        bool_map_value={},
        float_map_value={},
        double_map_value={},
        string_map_value={},
        bytes_map_value={},
        enum_map_value={},
        nested_enum_map_value={},
        message_map_value={},
        nested_message_map_value={},
        wkt_timestamp_map_value={},
    )
    assert foo.bool_ is True
    assert foo.float_ == 1.5
    assert foo.bytes_ == b"world"


def test_foo_alias_in_dict_output(foo):
    """Dict serialization uses the alias (original proto name) by default."""
    data = foo.model_dump(by_alias=True)
    assert "bool" in data
    assert "float" in data
    assert "bytes" in data
    assert "bool_" not in data
    assert "float_" not in data
    assert "bytes_" not in data


OPTIONAL_FIELDS = [
    "int32_optional",
    "int64_optional",
    "uint32_optional",
    "uint64_optional",
    "fixed32_optional",
    "fixed64_optional",
    "sint32_optional",
    "sint64_optional",
    "sfixed32_optional",
    "sfixed64_optional",
    "bool_optional",
    "float_optional",
    "double_optional",
    "string_optional",
    "bytes_optional",
    "enum_optional",
    "nested_enum_optional",
    "message_optional",
    "nested_message_optional",
    "wkt_timestamp_optional",
]


@pytest.mark.parametrize("field", OPTIONAL_FIELDS)
def test_foo_optional_defaults_none(foo, field):
    assert getattr(foo, field) is None


def test_foo_optional_set(foo_kwargs, message):
    foo_kwargs["int32_optional"] = 42
    foo_kwargs["string_optional"] = "opt"
    foo_kwargs["enum_optional"] = Enum.INACTIVE
    foo_kwargs["message_optional"] = message
    foo = Foo(**foo_kwargs)
    assert foo.int32_optional == 42
    assert foo.string_optional == "opt"
    assert foo.enum_optional == Enum.INACTIVE
    assert foo.message_optional.first_name == "John"


def test_foo_repeated_fields(foo):
    assert foo.int32_repeated == [1, 2]
    assert foo.string_repeated == ["a"]
    assert foo.bool_repeated == [True, False]
    assert foo.message_repeated[0].first_name == "John"
    assert foo.nested_message_repeated[0].first_name == "Jane"


def test_foo_map_key_types(foo):
    assert foo.int32_map_key[1] == "a"
    assert foo.string_map_key["key"] == "val"
    assert foo.bool_map_key[True] == "k"


def test_foo_map_value_types(foo):
    assert foo.int32_map_value["a"] == 1
    assert foo.bool_map_value["a"] is True
    assert foo.float_map_value["a"] == 1.0
    assert foo.enum_map_value["a"] == Enum.ACTIVE
    assert foo.message_map_value["a"].first_name == "John"
    assert foo.bytes_map_value["a"] == b"c"


def test_foo_oneof_default_none(foo):
    assert foo.a is None
    assert foo.b is None


def test_foo_oneof_set_a(foo_kwargs):
    foo_kwargs["a"] = 99
    foo = Foo(**foo_kwargs)
    assert foo.a == 99


def test_foo_oneof_set_b(foo_kwargs):
    foo_kwargs["b"] = "test"
    foo = Foo(**foo_kwargs)
    assert foo.b == "test"


def test_foo_zero_value_defaults():
    """Foo() with no arguments should succeed with proto3 zero values."""
    foo = Foo()
    assert foo.int32 == 0
    assert foo.int64 == 0
    assert foo.uint32 == 0
    assert foo.string == ""
    assert foo.bytes_ == b""
    assert foo.bool_ is False
    assert foo.float_ == 0.0
    assert foo.double == 0.0
    assert foo.enum is None
    assert foo.message is None
    assert foo.nested_message is None
    assert foo.wkt_timestamp is None
    assert foo.int32_repeated == []
    assert foo.int32_map_key == {}
    assert foo.a is None
    assert foo.b is None


def test_foo_json_roundtrip(foo):
    json_str = foo.model_dump_json()
    foo2 = Foo.model_validate_json(json_str)
    assert foo2.int32 == foo.int32
    assert foo2.string == foo.string
    assert foo2.enum == foo.enum
    assert foo2.wkt_timestamp == foo.wkt_timestamp


def test_foo_dict_roundtrip(foo):
    d = foo.model_dump()
    foo2 = Foo.model_validate(d)
    assert foo2.message.first_name == "John"
    assert foo2.nested_message.first_name == "Jane"


def test_message_json_roundtrip(message):
    json_str = message.model_dump_json()
    m2 = Message.model_validate_json(json_str)
    assert m2.first_name == message.first_name
    assert m2.last_name == message.last_name
