"""Boundary values and edge case tests for generated models."""

import datetime

import pytest

from api.v1.collections_pydantic import Collections
from api.v1.known_types_pydantic import WellKnownTypes
from api.v1.scalars_pydantic import Scalars


# --- Integer boundary values ---

INT32_MAX = 2**31 - 1
INT32_MIN = -(2**31)
INT64_MAX = 2**63 - 1
INT64_MIN = -(2**63)
UINT32_MAX = 2**32 - 1
UINT64_MAX = 2**64 - 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("int32", INT32_MAX),
        ("int32", INT32_MIN),
        ("int64", INT64_MAX),
        ("int64", INT64_MIN),
        ("uint32", UINT32_MAX),
        ("uint64", UINT64_MAX),
        ("fixed32", UINT32_MAX),
        ("fixed64", UINT64_MAX),
    ],
)
def test_integer_boundary_values(field, value):
    s = Scalars(**{field: value})
    assert getattr(s, field) == value


# --- int64 string coercion ---


def test_int64_accepts_string():
    """int64 fields accept string input (from JSON systems)."""
    wkt = WellKnownTypes(
        wkt_timestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        wkt_duration=datetime.timedelta(0),
        wkt_int64="9007199254740993",
    )
    assert wkt.wkt_int64 == 9007199254740993


# --- Empty strings and bytes ---


def test_empty_string_as_map_key():
    c = Collections(string_map_key={"": "empty_key"})
    assert c.string_map_key[""] == "empty_key"


def test_empty_bytes():
    s = Scalars(bytes_=b"")
    assert s.bytes_ == b""


# --- Negative duration ---


def test_negative_duration():
    wkt = WellKnownTypes(
        wkt_timestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        wkt_duration=datetime.timedelta(seconds=-5),
    )
    assert wkt.wkt_duration.total_seconds() == -5


# --- Naive datetime handling ---


def test_naive_datetime_accepted():
    """Pydantic accepts naive datetimes (no timezone)."""
    naive_dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
    wkt = WellKnownTypes(wkt_timestamp=naive_dt)
    assert wkt.wkt_timestamp.year == 2024


# --- Large repeated field ---


def test_large_repeated_field():
    values = list(range(1000))
    c = Collections(int32_repeated=values)
    assert len(c.int32_repeated) == 1000
    assert c.int32_repeated[999] == 999
