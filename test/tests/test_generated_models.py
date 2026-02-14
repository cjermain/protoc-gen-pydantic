import datetime

import pytest
from pydantic import ValidationError

from gen.api.v1.test_pydantic import (
    Enum,
    Empty,
    Foo,
    Foo_NestedEnum,
    Foo_NestedMessage,
    Message,
    WellKnownTypes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def timestamp():
    return datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=datetime.timezone.utc)


@pytest.fixture
def message():
    return Message(firstName="John", lastName="Doe")


@pytest.fixture
def nested_message():
    return Foo_NestedMessage(firstName="Jane", lastName="Doe")


@pytest.fixture
def foo_kwargs(timestamp, message, nested_message):
    return dict(
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
        bool_=True,
        float_=1.5,
        double=2.5,
        string="hello",
        bytes_=b"world",
        enum=Enum.ACTIVE,
        nestedEnum=Foo_NestedEnum.ACTIVE,
        message=message,
        nestedMessage=nested_message,
        wktTimestamp=timestamp,
        # repeated
        int32Repeated=[1, 2],
        int64Repeated=[3, 4],
        uint32Repeated=[5],
        uint64Repeated=[6],
        fixed32Repeated=[7],
        fixed64Repeated=[8],
        sint32Repeated=[9],
        sint64Repeated=[10],
        sfixed32Repeated=[11],
        sfixed64Repeated=[12],
        boolRepeated=[True, False],
        floatRepeated=[1.0],
        doubleRepeated=[2.0],
        stringRepeated=["a"],
        bytesRepeated=[b"b"],
        enumRepeated=[Enum.INACTIVE],
        nestedEnumRepeated=[Foo_NestedEnum.INACTIVE],
        messageRepeated=[message],
        nestedMessageRepeated=[nested_message],
        wktTimestampRepeated=[timestamp],
        # maps – key types
        int32MapKey={1: "a"},
        int64MapKey={2: "b"},
        uint32MapKey={3: "c"},
        uint64MapKey={4: "d"},
        fixed32MapKey={5: "e"},
        fixed64MapKey={6: "f"},
        sint32MapKey={7: "g"},
        sint64MapKey={8: "h"},
        sfixed32MapKey={9: "i"},
        sfixed64MapKey={10: "j"},
        boolMapKey={True: "k"},
        stringMapKey={"key": "val"},
        # maps – value types
        int32MapValue={"a": 1},
        int64MapValue={"a": 2},
        uint32MapValue={"a": 3},
        uint64MapValue={"a": 4},
        fixed32MapValue={"a": 5},
        fixed64MapValue={"a": 6},
        sint32MapValue={"a": 7},
        sint64MapValue={"a": 8},
        sfixed32MapValue={"a": 9},
        sfixed64MapValue={"a": 10},
        boolMapValue={"a": True},
        floatMapValue={"a": 1.0},
        doubleMapValue={"a": 2.0},
        stringMapValue={"a": "b"},
        bytesMapValue={"a": b"c"},
        enumMapValue={"a": Enum.ACTIVE},
        nestedEnumMapValue={"a": Foo_NestedEnum.ACTIVE},
        messageMapValue={"a": message},
        nestedMessageMapValue={"a": nested_message},
        wktTimestampMapValue={"a": timestamp},
    )


