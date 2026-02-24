import pytest

from api.v1.enums_pydantic import Enum
from api.v1.scalars_pydantic import Scalars

from conftest import make_scalars


def test_required_scalars():
    s = make_scalars()
    assert s.int32 == 1
    assert s.int64 == 2
    assert s.uint32 == 3
    assert s.string == "hello"
    assert s.bytes_ == b"world"
    assert s.bool_ is True
    assert s.float_ == 1.5
    assert s.double == 2.5
    assert s.enum == Enum.ACTIVE
    assert s.nested_enum == Scalars.NestedEnum.ACTIVE
    assert s.message.first_name == "John"
    assert s.nested_message.first_name == "Jane"


def test_zero_value_defaults():
    """Scalars() with no arguments should succeed with proto3 zero values."""
    s = Scalars()
    assert s.int32 == 0
    assert s.int64 == 0
    assert s.uint32 == 0
    assert s.string == ""
    assert s.bytes_ == b""
    assert s.bool_ is False
    assert s.float_ == 0.0
    assert s.double == 0.0
    assert s.enum is None
    assert s.message is None
    assert s.nested_message is None


def test_alias_construction_by_alias(message, nested_message):
    """Fields with aliases can be constructed using the original proto name."""
    s = Scalars(
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
        nested_enum=Scalars.NestedEnum.ACTIVE,
        message=message,
        nested_message=nested_message,
        # Use alias names (original proto names) instead of Python attr names
        **{"bool": True, "float": 1.5, "bytes": b"world"},
    )
    assert s.bool_ is True
    assert s.float_ == 1.5
    assert s.bytes_ == b"world"


def test_alias_in_dict_output():
    """Dict serialization uses the alias (original proto name) by default."""
    s = make_scalars()
    data = s.model_dump(by_alias=True)
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
]


@pytest.mark.parametrize("field", OPTIONAL_FIELDS)
def test_optional_defaults_none(field):
    s = make_scalars()
    assert getattr(s, field) is None


def test_optional_set(message):
    s = make_scalars(
        int32_optional=42,
        string_optional="opt",
        enum_optional=Enum.INACTIVE,
        message_optional=message,
    )
    assert s.int32_optional == 42
    assert s.string_optional == "opt"
    assert s.enum_optional == Enum.INACTIVE
    assert s.message_optional.first_name == "John"


def test_nested_message_valid():
    m = Scalars.NestedMessage(first_name="Jane", last_name="Doe")
    assert m.first_name == "Jane"


def test_nested_message_zero_value_defaults():
    """Nested messages also support proto3 zero-value defaults."""
    m = Scalars.NestedMessage()
    assert m.first_name == ""
    assert m.last_name == ""


def test_json_roundtrip():
    s = make_scalars()
    json_str = s.model_dump_json()
    s2 = Scalars.model_validate_json(json_str)
    assert s2.int32 == s.int32
    assert s2.string == s.string
    assert s2.enum == s.enum


def test_dict_roundtrip():
    s = make_scalars()
    d = s.model_dump()
    s2 = Scalars.model_validate(d)
    assert s2.message.first_name == "John"
    assert s2.nested_message.first_name == "Jane"
