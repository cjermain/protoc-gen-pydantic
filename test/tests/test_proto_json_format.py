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
from api.v1.messages_pydantic import Message
from api.v1.scalars_pydantic import Scalars

_WKT_DEFAULTS = dict(
    wkt_timestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    wkt_duration=datetime.timedelta(seconds=0),
    wkt_struct={},
    wkt_value=None,
    wkt_list_value=[],
    wkt_any=None,
    wkt_field_mask=[],
    wkt_bool=False,
    wkt_int32=0,
    wkt_int64=0,
    wkt_uint32=0,
    wkt_uint64=0,
    wkt_float=0.0,
    wkt_double=0.0,
    wkt_string="",
    wkt_bytes=b"",
    wkt_empty=None,
)


def make_wkt(**overrides):
    """Create a WellKnownTypes with sensible defaults, overriding specific fields."""
    return WellKnownTypes(**{**_WKT_DEFAULTS, **overrides})


@pytest.fixture
def wkt():
    return make_wkt(
        wkt_timestamp=datetime.datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
        wkt_duration=datetime.timedelta(seconds=3, milliseconds=500),
        wkt_struct={"key": "value"},
        wkt_value="hello",
        wkt_list_value=[1, "two"],
        wkt_any={"type": "test"},
        wkt_field_mask=["field1"],
        wkt_bool=True,
        wkt_int32=42,
        wkt_int64=9007199254740993,
        wkt_uint32=100,
        wkt_uint64=9007199254740993,
        wkt_float=3.14,
        wkt_double=2.718,
        wkt_string="test",
        wkt_bytes=b"binary",
    )


@pytest.fixture
def scalars_with_int64():
    """A Scalars with int64 values that exceed JS safe integer range."""
    return Scalars(
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
        nested_enum=Scalars.NestedEnum.ACTIVE,
        message=Message(first_name="John", last_name="Doe"),
        nested_message=Scalars.NestedMessage(first_name="Jane", last_name="Doe"),
    )


# --- int64 serialization ---


def test_int64_native_python_type(scalars_with_int64):
    """int64 fields are native int in Python."""
    assert isinstance(scalars_with_int64.int64, int)
    assert scalars_with_int64.int64 == 9007199254740993


def test_int64_json_mode_string(scalars_with_int64):
    """int64 serializes as string in JSON mode."""
    data = scalars_with_int64.model_dump(mode="json")
    assert data["int64"] == "9007199254740993"
    assert data["uint64"] == "9007199254740993"
    assert data["fixed64"] == "9007199254740993"
    assert data["sint64"] == "9007199254740993"
    assert data["sfixed64"] == "9007199254740993"


def test_int64_python_mode_int(scalars_with_int64):
    """int64 stays as int in Python mode (model_dump without mode='json')."""
    data = scalars_with_int64.model_dump()
    assert isinstance(data["int64"], int)
    assert data["int64"] == 9007199254740993


def test_int32_stays_int_in_json_mode(scalars_with_int64):
    """int32 fields stay as int even in JSON mode."""
    data = scalars_with_int64.model_dump(mode="json")
    assert isinstance(data["int32"], int)
    assert data["int32"] == 1


def test_int64_accepts_string_input():
    """Accepts string int64 from other systems."""
    wkt = make_wkt(
        wkt_int64="9007199254740993",
        wkt_uint64="9007199254740993",
    )
    assert wkt.wkt_int64 == 9007199254740993
    assert wkt.wkt_uint64 == 9007199254740993


# --- Timestamp serialization ---


def test_timestamp_native_python_type(wkt):
    """Timestamp is native datetime in Python."""
    assert isinstance(wkt.wkt_timestamp, datetime.datetime)


def test_timestamp_json_mode_rfc3339(wkt):
    """Timestamp serializes as RFC 3339 in JSON mode."""
    data = wkt.model_dump(mode="json")
    assert data["wkt_timestamp"] == "2024-01-15T10:30:00Z"


