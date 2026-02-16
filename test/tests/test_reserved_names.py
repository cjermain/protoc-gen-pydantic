from api.v1.reserved_names_pydantic import ReservedFieldNames


def test_reserved_field_names():
    """Fields named after Pydantic internals should not shadow BaseModel attributes."""
    obj = ReservedFieldNames(model_config_="a", model_fields_="b", model_dump_="c")
    assert obj.model_config_ == "a"
    assert obj.model_fields_ == "b"
    assert obj.model_dump_ == "c"


def test_reserved_field_names_by_alias():
    """Reserved fields can also be constructed using the alias (original proto name)."""
    obj = ReservedFieldNames(
        **{"model_config": "a", "model_fields": "b", "model_dump": "c"}
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
