"""Tests for the disable_validate=true plugin option.

When disable_validate=true, all buf.validate constraints and CEL validators
are omitted from generated models. Fields that would otherwise be
ConstrainedRequired retain their proto3 zero-value defaults.
"""

from pathlib import Path

GEN_NOVALIDATE_PARTIAL = Path("gen_novalidate/partial/v1")
VALIDATE_PARTIAL_FILE = GEN_NOVALIDATE_PARTIAL / "validate_partial_pydantic.py"


def test_no_after_validator():
    assert "_AfterValidator" not in VALIDATE_PARTIAL_FILE.read_text()


def test_no_annotated_import():
    assert "_Annotated" not in VALIDATE_PARTIAL_FILE.read_text()


def test_no_proto_types_import():
    assert "_proto_types" not in VALIDATE_PARTIAL_FILE.read_text()


def test_no_buf_validate_comment():
    assert "# buf.validate:" not in VALIDATE_PARTIAL_FILE.read_text()


def test_no_proto_types_file():
    assert not (GEN_NOVALIDATE_PARTIAL / "_proto_types.py").exists()


def test_address_has_default():
    source = VALIDATE_PARTIAL_FILE.read_text()
    assert 'address: str = _Field(\n        default="",\n' in source


def test_id_has_default():
    source = VALIDATE_PARTIAL_FILE.read_text()
    assert 'id_: str = _Field(\n        default="",\n' in source


def test_address_not_required():
    from conftest import _load_module

    mod = _load_module("novalidate_validate_partial", VALIDATE_PARTIAL_FILE)
    field_info = mod.ValidatedEmail.model_fields["address"]
    assert not field_info.is_required()
    assert field_info.default == ""


def test_id_not_required():
    from conftest import _load_module

    mod = _load_module("novalidate_validate_partial", VALIDATE_PARTIAL_FILE)
    field_info = mod.ValidatedUUID.model_fields["id_"]
    assert not field_info.is_required()
    assert field_info.default == ""


def test_address_no_metadata_validators():
    from conftest import _load_module

    mod = _load_module("novalidate_validate_partial", VALIDATE_PARTIAL_FILE)
    field_info = mod.ValidatedEmail.model_fields["address"]
    assert field_info.metadata == []


def test_validated_email_instantiates_without_args():
    from conftest import _load_module

    mod = _load_module("novalidate_validate_partial", VALIDATE_PARTIAL_FILE)
    obj = mod.ValidatedEmail()
    assert obj.address == ""


def test_validated_email_accepts_invalid_email():
    from conftest import _load_module

    mod = _load_module("novalidate_validate_partial", VALIDATE_PARTIAL_FILE)
    obj = mod.ValidatedEmail(address="not-an-email")
    assert obj.address == "not-an-email"
