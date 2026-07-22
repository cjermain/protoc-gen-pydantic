"""TDD spec for the `camel_case_alias` option (default: true).

Contract under test:
- model_dump/model_dump_json default to camelCase keys on the wire, matching
  canonical proto3 JSON, even though `preserving_proto_field_name=true` keeps
  the Python attribute snake_case.
- Construction/validation accepts EITHER the camelCase wire alias or the
  snake_case Python attribute name (populate_by_name=True).
- Python attribute access always stays snake_case, regardless of wire format.

This currently fails: no per-field alias is emitted for non-reserved fields
today, so the wire format matches the attribute name (snake_case) and
constructing by the camelCase name is silently ignored (extra='ignore').
"""

import json

from api.v1.messages_pydantic import Message


def test_model_dump_uses_camel_case_by_default():
    """Multi-word field names are serialized as camelCase on the wire by default."""
    m = Message(first_name="John", last_name="Doe")
    assert m.model_dump() == {"firstName": "John", "lastName": "Doe"}


def test_model_dump_json_uses_camel_case_by_default():
    """Multi-word field names are serialized as camelCase in JSON by default."""
    m = Message(first_name="John", last_name="Doe")
    assert json.loads(m.model_dump_json()) == {"firstName": "John", "lastName": "Doe"}


def test_construct_by_camel_case_alias():
    """Fields can be constructed using the camelCase wire name."""
    m = Message(**{"firstName": "John", "lastName": "Doe"})
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_construct_by_snake_case_attribute_name():
    """Fields can still be constructed using the Python (snake_case) attribute name."""
    m = Message(first_name="John", last_name="Doe")
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_model_validate_accepts_camel_case_keys():
    """model_validate accepts camelCase keys and stores them under snake_case attrs."""
    m = Message.model_validate({"firstName": "John", "lastName": "Doe"})
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_roundtrip_via_model_dump():
    """A model dumped to camelCase and revalidated reproduces an equal object."""
    original = Message(first_name="John", last_name="Doe")
    restored = Message.model_validate(original.model_dump())
    assert restored == original


def test_roundtrip_via_model_dump_json():
    """A model dumped to camelCase JSON and revalidated reproduces an equal object."""
    original = Message(first_name="John", last_name="Doe")
    restored = Message.model_validate_json(original.model_dump_json())
    assert restored == original
