"""Tests for plugin options using gen_options/ output.

All options are set to non-default values:
  - preserving_proto_field_name=false
  - auto_trim_enum_prefix=false
  - use_integers_for_enums=true
  - disable_field_description=true
  - use_none_union_syntax_instead_of_optional=false
"""

import importlib.machinery
import importlib.util
import sys
from enum import Enum as StdEnum
from pathlib import Path

import pytest

from conftest import _load_module

GEN_OPTIONS_DIR = Path("gen_options/api/v1")
SCALARS_FILE = GEN_OPTIONS_DIR / "scalars_pydantic.py"
MESSAGES_FILE = GEN_OPTIONS_DIR / "messages_pydantic.py"


@pytest.fixture
def scalars_source():
    return SCALARS_FILE.read_text()


@pytest.fixture
def messages_source():
    return MESSAGES_FILE.read_text()


@pytest.fixture
def opts_enums():
    return _load_module("enums_pydantic", GEN_OPTIONS_DIR / "enums_pydantic.py")


@pytest.fixture
def opts_messages(opts_enums):
    pkg_name = "gen_options_test.api_v1_pkg"
    mod_name = f"{pkg_name}.messages_pydantic"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    if pkg_name not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(pkg_name, None, is_package=True)
        )
        sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(mod_name, MESSAGES_FILE)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def opts_scalars(opts_enums, opts_messages):
    pkg_name = "gen_options_test.api_v1_pkg"
    mod_name = f"{pkg_name}.scalars_pydantic"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    if pkg_name not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(pkg_name, None, is_package=True)
        )
        sys.modules[pkg_name] = pkg
    else:
        pkg = sys.modules[pkg_name]
    proto_types = _load_module("_proto_types", GEN_OPTIONS_DIR / "_proto_types.py")
    pkg.enums_pydantic = opts_enums
    pkg.messages_pydantic = opts_messages
    pkg._proto_types = proto_types
    sys.modules[f"{pkg_name}.enums_pydantic"] = opts_enums
    sys.modules[f"{pkg_name}.messages_pydantic"] = opts_messages
    sys.modules[f"{pkg_name}._proto_types"] = proto_types
    spec = importlib.util.spec_from_file_location(mod_name, SCALARS_FILE)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- preserving_proto_field_name=false ---


def test_preserving_proto_field_name_camel_case(opts_messages):
    """Fields use camelCase names when preserving_proto_field_name=false."""
    Message = opts_messages.Message
    assert "firstName" in Message.model_fields
    assert "lastName" in Message.model_fields


def test_preserving_proto_field_name_no_snake_case(opts_messages):
    """snake_case names are not used when preserving_proto_field_name=false."""
    Message = opts_messages.Message
    assert "first_name" not in Message.model_fields
    assert "last_name" not in Message.model_fields


# --- auto_trim_enum_prefix=false ---


def test_auto_trim_enum_prefix_keeps_prefix(opts_scalars):
    """Enum values keep their type prefix when auto_trim_enum_prefix=false."""
    NestedEnum = opts_scalars.Scalars.NestedEnum
    assert hasattr(NestedEnum, "NESTED_ENUM_ACTIVE")
    assert hasattr(NestedEnum, "NESTED_ENUM_INACTIVE")
    assert hasattr(NestedEnum, "NESTED_ENUM_UNSPECIFIED")


# --- use_integers_for_enums=true ---


def test_use_integers_for_enums_base_is_int(opts_scalars):
    """Enum base class is int when use_integers_for_enums=true."""
    NestedEnum = opts_scalars.Scalars.NestedEnum
    assert issubclass(NestedEnum, int)
    assert issubclass(NestedEnum, StdEnum)
    assert not issubclass(NestedEnum, str)


def test_use_integers_for_enums_values_are_ints(opts_scalars):
    """Enum member values are integers when use_integers_for_enums=true."""
    NestedEnum = opts_scalars.Scalars.NestedEnum
    assert NestedEnum.NESTED_ENUM_ACTIVE == 1
    assert NestedEnum.NESTED_ENUM_INACTIVE == 2


# --- disable_field_description=true ---


def test_disable_field_description(opts_messages):
    """Field descriptions are None when disable_field_description=true."""
    Message = opts_messages.Message
    assert Message.model_fields["firstName"].description is None
    assert Message.model_fields["lastName"].description is None


# --- use_none_union_syntax_instead_of_optional=false ---


def test_use_none_union_syntax(scalars_source):
    """Source uses `Optional[T]` syntax instead of `| None` when option is false."""
    assert "_Optional" in scalars_source
    assert "| None" not in scalars_source
