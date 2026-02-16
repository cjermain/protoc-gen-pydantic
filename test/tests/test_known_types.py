import datetime

import pytest

from api.v1.known_types_pydantic import WellKnownTypes


@pytest.fixture
def wkt():
    return WellKnownTypes(
        wktTimestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        wktDuration=datetime.timedelta(seconds=30),
        wktStruct={"key": "value", "nested": {"a": 1}},
        wktValue="hello",
        wktListValue=[1, "two", True],
        wktAny={"type": "test"},
        wktFieldMask=["field1", "field2"],
        wktBool=True,
        wktInt32=42,
        wktInt64=9999999999,
        wktUint32=100,
        wktUint64=200,
        wktFloat=3.14,
        wktDouble=2.718,
        wktString="test",
        wktBytes=b"binary",
        wktEmpty=None,
    )


def test_wkt_timestamp(wkt):
    assert isinstance(wkt.wktTimestamp, datetime.datetime)
    assert wkt.wktTimestamp.year == 2024


def test_wkt_duration(wkt):
    assert isinstance(wkt.wktDuration, datetime.timedelta)
    assert wkt.wktDuration.total_seconds() == 30


def test_wkt_struct(wkt):
    assert isinstance(wkt.wktStruct, dict)
    assert wkt.wktStruct["key"] == "value"


def test_wkt_value(wkt):
    assert wkt.wktValue == "hello"


def test_wkt_list_value(wkt):
    assert isinstance(wkt.wktListValue, list)
    assert wkt.wktListValue == [1, "two", True]


def test_wkt_field_mask(wkt):
    assert wkt.wktFieldMask == ["field1", "field2"]


def test_wkt_wrapper_types(wkt):
    assert wkt.wktBool is True
    assert wkt.wktInt32 == 42
    assert wkt.wktInt64 == 9999999999
    assert wkt.wktUint32 == 100
    assert wkt.wktUint64 == 200
    assert wkt.wktFloat == pytest.approx(3.14)
    assert wkt.wktDouble == pytest.approx(2.718)
    assert wkt.wktString == "test"
    assert wkt.wktBytes == b"binary"


def test_wkt_empty(wkt):
    assert wkt.wktEmpty is None


def test_wkt_json_roundtrip(wkt):
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wktTimestamp == wkt.wktTimestamp
    assert wkt2.wktDuration == wkt.wktDuration
    assert wkt2.wktStruct == wkt.wktStruct
    assert wkt2.wktBool is True
    assert wkt2.wktString == "test"
