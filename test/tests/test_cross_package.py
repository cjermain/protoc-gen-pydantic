from api.v1.messages_pydantic import Message
from foo.bar.v1.cross_options_pydantic import Language
from foo.bar.v1.cross_reference_pydantic import CrossRefMessage


# --- cross_reference ---


def test_cross_reference_construction():
    """Cross-package message can reference types from another package."""
    msg = CrossRefMessage(
        id_="test-1",
        referenced_message=Message(first_name="John", last_name="Doe"),
        scalars_list=[],
    )
    assert msg.id_ == "test-1"
    assert msg.referenced_message.first_name == "John"


def test_cross_reference_json_roundtrip():
    """Cross-package message should survive JSON roundtrip."""
    msg = CrossRefMessage(
        id_="test-1",
        referenced_message=Message(first_name="John", last_name="Doe"),
        scalars_list=[],
    )
    json_str = msg.model_dump_json()
    restored = CrossRefMessage.model_validate_json(json_str)
    assert restored == msg


# --- cross_options ---


def test_cross_proto_display_name():
    assert Language.PYTHON.options.display_name == "Python"
    assert Language.GOLANG.options.display_name == "Golang"
    assert Language.RUST.options.display_name == "Rust"


def test_cross_proto_priority():
    assert Language.RUST.options.priority == 1
    assert Language.PYTHON.options.priority is None


def test_cross_proto_defaults_none():
    assert Language.UNSPECIFIED.options.display_name is None
    assert Language.UNSPECIFIED.options.priority is None
    assert Language.UNSPECIFIED.options.is_default is None
