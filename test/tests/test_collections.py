from api.v1.collections_pydantic import Collections
from api.v1.enums_pydantic import Enum

from conftest import make_collections


def test_repeated_fields():
    c = make_collections()
    assert c.int32_repeated == [1, 2]
    assert c.string_repeated == ["a"]
    assert c.bool_repeated == [True, False]
    assert c.message_repeated[0].first_name == "John"
    assert c.nested_message_repeated[0].first_name == "Jane"


def test_map_key_types():
    c = make_collections()
    assert c.int32_map_key[1] == "a"
    assert c.string_map_key["key"] == "val"
    assert c.bool_map_key[True] == "k"


def test_map_value_types():
    c = make_collections()
    assert c.int32_map_value["a"] == 1
    assert c.bool_map_value["a"] is True
    assert c.float_map_value["a"] == 1.0
    assert c.enum_map_value["a"] == Enum.ACTIVE
    assert c.message_map_value["a"].first_name == "John"
    assert c.bytes_map_value["a"] == b"c"


def test_zero_value_defaults():
    """Collections() with no arguments should have empty lists and dicts."""
    c = Collections()
    assert c.int32_repeated == []
    assert c.int32_map_key == {}
    assert c.string_map_value == {}


def test_json_roundtrip():
    c = make_collections()
    json_str = c.model_dump_json()
    c2 = Collections.model_validate_json(json_str)
    assert c2.int32_repeated == c.int32_repeated
    assert c2.string_map_key == c.string_map_key


def test_dict_roundtrip():
    c = make_collections()
    d = c.model_dump()
    c2 = Collections.model_validate(d)
    assert c2.message_repeated[0].first_name == "John"
    assert c2.message_map_value["a"].first_name == "John"
