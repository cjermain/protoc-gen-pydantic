import pytest

from api.v1.custom_options_pydantic import Color, Currency


# --- custom options access ---


def test_custom_options_usd():
    assert Currency.USD.options.display_name == "US Dollar"
    assert Currency.USD.options.priority == 1
    assert Currency.USD.options.is_default is True


def test_custom_options_eur():
    assert Currency.EUR.options.display_name == "Euro"
    assert Currency.EUR.options.priority == 2
    assert Currency.EUR.options.is_default is None


def test_custom_options_gbp():
    assert Currency.GBP.options.display_name == "British Pound"
    assert Currency.GBP.options.priority is None
    assert Currency.GBP.options.is_default is None


def test_custom_options_default_none():
    assert Currency.UNSPECIFIED.options.display_name is None
    assert Currency.UNSPECIFIED.options.priority is None
    assert Currency.UNSPECIFIED.options.is_default is None


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