def test_timestamp_python_mode_datetime(wkt):
    """Timestamp stays as datetime in Python mode."""
    data = wkt.model_dump()
    assert isinstance(data["wkt_timestamp"], datetime.datetime)


def test_timestamp_accepts_rfc3339():
    """Accepts RFC 3339 string from other systems."""
    wkt = WellKnownTypes.model_validate(
        {**_WKT_DEFAULTS, "wkt_timestamp": "2024-01-15T10:30:00Z", "wkt_duration": "0s"}
    )
    assert isinstance(wkt.wkt_timestamp, datetime.datetime)
    assert wkt.wkt_timestamp.year == 2024
    assert wkt.wkt_timestamp.month == 1
    assert wkt.wkt_timestamp.day == 15


def test_timestamp_with_microseconds():
    """Timestamp preserves microsecond precision."""
    ts = datetime.datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=datetime.timezone.utc)
    wkt = make_wkt(wkt_timestamp=ts)
    data = wkt.model_dump(mode="json")
    assert data["wkt_timestamp"] == "2024-01-15T10:30:00.123456Z"


# --- Duration serialization ---


def test_duration_native_python_type(wkt):
    """Duration is native timedelta in Python."""
    assert isinstance(wkt.wkt_duration, datetime.timedelta)


def test_duration_json_mode_string(wkt):
    """Duration serializes as 'Ns' string in JSON mode."""
    data = wkt.model_dump(mode="json")
    assert data["wkt_duration"] == "3.5s"


def test_duration_python_mode_timedelta(wkt):
    """Duration stays as timedelta in Python mode."""
    data = wkt.model_dump()
    assert isinstance(data["wkt_duration"], datetime.timedelta)


def test_duration_integer_seconds():
    """Duration with whole seconds omits decimal."""
    wkt = make_wkt(wkt_duration=datetime.timedelta(seconds=30))
    data = wkt.model_dump(mode="json")
    assert data["wkt_duration"] == "30s"


def test_duration_accepts_string():
    """Accepts duration string from other systems."""
    wkt = WellKnownTypes.model_validate({**_WKT_DEFAULTS, "wkt_duration": "3.5s"})
    assert wkt.wkt_duration == datetime.timedelta(seconds=3, milliseconds=500)


# --- ConfigDict: bytes and special floats ---


def test_bytes_base64(scalars_with_int64):
    """bytes fields serialize as base64 in JSON mode."""
    data = scalars_with_int64.model_dump(mode="json", by_alias=True)
    expected = base64.urlsafe_b64encode(b"\x00\x01\xff").decode()
    assert data["bytes"] == expected


def test_nan_infinity():
    """NaN and Infinity serialize as strings in model_dump_json()."""
    wkt = make_wkt(wkt_float=float("nan"), wkt_double=float("inf"))
    json_str = wkt.model_dump_json()
    assert '"NaN"' in json_str
    assert '"Infinity"' in json_str


# --- JSON roundtrip with new types ---


def test_int64_json_roundtrip():
    """int64 survives JSON serialization roundtrip."""
    wkt = make_wkt(
        wkt_duration=datetime.timedelta(seconds=30),
        wkt_int64=9007199254740993,
        wkt_uint64=9007199254740993,
    )
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wkt_int64 == 9007199254740993
    assert wkt2.wkt_uint64 == 9007199254740993


def test_timestamp_json_roundtrip():
    """Timestamp survives JSON serialization roundtrip."""
    ts = datetime.datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=datetime.timezone.utc)
    wkt = make_wkt(wkt_timestamp=ts, wkt_duration=datetime.timedelta(seconds=30))
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wkt_timestamp == ts


def test_duration_json_roundtrip():
    """Duration survives JSON serialization roundtrip."""
    dur = datetime.timedelta(seconds=3, milliseconds=500)
    wkt = make_wkt(wkt_duration=dur)
    json_str = wkt.model_dump_json()
    wkt2 = WellKnownTypes.model_validate_json(json_str)
    assert wkt2.wkt_duration == dur
