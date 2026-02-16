import json

from api.v1.enums_pydantic import Enum
from api.v1.types_pydantic import Foo, Message


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
    foo = Foo(bool_=True, float_=1.5, bytes_=b"hello")
    result = json.loads(foo.to_proto_json())
    # Aliased fields should use the original proto name
    assert "bool" in result
    assert "float" in result
    assert "bytes" in result
    # Python attribute names should not appear
    assert "bool_" not in result
    assert "float_" not in result
    assert "bytes_" not in result


def test_to_proto_dict_uses_alias():
    foo = Foo(bool_=True)
    result = foo.to_proto_dict()
    assert "bool" in result
    assert "bool_" not in result


def test_to_proto_json_empty_model():
    """A default-constructed model produces empty JSON."""
    foo = Foo()
    assert json.loads(foo.to_proto_json()) == {}


def test_to_proto_json_scalars():
    """Scalar fields with non-zero values are included."""
    foo = Foo(int32=42, string="hello", double=3.14)
    result = json.loads(foo.to_proto_json())
    assert result["int32"] == 42
    assert result["string"] == "hello"
    assert result["double"] == 3.14


def test_to_proto_json_nested_message():
    """Nested messages are serialized when set."""
    msg = Message(first_name="John", last_name="Doe")
    foo = Foo(message=msg)
    result = json.loads(foo.to_proto_json())
    assert result["message"] == {"first_name": "John", "last_name": "Doe"}


def test_to_proto_json_repeated():
    """Non-empty repeated fields are included."""
    foo = Foo(int32_repeated=[1, 2, 3])
    result = json.loads(foo.to_proto_json())
    assert result["int32_repeated"] == [1, 2, 3]


def test_to_proto_json_enum():
    """Enum fields are included when set."""
    foo = Foo(enum=Enum.ACTIVE)
    result = json.loads(foo.to_proto_json())
    assert result["enum"] == "ACTIVE"


def test_to_proto_json_override_exclude_defaults():
    """Callers can override exclude_defaults=False to include all fields."""
    m = Message()
    result = json.loads(m.to_proto_json(exclude_defaults=False))
    assert "first_name" in result
    assert result["first_name"] == ""


def test_to_proto_dict_override_by_alias():
    """Callers can override by_alias=False to get Python attribute names."""
    foo = Foo(bool_=True)
    result = foo.to_proto_dict(by_alias=False)
    assert "bool_" in result
    assert "bool" not in result
