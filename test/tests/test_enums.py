import pytest

from api.v1.enums_pydantic import Enum
from api.v1.scalars_pydantic import Scalars_NestedEnum


@pytest.mark.parametrize(
    "enum_cls,expected",
    [
        (Enum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
        (Scalars_NestedEnum, ["UNSPECIFIED", "ACTIVE", "INACTIVE"]),
    ],
)
def test_enum_values(enum_cls, expected):
    assert [m.value for m in enum_cls] == expected


@pytest.mark.parametrize("enum_cls", [Enum, Scalars_NestedEnum])
def test_enum_is_str(enum_cls):
    for member in enum_cls:
        assert isinstance(member, str)
