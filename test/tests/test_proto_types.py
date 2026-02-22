"""Tests for conditional _proto_types.py content.

Verifies that buildProtoTypesContent only emits the imports and validator
functions actually needed by files in each output directory.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from partial.v1.validate_partial_pydantic import ValidatedEmail, ValidatedUUID

GEN = Path("gen")


# ---------------------------------------------------------------------------
# Structural: which directories get a _proto_types.py at all
# ---------------------------------------------------------------------------


def test_partial_proto_types_exists():
    """partial/v1 uses email+uuid validators so _proto_types.py must be generated."""
    assert (GEN / "partial/v1/_proto_types.py").exists()


def test_foo_bar_v1_no_proto_types():
    """foo/bar/v1 has no runtime imports at all; _proto_types.py must not be generated."""
    assert not (GEN / "foo/bar/v1/_proto_types.py").exists()


# ---------------------------------------------------------------------------
# Content: partial/v1 has exactly the needed subset
# ---------------------------------------------------------------------------


def test_partial_proto_types_has_email_validator():
    text = (GEN / "partial/v1/_proto_types.py").read_text()
    assert "_validate_email" in text


def test_partial_proto_types_has_uuid_validator():
    text = (GEN / "partial/v1/_proto_types.py").read_text()
    assert "_validate_uuid" in text
    assert "import uuid as _uuid_lib" in text


def test_partial_proto_types_omits_ip_imports():
    """No IP validators used; ipaddress must not be imported."""
    text = (GEN / "partial/v1/_proto_types.py").read_text()
    assert "import ipaddress" not in text
    assert "_validate_ip" not in text
    assert "_validate_ipv4" not in text
    assert "_validate_ipv6" not in text


def test_partial_proto_types_omits_uri_imports():
    """No URI validator used; AnyUrl/TypeAdapter/_url_adapter must be absent."""
    text = (GEN / "partial/v1/_proto_types.py").read_text()
    assert "_AnyUrl" not in text
    assert "_TypeAdapter" not in text
    assert "_url_adapter" not in text
    assert "_validate_uri" not in text


# ---------------------------------------------------------------------------
# Content: api/v1 has all six format validators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol",
    [
        "import ipaddress as _ipaddress",
        "import uuid as _uuid_lib",
        "_AnyUrl",
        "_url_adapter",
        "_validate_email",
        "_validate_uri",
        "_validate_ip",
        "_validate_ipv4",
        "_validate_ipv6",
        "_validate_uuid",
    ],
)
def test_api_v1_proto_types_has_all_format_validators(symbol):
    text = (GEN / "api/v1/_proto_types.py").read_text()
    assert symbol in text


# ---------------------------------------------------------------------------
# Functional: partial/v1 models enforce their constraints
# ---------------------------------------------------------------------------


def test_validated_email_valid():
    m = ValidatedEmail(address="user@example.com")
    assert m.address == "user@example.com"


def test_validated_email_empty_allowed():
    # Proto3 zero value (empty string) bypasses the validator.
    m = ValidatedEmail(address="")
    assert m.address == ""


def test_validated_email_invalid():
    with pytest.raises(ValidationError):
        ValidatedEmail(address="not-an-email")


def test_validated_uuid_valid():
    # Field is named id_ (alias="id") because `id` is a Python builtin.
    m = ValidatedUUID(id="550e8400-e29b-41d4-a716-446655440000")
    assert m.id_ == "550e8400-e29b-41d4-a716-446655440000"


def test_validated_uuid_empty_allowed():
    m = ValidatedUUID(id="")
    assert m.id_ == ""


def test_validated_uuid_invalid():
    with pytest.raises(ValidationError):
        ValidatedUUID(id="not-a-uuid")
