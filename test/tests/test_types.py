import pytest
from pydantic import ValidationError

from api.v1.enums_pydantic import Enum
from api.v1.types_pydantic import Empty, Foo, Foo_NestedEnum, Foo_NestedMessage, Message


def test_empty_model():
    e = Empty()
    assert e is not None
    assert len(Empty.model_fields) == 0


def test_message_valid():
    m = Message(firstName="John", lastName="Doe")
    assert m.firstName == "John"
    assert m.lastName == "Doe"


def test_message_missing_field():
    with pytest.raises(ValidationError):
        Message(firstName="John")


def test_message_field_descriptions():
    assert Message.model_fields["firstName"].description is not None


def test_nested_message_valid():
    m = Foo_NestedMessage(firstName="Jane", lastName="Doe")
    assert m.firstName == "Jane"


def test_nested_message_missing_field():
    with pytest.raises(ValidationError):
        Foo_NestedMessage(lastName="Doe")


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
    assert foo.nestedEnum == Foo_NestedEnum.ACTIVE
    assert foo.message.firstName == "John"
    assert foo.nestedMessage.firstName == "Jane"


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
        nestedEnum=Foo_NestedEnum.ACTIVE,
        message=message,
        nestedMessage=nested_message,
        wktTimestamp=timestamp,
        # Use alias names (original proto names) instead of Python attr names
        **{"bool": True, "float": 1.5, "bytes": b"world"},
        int32Repeated=[],
        int64Repeated=[],
        uint32Repeated=[],
        uint64Repeated=[],
        fixed32Repeated=[],
        fixed64Repeated=[],
        sint32Repeated=[],
        sint64Repeated=[],
        sfixed32Repeated=[],
        sfixed64Repeated=[],
        boolRepeated=[],
        floatRepeated=[],
        doubleRepeated=[],
        stringRepeated=[],
        bytesRepeated=[],
        enumRepeated=[],
        nestedEnumRepeated=[],
        messageRepeated=[],
        nestedMessageRepeated=[],
        wktTimestampRepeated=[],
        int32MapKey={},
        int64MapKey={},
        uint32MapKey={},
        uint64MapKey={},
        fixed32MapKey={},
        fixed64MapKey={},
        sint32MapKey={},
        sint64MapKey={},
        sfixed32MapKey={},
        sfixed64MapKey={},
        boolMapKey={},
        stringMapKey={},
        int32MapValue={},
        int64MapValue={},
        uint32MapValue={},
        uint64MapValue={},
        fixed32MapValue={},
        fixed64MapValue={},
        sint32MapValue={},
        sint64MapValue={},
        sfixed32MapValue={},
        sfixed64MapValue={},
        boolMapValue={},
        floatMapValue={},
        doubleMapValue={},
        stringMapValue={},
        bytesMapValue={},
        enumMapValue={},
        nestedEnumMapValue={},
        messageMapValue={},
        nestedMessageMapValue={},
        wktTimestampMapValue={},
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
    "int32Optional",
    "int64Optional",
    "uint32Optional",
    "uint64Optional",
    "fixed32Optional",
    "fixed64Optional",
    "sint32Optional",
    "sint64Optional",
    "sfixed32Optional",
    "sfixed64Optional",
    "boolOptional",
    "floatOptional",
    "doubleOptional",
    "stringOptional",
    "bytesOptional",
    "enumOptional",
    "nestedEnumOptional",
    "messageOptional",
    "nestedMessageOptional",
    "wktTimestampOptional",
]


@pytest.mark.parametrize("field", OPTIONAL_FIELDS)
def test_foo_optional_defaults_none(foo, field):
    assert getattr(foo, field) is None


def test_foo_optional_set(foo_kwargs, message):
    foo_kwargs["int32Optional"] = 42
    foo_kwargs["stringOptional"] = "opt"
    foo_kwargs["enumOptional"] = Enum.INACTIVE
    foo_kwargs["messageOptional"] = message
    foo = Foo(**foo_kwargs)
    assert foo.int32Optional == 42
    assert foo.stringOptional == "opt"
    assert foo.enumOptional == Enum.INACTIVE
    assert foo.messageOptional.firstName == "John"


def test_foo_repeated_fields(foo):
    assert foo.int32Repeated == [1, 2]
    assert foo.stringRepeated == ["a"]
    assert foo.boolRepeated == [True, False]
    assert foo.messageRepeated[0].firstName == "John"
    assert foo.nestedMessageRepeated[0].firstName == "Jane"


def test_foo_map_key_types(foo):
    assert foo.int32MapKey[1] == "a"
    assert foo.stringMapKey["key"] == "val"
    assert foo.boolMapKey[True] == "k"


def test_foo_map_value_types(foo):
    assert foo.int32MapValue["a"] == 1
    assert foo.boolMapValue["a"] is True
    assert foo.floatMapValue["a"] == 1.0
    assert foo.enumMapValue["a"] == Enum.ACTIVE
    assert foo.messageMapValue["a"].firstName == "John"
    assert foo.bytesMapValue["a"] == b"c"


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


def test_foo_missing_required_raises():
    with pytest.raises(ValidationError):
        Foo(int32=1)


def test_foo_json_roundtrip(foo):
    json_str = foo.model_dump_json()
    foo2 = Foo.model_validate_json(json_str)
    assert foo2.int32 == foo.int32
    assert foo2.string == foo.string
    assert foo2.enum == foo.enum
    assert foo2.wktTimestamp == foo.wktTimestamp


def test_foo_dict_roundtrip(foo):
    d = foo.model_dump()
    foo2 = Foo.model_validate(d)
    assert foo2.message.firstName == "John"
    assert foo2.nestedMessage.firstName == "Jane"


def test_message_json_roundtrip(message):
    json_str = message.model_dump_json()
    m2 = Message.model_validate_json(json_str)
    assert m2.firstName == message.firstName
    assert m2.lastName == message.lastName
