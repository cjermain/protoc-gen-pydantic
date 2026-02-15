from api.v1.reserved_names_pydantic import ReservedFieldNames


def test_reserved_field_names():
    """Fields named after Pydantic internals should not shadow BaseModel attributes."""
    obj = ReservedFieldNames(modelConfig="a", modelFields="b", modelDump="c")
    assert obj.modelConfig == "a"
    assert obj.modelFields == "b"
    assert obj.modelDump == "c"


def test_reserved_field_names_roundtrip():
    """Reserved field name model should survive JSON roundtrip."""
    obj = ReservedFieldNames(modelConfig="a", modelFields="b", modelDump="c")
    data = obj.model_dump()
    restored = ReservedFieldNames(**data)
    assert restored == obj
