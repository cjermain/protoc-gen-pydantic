import pytest

from api.v1.custom_options_pydantic import Color, Currency


# --- custom options access ---


@pytest.mark.parametrize(
    "member,expected",
    [
        (
            Currency.USD,
            {"display_name": "US Dollar", "priority": 1, "is_default": True},
        ),
        (Currency.EUR, {"display_name": "Euro", "priority": 2}),
        (Currency.GBP, {"display_name": "British Pound"}),
    ],
)
def test_custom_options(member, expected):
    assert member.options.custom_options == expected


def test_custom_options_default_empty_dict():
    assert Currency.UNSPECIFIED.options.custom_options == {}


# --- built-in options still work ---


@pytest.mark.parametrize(
    "member,expected",
    [
        (Currency.UNSPECIFIED, 0),
        (Currency.USD, 1),
        (Currency.EUR, 2),
        (Currency.GBP, 3),
    ],
)
def test_number_options(member, expected):
    assert member.options.number == expected


def test_deprecated_default():
    for member in Currency:
        assert member.options.deprecated is False


# --- Color enum without custom options ---


def test_color_no_options():
    assert [m.value for m in Color] == [
        "UNSPECIFIED",
        "RED",
        "GREEN",
        "BLUE",
    ]
    for member in Color:
        assert isinstance(member, str)


# --- immutability ---


def test_custom_options_frozen():
    with pytest.raises(AttributeError):
        Currency.USD.options.deprecated = True
