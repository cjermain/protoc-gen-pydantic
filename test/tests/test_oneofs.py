import pytest
from pydantic import ValidationError

from api.v1.oneofs_pydantic import Oneofs


def test_default_none():
    o = Oneofs()
    assert o.a is None
    assert o.b is None


def test_set_a():
    o = Oneofs(a=99)
    assert o.a == 99
    assert o.b is None


def test_set_b():
    o = Oneofs(b="test")
    assert o.b == "test"
    assert o.a is None


def test_set_both_raises():
    """Setting multiple fields in a oneof raises ValidationError."""
    with pytest.raises(ValidationError):
        Oneofs(a=1, b="two")


def test_set_both_error_message():
    with pytest.raises(ValidationError, match="oneof 'union'"):
        Oneofs(a=1, b="two")


def test_json_roundtrip():
    o = Oneofs(a=42)
    json_str = o.model_dump_json()
    o2 = Oneofs.model_validate_json(json_str)
    assert o2.a == 42
