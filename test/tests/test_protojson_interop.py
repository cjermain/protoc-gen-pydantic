"""Tests for proto-compatible JSON serialization via model_dump(mode='json').

Verifies that:
- int64 fields serialize as strings, accept string input
- Timestamp fields serialize as RFC 3339, accept string input
- Duration fields serialize as "Ns" strings, accept string input
- bytes fields serialize as base64
- special floats serialize as strings
"""

import base64
import datetime

import pytest

from api.v1.enums_pydantic import Enum
from api.v1.known_types_pydantic import WellKnownTypes
from api.v1.types_pydantic import Foo, Foo_NestedEnum, Foo_NestedMessage, Message

_WKT_DEFAULTS = dict(
    wktTimestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    wktDuration=datetime.timedelta(seconds=0),
    wktStruct={},
    wktValue=None,
    wktListValue=[],
    wktAny=None,
    wktFieldMask=[],
    wktBool=False,
    wktInt32=0,
    wktInt64=0,
    wktUint32=0,
    wktUint64=0,
    wktFloat=0.0,
    wktDouble=0.0,
    wktString="",
    wktBytes=b"",
    wktEmpty=None,
)


def make_wkt(**overrides):
    """Create a WellKnownTypes with sensible defaults, overriding specific fields."""
    return WellKnownTypes(**{**_WKT_DEFAULTS, **overrides})


@pytest.fixture
def wkt():
    return make_wkt(
        wktTimestamp=datetime.datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
        wktDuration=datetime.timedelta(seconds=3, milliseconds=500),
        wktStruct={"key": "value"},
        wktValue="hello",
        wktListValue=[1, "two"],
        wktAny={"type": "test"},
        wktFieldMask=["field1"],
        wktBool=True,
        wktInt32=42,
        wktInt64=9007199254740993,
        wktUint32=100,
        wktUint64=9007199254740993,
        wktFloat=3.14,
        wktDouble=2.718,
        wktString="test",
        wktBytes=b"binary",
    )


@pytest.fixture
def foo_minimal():
    """A Foo with int64 values that exceed JS safe integer range."""
    return Foo(
        int32=1,
        int64=9007199254740993,
        uint32=3,
        uint64=9007199254740993,
        fixed32=5,
        fixed64=9007199254740993,
        sint32=7,
        sint64=9007199254740993,
        sfixed32=9,
        sfixed64=9007199254740993,
        bool_=True,
        float_=1.5,
        double=2.5,
        string="hello",
        bytes_=b"\x00\x01\xff",
        enum=Enum.ACTIVE,
        nestedEnum=Foo_NestedEnum.ACTIVE,
        message=Message(firstName="John", lastName="Doe"),
        nestedMessage=Foo_NestedMessage(firstName="Jane", lastName="Doe"),
        wktTimestamp=datetime.datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
        int32Repeated=[],
        int64Repeated=[],
        uint32Repeated=[],
        uint64Repeated=[],
        fixed32Repeated=[],
        fixed64Repeated=[],
        sint32Repeated=[],
        sint64Repeated=[],
        sfixed32Repeated=[],
        sfixed64Repeated=[],
        boolRepeated=[],
        floatRepeated=[],
        doubleRepeated=[],
        stringRepeated=[],
        bytesRepeated=[],
        enumRepeated=[],
        nestedEnumRepeated=[],
        messageRepeated=[],
        nestedMessageRepeated=[],
        wktTimestampRepeated=[],
        int32MapKey={},
        int64MapKey={},
        uint32MapKey={},
        uint64MapKey={},
        fixed32MapKey={},
        fixed64MapKey={},
        sint32MapKey={},
        sint64MapKey={},
        sfixed32MapKey={},
        sfixed64MapKey={},
        boolMapKey={},
        stringMapKey={},
        int32MapValue={},
        int64MapValue={},
        uint32MapValue={},
        uint64MapValue={},
        fixed32MapValue={},
        fixed64MapValue={},
        sint32MapValue={},
        sint64MapValue={},
        sfixed32MapValue={},
        sfixed64MapValue={},
        boolMapValue={},
        floatMapValue={},
        doubleMapValue={},
        stringMapValue={},
        bytesMapValue={},
        enumMapValue={},
        nestedEnumMapValue={},
        messageMapValue={},
        nestedMessageMapValue={},
        wktTimestampMapValue={},
    )


# --- int64 YAML workflow ---


def test_int64_native_python_type(foo_minimal):
    """int64 fields are native int in Python."""
    assert isinstance(foo_minimal.int64, int)
    assert foo_minimal.int64 == 9007199254740993


def test_int64_json_mode_string(foo_minimal):
    """int64 serializes as string in JSON mode."""
    data = foo_minimal.model_dump(mode="json")
    assert data["int64"] == "9007199254740993"
    assert data["uint64"] == "9007199254740993"
    assert data["fixed64"] == "9007199254740993"
    assert data["sint64"] == "9007199254740993"
    assert data["sfixed64"] == "9007199254740993"


