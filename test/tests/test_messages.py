from api.v1.messages_pydantic import Empty, Message


def test_message_valid():
    m = Message(first_name="John", last_name="Doe")
    assert m.first_name == "John"
    assert m.last_name == "Doe"


def test_message_zero_value_defaults():
    """Proto3 messages can be constructed with no arguments; fields take zero values."""
    m = Message()
    assert m.first_name == ""
    assert m.last_name == ""


def test_empty_model():
    e = Empty()
    assert e is not None
    assert len(Empty.model_fields) == 0


def test_message_json_roundtrip():
    m = Message(first_name="John", last_name="Doe")
    json_str = m.model_dump_json()
    m2 = Message.model_validate_json(json_str)
    assert m2.first_name == m.first_name
    assert m2.last_name == m.last_name
