import pytest

from api.v1.reserved_names_pydantic import ReservedFieldNames, ReservedOneof


def test_reserved_field_names():
    """Fields named after Pydantic internals should not shadow BaseModel attributes."""
    obj = ReservedFieldNames(model_config_="a", model_fields_="b", model_dump_="c")
    assert obj.model_config_ == "a"
    assert obj.model_fields_ == "b"
    assert obj.model_dump_ == "c"


def test_reserved_field_names_by_alias():
    """Reserved fields can also be constructed using the alias (camelCase wire name)."""
    obj = ReservedFieldNames(
        **{"modelConfig": "a", "modelFields": "b", "modelDump": "c"}
    )
    assert obj.model_config_ == "a"
    assert obj.model_fields_ == "b"
    assert obj.model_dump_ == "c"


def test_reserved_field_names_roundtrip():
    """Reserved field name model should survive JSON roundtrip."""
    obj = ReservedFieldNames(model_config_="a", model_fields_="b", model_dump_="c")
    data = obj.model_dump()
    restored = ReservedFieldNames(**data)
    assert restored == obj


def test_reserved_oneof_single_field_valid():
    """Oneof with reserved-name members accepts a single field set."""
    obj = ReservedOneof(**{"bool": True})
    assert obj.bool_ is True
    assert obj.float_ is None
    assert obj.count is None


def test_reserved_oneof_single_non_reserved_valid():
    """Oneof with reserved-name members accepts the non-reserved field set."""
    obj = ReservedOneof(count=5)
    assert obj.bool_ is None
    assert obj.float_ is None
    assert obj.count == 5


def test_reserved_oneof_multiple_fields_invalid():
    """Oneof with reserved-name members rejects multiple fields set."""
    with pytest.raises(ValueError, match="oneof 'value'"):
        ReservedOneof(**{"bool": True, "float": 1.5})