def test_int64_python_mode_int(foo_minimal):
    """int64 stays as int in Python mode (model_dump without mode='json')."""
    data = foo_minimal.model_dump()
    assert isinstance(data["int64"], int)
    assert data["int64"] == 9007199254740993


def test_int32_stays_int_in_json_mode(foo_minimal):
    """int32 fields stay as int even in JSON mode."""
    data = foo_minimal.model_dump(mode="json")
    assert isinstance(data["int32"], int)
    assert data["int32"] == 1


def test_int64_accepts_string_input():
    """Accepts string int64 from other systems."""
    wkt = make_wkt(
        wktInt64="9007199254740993",
        wktUint64="9007199254740993",
    )
    assert wkt.wktInt64 == 9007199254740993
    assert wkt.wktUint64 == 9007199254740993


# --- Timestamp YAML workflow ---


def test_timestamp_native_python_type(wkt):
    """Timestamp is native datetime in Python."""
    assert isinstance(wkt.wktTimestamp, datetime.datetime)


def test_timestamp_json_mode_rfc3339(wkt):
    """Timestamp serializes as RFC 3339 in JSON mode."""
    data = wkt.model_dump(mode="json")
    assert data["wktTimestamp"] == "2024-01-15T10:30:00Z"


def test_timestamp_python_mode_datetime(wkt):
    """Timestamp stays as datetime in Python mode."""
    data = wkt.model_dump()
    assert isinstance(data["wktTimestamp"], datetime.datetime)


def test_timestamp_accepts_rfc3339():
    """Accepts RFC 3339 string from other systems."""
    wkt = WellKnownTypes.model_validate(
        {**_WKT_DEFAULTS, "wktTimestamp": "2024-01-15T10:30:00Z", "wktDuration": "0s"}
    )
    assert isinstance(wkt.wktTimestamp, datetime.datetime)
    assert wkt.wktTimestamp.year == 2024
    assert wkt.wktTimestamp.month == 1
    assert wkt.wktTimestamp.day == 15


def test_timestamp_with_microseconds():
    """Timestamp preserves microsecond precision."""
    ts = datetime.datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=datetime.timezone.utc)
    wkt = make_wkt(wktTimestamp=ts)
    data = wkt.model_dump(mode="json")
    assert data["wktTimestamp"] == "2024-01-15T10:30:00.123456Z"


# --- Duration YAML workflow ---


def test_duration_native_python_type(wkt):
    """Duration is native timedelta in Python."""
    assert isinstance(wkt.wktDuration, datetime.timedelta)


def test_duration_json_mode_string(wkt):
    """Duration serializes as 'Ns' string in JSON mode."""
    data = wkt.model_dump(mode="json")
    assert data["wktDuration"] == "3.5s"


def test_duration_python_mode_timedelta(wkt):
    """Duration stays as timedelta in Python mode."""
    data = wkt.model_dump()
    assert isinstance(data["wktDuration"], datetime.timedelta)


def test_duration_integer_seconds():
    """Duration with whole seconds omits decimal."""
    wkt = make_wkt(wktDuration=datetime.timedelta(seconds=30))
    data = wkt.model_dump(mode="json")
    assert data["wktDuration"] == "30s"


def test_duration_accepts_string():
    """Accepts duration string from other systems."""
    wkt = WellKnownTypes.model_validate({**_WKT_DEFAULTS, "wktDuration": "3.5s"})
    assert wkt.wktDuration == datetime.timedelta(seconds=3, milliseconds=500)


# --- ConfigDict: bytes and special floats ---


def test_bytes_base64(foo_minimal):
    """bytes fields serialize as base64 in JSON mode."""
    data = foo_minimal.model_dump(mode="json", by_alias=True)
    expected = base64.urlsafe_b64encode(b"\x00\x01\xff").decode()
    assert data["bytes"] == expected


def test_nan_infinity():
    """NaN and Infinity serialize as strings in model_dump_json()."""
    wkt = make_wkt(wktFloat=float("nan"), wktDouble=float("inf"))
    json_str = wkt.model_dump_json()
    assert '"NaN"' in json_str
    assert '"Infinity"' in json_str


# --- JSON roundtrip with new types ---


def test_int64_json_roundtrip():
    """int64 survives JSON serialization roundtrip."""
    wkt = make_wkt(
        wktDuration=datetime.timedelta(seconds=30),
        wktInt64=9007199254740993,
        wktUint64=9007199254740993,
    )
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wktInt64 == 9007199254740993
    assert wkt2.wktUint64 == 9007199254740993


def test_timestamp_json_roundtrip():
    """Timestamp survives JSON serialization roundtrip."""
    ts = datetime.datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=datetime.timezone.utc)
    wkt = make_wkt(wktTimestamp=ts, wktDuration=datetime.timedelta(seconds=30))
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wktTimestamp == ts


def test_duration_json_roundtrip():
    """Duration survives JSON serialization roundtrip."""
    dur = datetime.timedelta(seconds=3, milliseconds=500)
    wkt = make_wkt(wktDuration=dur)
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wktDuration == dur
