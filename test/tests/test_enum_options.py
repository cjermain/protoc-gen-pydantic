import pytest

from api.v1.enum_options_pydantic import Status


# --- options access ---


@pytest.mark.parametrize(
    "member,expected",
    [
        (Status.UNSPECIFIED, False),
        (Status.ACTIVE, False),
        (Status.INACTIVE, False),
        (Status.ARCHIVED, True),
    ],
)
def test_deprecated(member, expected):
    assert member.options.deprecated is expected


def test_debug_redact_defaults_false():
    for member in Status:
        assert member.options.debug_redact is False


@pytest.mark.parametrize(
    "member,expected",
    [
        (Status.UNSPECIFIED, 0),
        (Status.ACTIVE, 1),
        (Status.INACTIVE, 2),
        (Status.ARCHIVED, 3),
    ],
)
def test_options_number(member, expected):
    assert member.options.number == expected


# --- enum values unchanged ---


def test_values_are_strings():
    for member in Status:
        assert isinstance(member, str)


def test_enum_values():
    assert [m.value for m in Status] == [
        "UNSPECIFIED",
        "ACTIVE",
        "INACTIVE",
        "ARCHIVED",
    ]


def test_iteration():
    assert [m.name for m in Status] == [
        "UNSPECIFIED",
        "ACTIVE",
        "INACTIVE",
        "ARCHIVED",
    ]


# --- immutability ---


def test_options_frozen():
    with pytest.raises(AttributeError):
        Status.ARCHIVED.options.deprecated = False
