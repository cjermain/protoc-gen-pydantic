from api.v1.types_pydantic import Message
from foo.bar.v1.cross_reference_pydantic import CrossRefMessage


def test_cross_reference_construction():
    """Cross-package message can reference types from another package."""
    msg = CrossRefMessage(
        id_="test-1",
        referenced_message=Message(first_name="John", last_name="Doe"),
        foo_list=[],
    )
    assert msg.id_ == "test-1"
    assert msg.referenced_message.first_name == "John"


def test_cross_reference_json_roundtrip():
    """Cross-package message should survive JSON roundtrip."""
    msg = CrossRefMessage(
        id_="test-1",
        referenced_message=Message(first_name="John", last_name="Doe"),
        foo_list=[],
    )
    json_str = msg.model_dump_json()
    restored = CrossRefMessage.model_validate_json(json_str)
    assert restored == msg
