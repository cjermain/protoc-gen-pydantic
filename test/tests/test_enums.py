import pytest
from api.v1.enums_pydantic import Enum, Shape
from api.v1.scalars_pydantic import Scalars


@pytest.mark.parametrize(
    "enum_cls,expected",
    [
        (Enum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
        (Scalars.NestedEnum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
    ],
)
def test_enum_values(enum_cls, expected):
    assert [m.value for m in enum_cls] == expected


@pytest.mark.parametrize("enum_cls", [Enum, Scalars.NestedEnum])
def test_enum_is_str(enum_cls):
    for member in enum_cls:
        assert isinstance(member, str)


# ---------------------------------------------------------------------------
# Shape.Kind — nested enum with deprecated option on SQUARE
# ---------------------------------------------------------------------------


def test_shape_kind_values():
    assert [m.value for m in Shape.Kind] == ["UNSPECIFIED", "CIRCLE", "SQUARE"]


def test_shape_kind_square_deprecated():
    assert Shape.Kind.SQUARE.options.deprecated is True


def test_shape_kind_circle_not_deprecated():
    assert Shape.Kind.CIRCLE.options.deprecated is False


def test_shape_kind_unspecified_not_deprecated():
    assert Shape.Kind.UNSPECIFIED.options.deprecated is False
