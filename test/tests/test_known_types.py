import datetime

import pytest

from api.v1.known_types_pydantic import WellKnownTypes


@pytest.fixture
def wkt():
    return WellKnownTypes(
        wkt_timestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        wkt_duration=datetime.timedelta(seconds=30),
        wkt_struct={"key": "value", "nested": {"a": 1}},
        wkt_value="hello",
        wkt_list_value=[1, "two", True],
        wkt_any={"type": "test"},
        wkt_field_mask=["field1", "field2"],
        wkt_bool=True,
        wkt_int32=42,
        wkt_int64=9999999999,
        wkt_uint32=100,
        wkt_uint64=200,
        wkt_float=3.14,
        wkt_double=2.718,
        wkt_string="test",
        wkt_bytes=b"binary",
        wkt_empty=None,
    )


def test_wkt_timestamp(wkt):
    assert isinstance(wkt.wkt_timestamp, datetime.datetime)
    assert wkt.wkt_timestamp.year == 2024


def test_wkt_duration(wkt):
    assert isinstance(wkt.wkt_duration, datetime.timedelta)
    assert wkt.wkt_duration.total_seconds() == 30


def test_wkt_struct(wkt):
    assert isinstance(wkt.wkt_struct, dict)
    assert wkt.wkt_struct["key"] == "value"


def test_wkt_value(wkt):
    assert wkt.wkt_value == "hello"


def test_wkt_list_value(wkt):
    assert isinstance(wkt.wkt_list_value, list)
    assert wkt.wkt_list_value == [1, "two", True]


def test_wkt_field_mask(wkt):
    assert wkt.wkt_field_mask == ["field1", "field2"]


def test_wkt_wrapper_types(wkt):
    assert wkt.wkt_bool is True
    assert wkt.wkt_int32 == 42
    assert wkt.wkt_int64 == 9999999999
    assert wkt.wkt_uint32 == 100
    assert wkt.wkt_uint64 == 200
    assert wkt.wkt_float == pytest.approx(3.14)
    assert wkt.wkt_double == pytest.approx(2.718)
    assert wkt.wkt_string == "test"
    assert wkt.wkt_bytes == b"binary"


def test_wkt_empty(wkt):
    assert wkt.wkt_empty is None


def test_wkt_json_roundtrip(wkt):
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wkt_timestamp == wkt.wkt_timestamp
    assert wkt2.wkt_duration == wkt.wkt_duration
    assert wkt2.wkt_struct == wkt.wkt_struct
    assert wkt2.wkt_bool is True
    assert wkt2.wkt_string == "test"
