"""Tests for plugin options using gen_options/ output.

All options are set to non-default values:
  - preserving_proto_field_name=true
  - auto_trim_enum_prefix=false
  - use_integers_for_enums=true
  - disable_field_description=true
  - use_none_union_syntax_instead_of_optional=true
"""

from pathlib import Path

import pytest

TYPES_FILE = Path("gen_options/api/v1/types_pydantic.py")


@pytest.fixture
def types_source():
    return TYPES_FILE.read_text()


# --- preserving_proto_field_name=true ---


def test_preserving_proto_field_name_snake_case(types_source):
    assert "first_name" in types_source
    assert "last_name" in types_source


def test_preserving_proto_field_name_no_camel_case(types_source):
    assert "firstName" not in types_source
    assert "lastName" not in types_source


# --- auto_trim_enum_prefix=false ---


def test_auto_trim_enum_prefix_keeps_prefix(types_source):
    assert "NESTED_ENUM_ACTIVE" in types_source
    assert "NESTED_ENUM_INACTIVE" in types_source
    assert "NESTED_ENUM_UNSPECIFIED" in types_source


# --- use_integers_for_enums=true ---


def test_use_integers_for_enums_base_is_int(types_source):
    assert "int, _Enum" in types_source
    assert "str, _Enum" not in types_source


def test_use_integers_for_enums_values_are_ints(types_source):
    assert "NESTED_ENUM_ACTIVE = 1" in types_source
    assert "NESTED_ENUM_INACTIVE = 2" in types_source


# --- disable_field_description=true ---


def test_disable_field_description(types_source):
    assert "description=" not in types_source


# --- use_none_union_syntax_instead_of_optional=true ---


def test_use_none_union_syntax(types_source):
    assert "| None" in types_source
    assert "_Optional" not in types_source
