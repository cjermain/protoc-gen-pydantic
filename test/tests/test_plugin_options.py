"""Tests for plugin options using gen_options/ output.

All options are set to non-default values:
  - preserving_proto_field_name=true
  - auto_trim_enum_prefix=false
  - use_integers_for_enums=true
  - disable_field_description=true
  - use_none_union_syntax_instead_of_optional=true
"""

import importlib.util
import sys
from enum import Enum as StdEnum
from pathlib import Path

import pytest

GEN_OPTIONS_DIR = Path("gen_options/api/v1")
TYPES_FILE = GEN_OPTIONS_DIR / "types_pydantic.py"


def _load_module(name, filepath):
    """Load a module from gen_options/ under a unique name to avoid conflicts with gen/."""
    full_name = f"gen_options_test.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def types_source():
    return TYPES_FILE.read_text()


@pytest.fixture
def opts_enums():
    return _load_module("enums_pydantic", GEN_OPTIONS_DIR / "enums_pydantic.py")


@pytest.fixture
def opts_types(opts_enums):
    # types_pydantic has `from .enums_pydantic import Enum` — wire up a virtual
    # package so the relative import resolves to our loaded modules.
    pkg_name = "gen_options_test.api_v1_pkg"
    mod_name = f"{pkg_name}.types_pydantic"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    if pkg_name not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec(pkg_name, None, is_package=True)
        )
        proto_types = _load_module("_proto_types", GEN_OPTIONS_DIR / "_proto_types.py")
        pkg.enums_pydantic = opts_enums
        pkg._proto_types = proto_types
        sys.modules[pkg_name] = pkg
        sys.modules[f"{pkg_name}.enums_pydantic"] = opts_enums
        sys.modules[f"{pkg_name}._proto_types"] = proto_types
    spec = importlib.util.spec_from_file_location(mod_name, TYPES_FILE)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# --- preserving_proto_field_name=true ---


def test_preserving_proto_field_name_snake_case(opts_types):
    """Fields use snake_case names when preserving_proto_field_name=true."""
    Message = opts_types.Message
    assert "first_name" in Message.model_fields
    assert "last_name" in Message.model_fields


def test_preserving_proto_field_name_no_camel_case(opts_types):
    """camelCase names are not used when preserving_proto_field_name=true."""
    Message = opts_types.Message
    assert "firstName" not in Message.model_fields
    assert "lastName" not in Message.model_fields


# --- auto_trim_enum_prefix=false ---


def test_auto_trim_enum_prefix_keeps_prefix(opts_types):
    """Enum values keep their type prefix when auto_trim_enum_prefix=false."""
    NestedEnum = opts_types.Foo_NestedEnum
    assert hasattr(NestedEnum, "NESTED_ENUM_ACTIVE")
    assert hasattr(NestedEnum, "NESTED_ENUM_INACTIVE")
    assert hasattr(NestedEnum, "NESTED_ENUM_UNSPECIFIED")


# --- use_integers_for_enums=true ---


def test_use_integers_for_enums_base_is_int(opts_types):
    """Enum base class is int when use_integers_for_enums=true."""
    NestedEnum = opts_types.Foo_NestedEnum
    assert issubclass(NestedEnum, int)
    assert issubclass(NestedEnum, StdEnum)
    assert not issubclass(NestedEnum, str)


def test_use_integers_for_enums_values_are_ints(opts_types):
    """Enum member values are integers when use_integers_for_enums=true."""
    NestedEnum = opts_types.Foo_NestedEnum
    assert NestedEnum.NESTED_ENUM_ACTIVE == 1
    assert NestedEnum.NESTED_ENUM_INACTIVE == 2


# --- disable_field_description=true ---


def test_disable_field_description(opts_types):
    """Field descriptions are None when disable_field_description=true."""
    Message = opts_types.Message
    assert Message.model_fields["first_name"].description is None
    assert Message.model_fields["last_name"].description is None


# --- use_none_union_syntax_instead_of_optional=true ---


def test_use_none_union_syntax(types_source):
    """Source uses `| None` syntax instead of Optional when option is true."""
    assert "| None" in types_source
    assert "_Optional" not in types_source
