"""Pydantic validation error tests for generated models."""

import pytest
from pydantic import ValidationError

from api.v1.messages_pydantic import Message
from api.v1.oneofs_pydantic import Oneofs
from api.v1.scalars_pydantic import Scalars


def test_wrong_type_for_int32():
    with pytest.raises(ValidationError):
        Scalars(int32="not_a_number")


def test_wrong_type_for_string():
    with pytest.raises(ValidationError):
        Scalars(string=12345)


def test_wrong_type_for_bool():
    """Pydantic coerces many values to bool; a dict should fail."""
    with pytest.raises(ValidationError):
        Scalars(bool_={"not": "a bool"})


def test_wrong_type_for_bytes():
    with pytest.raises(ValidationError):
        Scalars(bytes_=12345)


def test_wrong_type_for_nested_message():
    with pytest.raises(ValidationError):
        Scalars(message="not a message")


def test_wrong_type_for_optional_message():
    with pytest.raises(ValidationError):
        Scalars(message_optional="not a message")


def test_wrong_type_for_oneof_a():
    with pytest.raises(ValidationError):
        Oneofs(a="not_an_int")


def test_wrong_type_for_oneof_b():
    with pytest.raises(ValidationError):
        Oneofs(b={"not": "a string"})


def test_message_wrong_field_type():
    with pytest.raises(ValidationError):
        Message(first_name=12345)