@pytest.fixture
def foo(foo_kwargs):
    return Foo(**foo_kwargs)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "enum_cls,expected",
    [
        (Enum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
        (Foo_NestedEnum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
    ],
)
def test_enum_values(enum_cls, expected):
    assert [m.value for m in enum_cls] == expected


@pytest.mark.parametrize("enum_cls", [Enum, Foo_NestedEnum])
def test_enum_is_str(enum_cls):
    for member in enum_cls:
        assert isinstance(member, str)


# ---------------------------------------------------------------------------
# Simple models
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Foo – required scalars
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Foo – alias fields (builtin shadowing)
# ---------------------------------------------------------------------------


def test_foo_alias_construction_by_alias(timestamp, message, nested_message):
    """Fields with aliases can be constructed using the original proto name."""
    foo = Foo(
        int32=1, int64=2, uint32=3, uint64=4,
        fixed32=5, fixed64=6, sint32=7, sint64=8,
        sfixed32=9, sfixed64=10,
        double=2.5, string="hello",
        enum=Enum.ACTIVE, nestedEnum=Foo_NestedEnum.ACTIVE,
        message=message, nestedMessage=nested_message,
        wktTimestamp=timestamp,
        # Use alias names (original proto names) instead of Python attr names
        **{"bool": True, "float": 1.5, "bytes": b"world"},
        int32Repeated=[], int64Repeated=[], uint32Repeated=[], uint64Repeated=[],
        fixed32Repeated=[], fixed64Repeated=[], sint32Repeated=[], sint64Repeated=[],
        sfixed32Repeated=[], sfixed64Repeated=[], boolRepeated=[], floatRepeated=[],
        doubleRepeated=[], stringRepeated=[], bytesRepeated=[],
        enumRepeated=[], nestedEnumRepeated=[], messageRepeated=[],
        nestedMessageRepeated=[], wktTimestampRepeated=[],
        int32MapKey={}, int64MapKey={}, uint32MapKey={}, uint64MapKey={},
        fixed32MapKey={}, fixed64MapKey={}, sint32MapKey={}, sint64MapKey={},
        sfixed32MapKey={}, sfixed64MapKey={}, boolMapKey={}, stringMapKey={},
        int32MapValue={}, int64MapValue={}, uint32MapValue={}, uint64MapValue={},
        fixed32MapValue={}, fixed64MapValue={}, sint32MapValue={}, sint64MapValue={},
        sfixed32MapValue={}, sfixed64MapValue={}, boolMapValue={}, floatMapValue={},
        doubleMapValue={}, stringMapValue={}, bytesMapValue={},
        enumMapValue={}, nestedEnumMapValue={}, messageMapValue={},
        nestedMessageMapValue={}, wktTimestampMapValue={},
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


# ---------------------------------------------------------------------------
# Foo – optional fields
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Foo – repeated fields
# ---------------------------------------------------------------------------


def test_foo_repeated_fields(foo):
    assert foo.int32Repeated == [1, 2]
    assert foo.stringRepeated == ["a"]
    assert foo.boolRepeated == [True, False]
    assert foo.messageRepeated[0].firstName == "John"
    assert foo.nestedMessageRepeated[0].firstName == "Jane"


# ---------------------------------------------------------------------------
# Foo – map fields
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Foo – oneof
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Foo – validation & roundtrip
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# WellKnownTypes
# ---------------------------------------------------------------------------


@pytest.fixture
def wkt():
    return WellKnownTypes(
        wktTimestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        wktDuration=datetime.timedelta(seconds=30),
        wktStruct={"key": "value", "nested": {"a": 1}},
        wktValue="hello",
        wktListValue=[1, "two", True],
        wktAny={"type": "test"},
        wktFieldMask=["field1", "field2"],
        wktBool=True,
        wktInt32=42,
        wktInt64=9999999999,
        wktUint32=100,
        wktUint64=200,
        wktFloat=3.14,
        wktDouble=2.718,
        wktString="test",
        wktBytes=b"binary",
        wktEmpty=None,
    )


def test_wkt_timestamp(wkt):
    assert isinstance(wkt.wktTimestamp, datetime.datetime)
    assert wkt.wktTimestamp.year == 2024


def test_wkt_duration(wkt):
    assert isinstance(wkt.wktDuration, datetime.timedelta)
    assert wkt.wktDuration.total_seconds() == 30


def test_wkt_struct(wkt):
    assert isinstance(wkt.wktStruct, dict)
    assert wkt.wktStruct["key"] == "value"


def test_wkt_value(wkt):
    assert wkt.wktValue == "hello"


def test_wkt_list_value(wkt):
    assert isinstance(wkt.wktListValue, list)
    assert wkt.wktListValue == [1, "two", True]


def test_wkt_field_mask(wkt):
    assert wkt.wktFieldMask == ["field1", "field2"]


def test_wkt_wrapper_types(wkt):
    assert wkt.wktBool is True
    assert wkt.wktInt32 == 42
    assert wkt.wktInt64 == 9999999999
    assert wkt.wktUint32 == 100
    assert wkt.wktUint64 == 200
    assert wkt.wktFloat == pytest.approx(3.14)
    assert wkt.wktDouble == pytest.approx(2.718)
    assert wkt.wktString == "test"
    assert wkt.wktBytes == b"binary"


def test_wkt_empty(wkt):
    assert wkt.wktEmpty is None


def test_wkt_json_roundtrip(wkt):
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wktTimestamp == wkt.wktTimestamp
    assert wkt2.wktDuration == wkt.wktDuration
    assert wkt2.wktStruct == wkt.wktStruct
    assert wkt2.wktBool is True
    assert wkt2.wktString == "test"
