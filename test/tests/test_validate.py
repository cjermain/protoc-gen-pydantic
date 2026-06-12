from pathlib import Path

import pytest
from pydantic import ValidationError

import datetime
from datetime import datetime as _dt_datetime
from datetime import timedelta, timezone

from api.v1.validate_pydantic import (
    ValidatedBytes,
    ValidatedBytesIP,
    ValidatedCEL,
    ValidatedCELAll,
    ValidatedCELBool,
    ValidatedCELBytes,
    ValidatedCELCastDouble,
    ValidatedCELCastInt,
    ValidatedCELCastString,
    ValidatedCELCastUint,
    ValidatedCELContains,
    ValidatedCELEndsWith,
    ValidatedCELEnum,
    ValidatedCELFloatLiteral,
    ValidatedCELGlobalSize,
    ValidatedCELIndex,
    ValidatedCELInList,
    ValidatedCELIsInfDir,
    ValidatedCELIsIpPrefixV6,
    ValidatedCELMapField,
    ValidatedCELMapLiteral,
    ValidatedCELNegate,
    ValidatedCELNullCheck,
    ValidatedCELTsDate,
    ValidatedCELTsMinutes,
    ValidatedCELTsSeconds,
    ValidatedCELUint,
    ValidatedCELCrossField,
    ValidatedCELDropped,
    ValidatedCELExists,
    ValidatedCELExistsOne,
    ValidatedCELField,
    ValidatedCELFilter,
    ValidatedCELHas,
    ValidatedCELIsEmail,
    ValidatedCELIsHostAndPort,
    ValidatedCELIsHostname,
    ValidatedCELIsIp,
    ValidatedCELIsIpPrefix,
    ValidatedCELIsNanInf,
    ValidatedCELIsUri,
    ValidatedCELDurGetHours,
    ValidatedCELDurGetMillis,
    ValidatedCELDurGetMinutes,
    ValidatedCELDurGetSeconds,
    ValidatedCELDuration,
    ValidatedCELDurationRange,
    ValidatedCELMapAll,
    ValidatedCELMessage,
    ValidatedCELMessageAll,
    ValidatedCELStillDropped,
    ValidatedCELStringReturn,
    ValidatedCELTimestamp,
    ValidatedCELTimestampAfter,
    ValidatedCELTimestampWindow,
    ValidatedCELTsDayOfMonth,
    ValidatedCELTsDayOfWeek,
    ValidatedCELTsDayOfYear,
    ValidatedCELTsHours,
    ValidatedCELTsHoursTZ,
    ValidatedCELTsHoursUTC,
    ValidatedCELTsMillis,
    ValidatedCELTsMonth,
    ValidatedCELTsYear,
    ValidatedConst,
    ValidatedConstOptional,
    ValidatedDropped,
    ValidatedDuration,
    ValidatedExamples,
    ValidatedFinite,
    ValidatedFloatExamples,
    ValidatedFloatIn,
    ValidatedFormats,
    ValidatedFormatsExtended,
    ValidatedIn,
    ValidatedMap,
    ValidatedMapConstraints,
    ValidatedNotContains,
    ValidatedOneof,
    ValidatedOneofFormat,
    ValidatedRepeated,
    ValidatedRepeatedItems,
    ValidatedReserved,
    ValidatedScalars,
    ValidatedStringAffix,
    ValidatedRequired,
    ValidatedStringContains,
    ValidatedStringLen,
    ValidatedStrings,
    ValidatedTimestamp,
    ValidatedUnique,
    ValidatedWellKnownRegex,
    ValidatedIgnore,
    ValidatedStringBytes,
    ValidatedCELExprField,
    ValidatedCELExprFieldString,
    ValidatedCELExprFieldMulti,
    ValidatedCELExprMessage,
    ValidatedCELExprMessageMulti,
    ValidatedCELExprFieldDropped,
    ValidatedCELExprMessageDropped,
    ValidatedCELInsideItems,
    ValidatedCELInsideMapValues,
    ValidatedCELEnumField,
    ValidatedCELEnumAliased,
    ValidatedCELReservedName,
)


# Minimum valid kwargs for messages where multiple fields became ConstrainedRequired.
_VALID_FORMATS = dict(
    email="user@example.com",
    website="https://example.com",
    address="1.2.3.4",
    token="550e8400-e29b-41d4-a716-446655440000",
    host_v4="1.2.3.4",
    host_v6="::1",
)
_VALID_FORMATS_EXT = dict(
    hostname="example.com",
    uri_ref="https://example.com",
    addr="example.com",
    tuuid="550e8400e29b41d4a716446655440000",
    ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    cidr="192.168.0.1/24",
    cidr_v4="192.168.0.1/24",
    cidr_v6="::1/128",
    ip_net="192.168.0.0/24",
    ipv4_net="192.168.0.0/24",
    ipv6_net="2001:db8::/32",
    endpoint="example.com:80",
)
_VALID_WKR = dict(
    header_name="Content-Type",
    header_value="application/json",
    loose_header="Content-Type",
)
_VALID_IN = dict(status="active", priority=1, limit=10)
_VALID_AFFIX = dict(
    url="https://example.com",
    filename="main.go",
    path="/home/user/notes.txt",
    content="abc",
    report="report_2024",
    notes="abcnote",
)
_VALID_BYTES = dict(
    token=b"x" * 16,
    hash=b"x" * 32,
    uuid=b"\x55\x0e\x84\x00\xe2\x9b\x41\xd4\xa7\x16\x44\x66\x55\x44\x00\x00",
)
_VALID_CONTAINS = dict(topic="protobuf guide", label="env-prod-us")
_VALID_STR_BYTES = dict(payload="x", token="a" * 32, tag="ab")

# ---------------------------------------------------------------------------
# ValidatedScalars
# ---------------------------------------------------------------------------


def test_validated_scalars_required():
    # age (gt=0), priority (gt=0), rank (ge=1) are ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedScalars()


def test_validated_scalars_valid():
    s = ValidatedScalars(age=1, score=50.0, priority=1, ratio=0.5, rank=5)
    assert s.age == 1
    assert s.score == 50.0
    assert s.priority == 1
    assert s.ratio == pytest.approx(0.5)
    assert s.rank == 5


def test_validated_scalars_boundary_values():
    # age: gt=0, le=150  → 1 and 150 are valid
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.age == 1
    s = ValidatedScalars(age=150, score=100.0, priority=1, ratio=0.0, rank=10)
    assert s.age == 150

    # score: ge=0.0, le=100.0
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.score == 0.0
    s = ValidatedScalars(age=1, score=100.0, priority=1, ratio=0.0, rank=1)
    assert s.score == 100.0

    # ratio: ge=0.0, lt=1.0 → 0.0 valid, 1.0 invalid
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.ratio == 0.0

    # rank: ge=1, le=10
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.rank == 1
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=10)
    assert s.rank == 10


def test_validated_scalars_age_gt_zero():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=0, score=50.0, priority=1, ratio=0.5, rank=5)


def test_validated_scalars_age_exceeds_max():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=151, score=50.0, priority=1, ratio=0.5, rank=5)


def test_validated_scalars_score_below_min():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=-0.1, priority=1, ratio=0.5, rank=5)


def test_validated_scalars_score_exceeds_max():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=100.1, priority=1, ratio=0.5, rank=5)


def test_validated_scalars_priority_must_be_positive():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=50.0, priority=0, ratio=0.5, rank=5)


def test_validated_scalars_ratio_below_min():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=50.0, priority=1, ratio=-0.1, rank=5)


def test_validated_scalars_ratio_at_upper_bound():
    # lt=1.0 means 1.0 is invalid
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=50.0, priority=1, ratio=1.0, rank=5)


def test_validated_scalars_rank_below_min():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=50.0, priority=1, ratio=0.5, rank=0)


def test_validated_scalars_rank_exceeds_max():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=50.0, priority=1, ratio=0.5, rank=11)


# ---------------------------------------------------------------------------
# ValidatedStrings
# ---------------------------------------------------------------------------


def test_validated_strings_required():
    # name (min_len=1), code (pattern), tag (min_len=2) are ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedStrings()


def test_validated_strings_valid():
    s = ValidatedStrings(name="Alice", code="ABC", bio="Some bio", tag="ok")
    assert s.name == "Alice"
    assert s.code == "ABC"
    assert s.bio == "Some bio"
    assert s.tag == "ok"


def test_validated_strings_name_min_length():
    # name: min_length=1 → empty string fails
    with pytest.raises(ValidationError):
        ValidatedStrings(name="", code="ABC", bio="bio", tag="ok")


def test_validated_strings_name_max_length():
    with pytest.raises(ValidationError):
        ValidatedStrings(name="a" * 101, code="ABC", bio="bio", tag="ok")


def test_validated_strings_name_boundary():
    # Exactly 1 char (min) and 100 chars (max) are valid
    ValidatedStrings(name="a", code="ABC", bio="bio", tag="ok")
    ValidatedStrings(name="a" * 100, code="ABC", bio="bio", tag="ok")


def test_validated_strings_code_pattern():
    # code: pattern="^[A-Z]+$" — lowercase fails
    with pytest.raises(ValidationError):
        ValidatedStrings(name="Alice", code="abc", bio="bio", tag="ok")


def test_validated_strings_code_pattern_valid():
    ValidatedStrings(name="Alice", code="HELLO", bio="bio", tag="ok")


def test_validated_strings_bio_max_length():
    with pytest.raises(ValidationError):
        ValidatedStrings(name="Alice", code="ABC", bio="x" * 501, tag="ok")


def test_validated_strings_bio_boundary():
    # Exactly 500 chars is valid
    ValidatedStrings(name="Alice", code="ABC", bio="x" * 500, tag="ok")


def test_validated_strings_tag_min_length():
    with pytest.raises(ValidationError):
        ValidatedStrings(name="Alice", code="ABC", bio="bio", tag="x")


def test_validated_strings_tag_boundary():
    # Exactly 2 chars (min) is valid
    ValidatedStrings(name="Alice", code="ABC", bio="bio", tag="xy")


# ---------------------------------------------------------------------------
# ValidatedRepeated
# ---------------------------------------------------------------------------


def test_validated_repeated_valid():
    r = ValidatedRepeated(items=["a", "b"], tags=["x"])
    assert r.items == ["a", "b"]
    assert r.tags == ["x"]


def test_validated_repeated_items_empty_fails():
    # items: min_length=1
    with pytest.raises(ValidationError):
        ValidatedRepeated(items=[], tags=["x"])


def test_validated_repeated_items_too_many():
    # items: max_length=10
    with pytest.raises(ValidationError):
        ValidatedRepeated(items=["x"] * 11, tags=["x"])


def test_validated_repeated_items_boundary():
    # 1 item (min) and 10 items (max) are valid
    ValidatedRepeated(items=["a"], tags=["x"])
    ValidatedRepeated(items=["a"] * 10, tags=["x"])


def test_validated_repeated_tags_empty_fails():
    # tags: min_length=1
    with pytest.raises(ValidationError):
        ValidatedRepeated(items=["a"], tags=[])


# ---------------------------------------------------------------------------
# ValidatedMap
# ---------------------------------------------------------------------------


def test_validated_map_valid():
    m = ValidatedMap(labels={"k": "v"})
    assert m.labels == {"k": "v"}


def test_validated_map_empty_fails():
    with pytest.raises(ValidationError):
        ValidatedMap(labels={})


def test_validated_map_too_many():
    with pytest.raises(ValidationError):
        ValidatedMap(labels={str(i): str(i) for i in range(11)})


def test_validated_map_boundary():
    ValidatedMap(labels={"a": "1"})
    ValidatedMap(labels={str(i): str(i) for i in range(10)})


# ---------------------------------------------------------------------------
# ValidatedScalars — uint64 and sint32 optional fields (item 11)
# ---------------------------------------------------------------------------


def test_validated_scalars_count_valid():
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1, count=1)
    assert s.count == 1


def test_validated_scalars_count_zero_fails():
    # uint64 gt=0 — zero is rejected
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1, count=0)


def test_validated_scalars_count_omitted():
    # optional — can be omitted; None does not trigger the constraint
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.count is None


def test_validated_scalars_offset_valid():
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1, offset=0)
    assert s.offset == 0


def test_validated_scalars_offset_negative_fails():
    # sint32 gte=0 — negative is rejected
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1, offset=-1)


def test_validated_scalars_offset_omitted():
    # optional — can be omitted; None does not trigger the constraint
    s = ValidatedScalars(age=1, score=0.0, priority=1, ratio=0.0, rank=1)
    assert s.offset is None


# ---------------------------------------------------------------------------
# ValidatedReserved — alias + constraint combination (item 10)
# ---------------------------------------------------------------------------


def test_validated_reserved_alias_and_constraint():
    r = ValidatedReserved(float_=1.0)
    assert r.float_ == pytest.approx(1.0)


def test_validated_reserved_alias_construction():
    # alias allows construction with the original proto name
    r = ValidatedReserved(**{"float": 1.0})
    assert r.float_ == pytest.approx(1.0)


def test_validated_reserved_constraint_enforced():
    with pytest.raises(ValidationError):
        ValidatedReserved(float_=0.0)


# ---------------------------------------------------------------------------
# ValidatedDropped — dropped constraints are not enforced; comments are emitted
# ---------------------------------------------------------------------------

_GEN_VALIDATE = (
    Path(__file__).parent.parent / "gen" / "api" / "v1" / "validate_pydantic.py"
)


def test_validated_dropped_required_not_enforced():
    # required = true is not translated (stays as dropped comment); name has no extra
    # Pydantic constraint so it keeps its zero default "".
    d = ValidatedDropped(score=1)
    assert d.name == ""


def test_validated_dropped_bytes_const_not_enforced():
    # bytes.const is not translated (bytes kind unsupported); any bytes value is accepted.
    d = ValidatedDropped(score=1, blob=b"\xff")
    assert d.blob == b"\xff"


def test_validated_dropped_comments_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: required (not translated)" in text
    assert "# buf.validate: const (not translated)" in text


def test_validated_dropped_combined_constraint_valid():
    # score has both gt=0 (translated) and required=true (dropped).
    # A positive value satisfies the Pydantic constraint.
    d = ValidatedDropped(score=1)
    assert d.score == 1


def test_validated_dropped_combined_constraint_enforced():
    # The translatable gt=0 constraint IS enforced even though required is dropped.
    with pytest.raises(ValidationError):
        ValidatedDropped(score=0)


def test_validated_dropped_combined_comment_in_generated_file():
    # Both the Pydantic arg and the dropped-constraint comment appear for score.
    text = _GEN_VALIDATE.read_text()
    assert "gt=0," in text
    assert "# buf.validate: required (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedOneof — comment + oneof + constraint triple combination (item 12)
# ---------------------------------------------------------------------------


def test_validated_oneof_valid_small():
    v = ValidatedOneof(small=1)
    assert v.small == 1


def test_validated_oneof_valid_large():
    v = ValidatedOneof(large=1)
    assert v.large == 1


def test_validated_oneof_constraint_enforced():
    with pytest.raises(ValidationError):
        ValidatedOneof(small=0)


def test_validated_oneof_description_contains_comment_and_oneof():
    field_info = ValidatedOneof.model_fields["small"]
    assert "Must be positive when set" in field_info.description
    assert "oneof" in field_info.description


def test_validated_oneof_exclusivity():
    with pytest.raises(ValidationError, match="oneof 'value'"):
        ValidatedOneof(small=1, large=2)


# ---------------------------------------------------------------------------
# JSON roundtrip
# ---------------------------------------------------------------------------


def test_validated_scalars_priority_string_input_valid():
    """ProtoJSON sends int64 as a string; constraint must still apply."""
    s = ValidatedScalars(age=1, score=0.0, priority="5", ratio=0.0, rank=1)
    assert s.priority == 5


def test_validated_scalars_priority_string_input_invalid():
    with pytest.raises(ValidationError):
        ValidatedScalars(age=1, score=0.0, priority="0", ratio=0.0, rank=1)


def test_validated_scalars_json_roundtrip():
    s = ValidatedScalars(age=42, score=75.5, priority=10, ratio=0.25, rank=7)
    json_str = s.model_dump_json()
    s2 = ValidatedScalars.model_validate_json(json_str)
    assert s2.age == s.age
    assert s2.score == pytest.approx(s.score)
    assert s2.priority == s.priority
    assert s2.ratio == pytest.approx(s.ratio)
    assert s2.rank == s.rank


# ---------------------------------------------------------------------------
# gen_options build — constraints are preserved under non-default plugin options
# ---------------------------------------------------------------------------

_GEN_OPTIONS_VALIDATE = Path(__file__).parent.parent / "gen_options" / "api" / "v1"


@pytest.fixture(scope="module")
def opts_validate(load_module):
    return load_module(
        "validate_pydantic", _GEN_OPTIONS_VALIDATE / "validate_pydantic.py"
    )


def test_gen_options_scalars_constraints_enforced(opts_validate):
    VS = opts_validate.ValidatedScalars
    VS(age=1, score=0.0, priority=1, ratio=0.0, rank=1)  # valid
    with pytest.raises(Exception):  # ValidationError
        VS(age=0, score=0.0, priority=1, ratio=0.0, rank=1)


def test_gen_options_strings_constraints_enforced(opts_validate):
    VS = opts_validate.ValidatedStrings
    VS(name="a", code="A", bio="", tag="ab")
    with pytest.raises(Exception):  # ValidationError
        VS(name="", code="A", bio="", tag="ab")


def test_gen_options_repeated_constraints_enforced(opts_validate):
    VR = opts_validate.ValidatedRepeated
    VR(items=["x"], tags=["y"])
    with pytest.raises(Exception):  # ValidationError
        VR(items=[], tags=["y"])


def test_gen_options_map_constraints_enforced(opts_validate):
    VM = opts_validate.ValidatedMap
    VM(labels={"k": "v"})
    with pytest.raises(Exception):  # ValidationError
        VM(labels={})


# ---------------------------------------------------------------------------
# ValidatedDuration / ValidatedTimestamp — no panic on message-typed bounds
# ---------------------------------------------------------------------------


def test_validated_duration_accepts_timedelta():
    # Duration bounds (gt, lte) are dropped; any timedelta is accepted.
    d = ValidatedDuration(timeout=datetime.timedelta(seconds=30))
    assert d.timeout == datetime.timedelta(seconds=30)


def test_validated_duration_accepts_none():
    # Field is optional (message type), so None is valid.
    d = ValidatedDuration()
    assert d.timeout is None


def test_validated_duration_comments_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    # Both bounds appear as dropped-constraint comments, not as Field() kwargs.
    assert "# buf.validate: gt (not translated)" in text
    assert "# buf.validate: lte (not translated)" in text
    # No Pydantic bound args are emitted for the duration field.
    assert "class ValidatedDuration" in text


def test_validated_timestamp_accepts_datetime():
    # Timestamp bounds (gt) are dropped; any datetime is accepted.
    ts = ValidatedTimestamp(
        created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    )
    assert ts.created_at == datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)


def test_validated_timestamp_accepts_none():
    ts = ValidatedTimestamp()
    assert ts.created_at is None


def test_validated_timestamp_comments_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "class ValidatedTimestamp" in text
    # The timestamp gt bound also appears as a dropped comment.
    # (The string "gt (not translated)" already checked by duration test above.)


# ---------------------------------------------------------------------------
# ValidatedFormats — format validators enforced via _AfterValidator (P3)
# ---------------------------------------------------------------------------


def test_validated_format_defaults():
    # Format-validator fields (email, website, address, token, host_v4, host_v6) are now
    # ConstrainedRequired — zero-arg construction raises ValidationError.
    with pytest.raises(ValidationError):
        ValidatedFormats()
    # ratio (finite validator) is NOT ConstrainedRequired: 0.0 passes float.finite.
    d = ValidatedFormats(**_VALID_FORMATS)
    assert d.ratio == pytest.approx(0.0)


def test_validated_format_finite_enforced_inf():
    with pytest.raises(ValidationError):
        ValidatedFormats(**_VALID_FORMATS, ratio=float("inf"))


def test_validated_format_finite_enforced_nan():
    with pytest.raises(ValidationError):
        ValidatedFormats(**_VALID_FORMATS, ratio=float("nan"))


def test_validated_format_finite_valid():
    d = ValidatedFormats(**_VALID_FORMATS, ratio=1.0)
    assert d.ratio == pytest.approx(1.0)


@pytest.mark.parametrize("email", ["user@example.com", "a@b.co", "x.y+z@domain.org"])
def test_validated_format_email_valid(email):
    d = ValidatedFormats(**{**_VALID_FORMATS, "email": email})
    assert d.email == email


@pytest.mark.parametrize("email", ["notanemail", "@domain.com", "user@", "nodot@nodot"])
def test_validated_format_email_invalid(email):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "email": email})


@pytest.mark.parametrize("uri", ["https://example.com", "http://x.org/path?q=1"])
def test_validated_format_uri_valid(uri):
    d = ValidatedFormats(**{**_VALID_FORMATS, "website": uri})
    assert d.website == uri


@pytest.mark.parametrize("uri", ["notauri", "example.com", "ftp//missing-colon"])
def test_validated_format_uri_invalid(uri):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "website": uri})


@pytest.mark.parametrize("addr", ["1.2.3.4", "::1", "2001:db8::1"])
def test_validated_format_ip_valid(addr):
    d = ValidatedFormats(**{**_VALID_FORMATS, "address": addr})
    assert d.address == addr


@pytest.mark.parametrize("addr", ["999.0.0.1", "not-an-ip", "256.1.1.1"])
def test_validated_format_ip_invalid(addr):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "address": addr})


@pytest.mark.parametrize("v4", ["192.168.1.1", "0.0.0.0", "255.255.255.255"])
def test_validated_format_ipv4_valid(v4):
    d = ValidatedFormats(**{**_VALID_FORMATS, "host_v4": v4})
    assert d.host_v4 == v4


@pytest.mark.parametrize("v4", ["::1", "not-an-ip", "256.0.0.1"])
def test_validated_format_ipv4_invalid(v4):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "host_v4": v4})


@pytest.mark.parametrize("v6", ["::1", "2001:db8::1", "fe80::1"])
def test_validated_format_ipv6_valid(v6):
    d = ValidatedFormats(**{**_VALID_FORMATS, "host_v6": v6})
    assert d.host_v6 == v6


@pytest.mark.parametrize("v6", ["1.2.3.4", "not-an-ip", "gggg::1"])
def test_validated_format_ipv6_invalid(v6):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "host_v6": v6})


@pytest.mark.parametrize(
    "u",
    [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    ],
)
def test_validated_format_uuid_valid(u):
    d = ValidatedFormats(**{**_VALID_FORMATS, "token": u})
    assert d.token == u


@pytest.mark.parametrize(
    "u", ["not-a-uuid", "12345", "550e8400-zzzz-41d4-a716-446655440000"]
)
def test_validated_format_uuid_invalid(u):
    with pytest.raises(ValidationError):
        ValidatedFormats(**{**_VALID_FORMATS, "token": u})


# ---------------------------------------------------------------------------
# ValidatedStringLen — string.len → min_length=N, max_length=N (P2)
# ---------------------------------------------------------------------------


def test_validated_string_len_required():
    # code (min_len=5 via len=5) is ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedStringLen()


def test_validated_string_len_exact_length_valid():
    m = ValidatedStringLen(code="hello")
    assert m.code == "hello"


def test_validated_string_len_too_short():
    with pytest.raises(ValidationError):
        ValidatedStringLen(code="hi")


def test_validated_string_len_too_long():
    with pytest.raises(ValidationError):
        ValidatedStringLen(code="toolong")


def test_validated_string_len_boundary():
    # Exactly 5 chars is the only valid length.
    ValidatedStringLen(code="abcde")
    with pytest.raises(ValidationError):
        ValidatedStringLen(code="abcd")
    with pytest.raises(ValidationError):
        ValidatedStringLen(code="abcdef")


# ---------------------------------------------------------------------------
# ValidatedStringAffix — prefix/suffix → pattern (P2)
# ---------------------------------------------------------------------------


def test_validated_string_affix_required():
    # All six affix fields produce patterns — all are ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedStringAffix()


def test_validated_string_affix_prefix_valid():
    m = ValidatedStringAffix(**{**_VALID_AFFIX, "url": "https://example.com"})
    assert m.url == "https://example.com"


def test_validated_string_affix_prefix_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "url": "http://example.com"})


def test_validated_string_affix_suffix_valid():
    m = ValidatedStringAffix(**{**_VALID_AFFIX, "filename": "main.go"})
    assert m.filename == "main.go"


def test_validated_string_affix_suffix_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "filename": "main.py"})


def test_validated_string_affix_prefix_and_suffix_valid():
    m = ValidatedStringAffix(**{**_VALID_AFFIX, "path": "/home/user/notes.txt"})
    assert m.path == "/home/user/notes.txt"


def test_validated_string_affix_prefix_and_suffix_invalid_prefix():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "path": "/tmp/notes.txt"})


def test_validated_string_affix_prefix_and_suffix_invalid_suffix():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "path": "/home/user/notes.py"})


def test_validated_string_affix_conflict_pattern_wins():
    # content has both pattern and prefix; pattern is translated, prefix is dropped.
    # The explicit pattern ^[a-z]+$ is enforced.
    ValidatedStringAffix(**{**_VALID_AFFIX, "content": "abc"})
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "content": "ABC"})


def test_validated_string_affix_conflict_comment_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: prefix (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedExamples — field examples annotation (P2)
# ---------------------------------------------------------------------------


def test_validated_examples_valid():
    m = ValidatedExamples(count=5, name="alice")
    assert m.count == 5
    assert m.name == "alice"


def test_validated_examples_constraint_still_enforced():
    # examples= does not affect validation; gt=0 is still enforced.
    with pytest.raises(ValidationError):
        ValidatedExamples(count=0, name="alice")


def test_validated_examples_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "examples=[1, 42]" in text
    assert 'examples=["alice", "bob"]' in text


# ---------------------------------------------------------------------------
# ValidatedConst — const constraint translated to Literal[...]
# ---------------------------------------------------------------------------


def test_validated_const_tag_enforced():
    with pytest.raises(ValidationError):
        ValidatedConst(tag="other")


def test_validated_const_tag_default():
    m = ValidatedConst()
    assert m.tag == "fixed"


def test_validated_const_count_enforced():
    with pytest.raises(ValidationError):
        ValidatedConst(count=99)


def test_validated_const_count_default():
    m = ValidatedConst()
    assert m.count == 42


def test_validated_const_active_default():
    m = ValidatedConst()
    assert m.active is True


def test_validated_const_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert '_Literal["fixed"]' in text


def test_validated_const_score_default():
    m = ValidatedConst()
    assert m.score == pytest.approx(3.14)


def test_validated_const_score_valid():
    m = ValidatedConst(score=3.14)
    assert m.score == pytest.approx(3.14)


def test_validated_const_score_enforced():
    with pytest.raises(ValidationError):
        ValidatedConst(score=9.9)


# ---------------------------------------------------------------------------
# ValidatedIn — in and not_in constraints translated to AfterValidator
# ---------------------------------------------------------------------------


def test_validated_in_status_valid():
    m = ValidatedIn(**{**_VALID_IN, "status": "active"})
    assert m.status == "active"


def test_validated_in_status_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(**{**_VALID_IN, "status": "banned"})


def test_validated_in_not_in_code_valid():
    m = ValidatedIn(**_VALID_IN, code="approved")
    assert m.code == "approved"


def test_validated_in_not_in_code_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(**_VALID_IN, code="deleted")


def test_validated_in_priority_valid():
    m = ValidatedIn(**{**_VALID_IN, "priority": 1})
    assert m.priority == 1


def test_validated_in_priority_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(**{**_VALID_IN, "priority": 5})


def test_validated_in_required():
    # status, priority, limit are now ConstrainedRequired (zero values not in allowed set).
    with pytest.raises(ValidationError):
        ValidatedIn()


# ---------------------------------------------------------------------------
# ValidatedUnique — repeated.unique translated to AfterValidator
# ---------------------------------------------------------------------------


def test_validated_unique_tags_valid():
    m = ValidatedUnique(tags=["a", "b", "c"])
    assert m.tags == ["a", "b", "c"]


def test_validated_unique_tags_duplicates():
    with pytest.raises(ValidationError):
        ValidatedUnique(tags=["a", "a"])


def test_validated_unique_empty_allowed():
    m = ValidatedUnique(tags=[])
    assert m.tags == []


def test_validated_unique_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "_AfterValidator(_require_unique)" in text


# ---------------------------------------------------------------------------
# ValidatedStringContains — string.contains → pattern (unanchored regex)
# ---------------------------------------------------------------------------


def test_validated_string_contains_required():
    # topic (pattern from contains) and label (pattern from prefix) are ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedStringContains()


def test_validated_string_contains_topic_valid():
    m = ValidatedStringContains(**{**_VALID_CONTAINS, "topic": "protobuf guide"})
    assert m.topic == "protobuf guide"


def test_validated_string_contains_topic_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringContains(**{**_VALID_CONTAINS, "topic": "avro guide"})


def test_validated_string_contains_label_prefix_only():
    # prefix is used; contains conflicts with prefix and is dropped
    m = ValidatedStringContains(**{**_VALID_CONTAINS, "label": "env-prod-us"})
    assert m.label == "env-prod-us"


def test_validated_string_contains_label_dropped_comment():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: contains (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedBytes — bytes min_len / len / max_len → min_length / max_length
# ---------------------------------------------------------------------------


def test_validated_bytes_required():
    # token (min_len=16), hash (min_len=32), uuid (bytes_uuid format) are ConstrainedRequired.
    with pytest.raises(ValidationError):
        ValidatedBytes()


def test_validated_bytes_token_valid():
    m = ValidatedBytes(**{**_VALID_BYTES, "token": b"x" * 16})
    assert m.token == b"x" * 16


def test_validated_bytes_token_too_short():
    with pytest.raises(ValidationError):
        ValidatedBytes(**{**_VALID_BYTES, "token": b"short"})


def test_validated_bytes_hash_exact():
    # `hash` is a Python builtin → renamed to `hash_` with alias
    m = ValidatedBytes(**{**_VALID_BYTES, "hash": b"x" * 32})
    assert m.hash_ == b"x" * 32


def test_validated_bytes_hash_wrong_length():
    with pytest.raises(ValidationError):
        ValidatedBytes(**{**_VALID_BYTES, "hash": b"x" * 31})


def test_validated_bytes_payload_valid():
    m = ValidatedBytes(**_VALID_BYTES, payload=b"x" * 1024)
    assert m.payload == b"x" * 1024


def test_validated_bytes_payload_too_large():
    with pytest.raises(ValidationError):
        ValidatedBytes(**_VALID_BYTES, payload=b"x" * 1025)


# ---------------------------------------------------------------------------
# ValidatedRequired — required = true on proto3 optional scalar fields
# ---------------------------------------------------------------------------


def test_validated_required_optional_scalar_is_required():
    # required_name and required_score have no default; omitting them raises.
    with pytest.raises(ValidationError):
        ValidatedRequired(plain_name="x")


def test_validated_required_optional_scalar_accepts_value():
    r = ValidatedRequired(required_name="alice", required_score=1)
    assert r.required_name == "alice"
    assert r.required_score == 1


def test_validated_required_score_constraint_enforced():
    # gt=0 still enforced after required stripping.
    with pytest.raises(ValidationError):
        ValidatedRequired(required_name="alice", required_score=0)


def test_validated_required_detail_accepts_none():
    # Message-typed required: not translated; field still accepts None.
    r = ValidatedRequired(required_name="alice", required_score=1)
    assert r.required_detail is None


def test_validated_required_plain_scalar_accepts_default():
    # Plain scalar required: not translated; default "" is accepted.
    r = ValidatedRequired(required_name="alice", required_score=1)
    assert r.plain_name == ""


def test_validated_required_annotations_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    # Scalars use unquoted annotations; user-defined types (messages/enums) remain quoted.
    assert "required_name: str" in text
    assert 'required_detail: "ValidatedRequired.Detail | None"' in text
    assert "# buf.validate: required (not translated)" in text


def test_validated_required_field_is_required_in_pydantic():
    assert ValidatedRequired.model_fields["required_name"].is_required()
    assert ValidatedRequired.model_fields["required_score"].is_required()
    assert not ValidatedRequired.model_fields["plain_name"].is_required()


# ---------------------------------------------------------------------------
# ValidatedIn — uint32.in (uint path in formatScalarLiteral)
# ---------------------------------------------------------------------------


def test_validated_in_limit_valid():
    m = ValidatedIn(**{**_VALID_IN, "limit": 10})
    assert m.limit == 10


def test_validated_in_limit_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(**{**_VALID_IN, "limit": 99})


def test_validated_in_limit_boundary():
    ValidatedIn(**{**_VALID_IN, "limit": 50})
    ValidatedIn(**{**_VALID_IN, "limit": 100})
    with pytest.raises(ValidationError):
        ValidatedIn(**{**_VALID_IN, "limit": 1})


# ---------------------------------------------------------------------------
# ValidatedStringAffix — pattern+suffix conflict and pattern+contains conflict
# ---------------------------------------------------------------------------


def test_validated_string_affix_pattern_suffix_conflict_pattern_enforced():
    # report: pattern="^report_" wins; suffix=".csv" is dropped.
    ValidatedStringAffix(**{**_VALID_AFFIX, "report": "report_2024.csv"})
    ValidatedStringAffix(
        **{**_VALID_AFFIX, "report": "report_2024.txt"}
    )  # suffix not enforced
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "report": "other_2024"})


def test_validated_string_affix_pattern_suffix_conflict_comment():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: suffix (not translated)" in text


def test_validated_string_affix_pattern_contains_conflict_pattern_enforced():
    # notes: pattern="^[a-z]+$" wins; contains="note" is dropped.
    ValidatedStringAffix(**{**_VALID_AFFIX, "notes": "abcnote"})
    with pytest.raises(ValidationError):
        ValidatedStringAffix(**{**_VALID_AFFIX, "notes": "ABC"})


# ---------------------------------------------------------------------------
# ValidatedFinite — float.finite and double.finite constraints
# ---------------------------------------------------------------------------


def test_validated_finite_ratio_valid():
    m = ValidatedFinite(ratio=1.0)
    assert m.ratio == pytest.approx(1.0)


def test_validated_finite_ratio_inf():
    with pytest.raises(ValidationError):
        ValidatedFinite(ratio=float("inf"))


def test_validated_finite_ratio_nan():
    with pytest.raises(ValidationError):
        ValidatedFinite(ratio=float("nan"))


def test_validated_finite_value_valid():
    m = ValidatedFinite(value=3.14)
    assert m.value == pytest.approx(3.14)


def test_validated_finite_value_inf():
    with pytest.raises(ValidationError):
        ValidatedFinite(value=float("inf"))


# ---------------------------------------------------------------------------
# ValidatedOneofFormat — AfterValidator on a oneof field (wrapWithAnnotated)
# ---------------------------------------------------------------------------


def test_validated_oneof_format_email_valid():
    # Email AfterValidator works inside oneof.
    m = ValidatedOneofFormat(email_contact="user@example.com")
    assert m.email_contact == "user@example.com"


def test_validated_oneof_format_email_invalid():
    with pytest.raises(ValidationError):
        ValidatedOneofFormat(email_contact="notanemail")


def test_validated_oneof_format_phone_valid():
    # Phone field has no constraint; any string is accepted.
    m = ValidatedOneofFormat(phone_contact="+1-555-0100")
    assert m.phone_contact == "+1-555-0100"


def test_validated_oneof_format_both_raises():
    with pytest.raises(ValidationError, match="oneof 'contact'"):
        ValidatedOneofFormat(
            email_contact="user@example.com", phone_contact="+1-555-0100"
        )


def test_validated_oneof_format_annotation_in_generated_file():
    # The generated type for email_contact should use _Annotated + AfterValidator.
    text = _GEN_VALIDATE.read_text()
    assert "_validate_email" in text


# ---------------------------------------------------------------------------
# ValidatedConstOptional — const on a oneof field (ConstLiteral on optional)
# ---------------------------------------------------------------------------


def test_validated_const_optional_fixed_token_valid():
    m = ValidatedConstOptional(fixed_token="fixed")
    assert m.fixed_token == "fixed"


def test_validated_const_optional_fixed_token_invalid():
    with pytest.raises(ValidationError):
        ValidatedConstOptional(fixed_token="other")


def test_validated_const_optional_other_token_valid():
    m = ValidatedConstOptional(other_token="anything")
    assert m.other_token == "anything"


def test_validated_const_optional_both_raises():
    with pytest.raises(ValidationError, match="oneof 'token_type'"):
        ValidatedConstOptional(fixed_token="fixed", other_token="x")


def test_validated_const_optional_annotation_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "ValidatedConstOptional" in text


# ---------------------------------------------------------------------------
# ValidatedBytes — bytes.uuid (16-byte binary UUID)
# ---------------------------------------------------------------------------


def test_validated_bytes_uuid_valid():
    m = ValidatedBytes(**{**_VALID_BYTES, "uuid": b"\x00" * 16})
    assert m.uuid == b"\x00" * 16


def test_validated_bytes_uuid_empty_skips_validation():
    # Empty bytes is the proto3 zero value; validator is skipped.
    # uuid (bytes_uuid) is ConstrainedRequired, but empty bytes is accepted when provided.
    m = ValidatedBytes(**{**_VALID_BYTES, "uuid": b""})
    assert m.uuid == b""


def test_validated_bytes_uuid_too_short():
    with pytest.raises(ValidationError):
        ValidatedBytes(**{**_VALID_BYTES, "uuid": b"\x00" * 15})


def test_validated_bytes_uuid_too_long():
    with pytest.raises(ValidationError):
        ValidatedBytes(**{**_VALID_BYTES, "uuid": b"\x00" * 17})


# ---------------------------------------------------------------------------
# ValidatedFormatsExtended — new format validators (Tier 1)
# ---------------------------------------------------------------------------


def test_validated_formats_extended_defaults():
    # All format-validator fields are ConstrainedRequired — zero-arg construction fails.
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended()


@pytest.mark.parametrize(
    "host",
    ["example.com", "localhost", "sub.domain.example.co.uk", "xn--nxasmq6b.com"],
)
def test_validated_formats_extended_hostname_valid(host):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "hostname": host})
    assert m.hostname == host


@pytest.mark.parametrize(
    "host",
    ["-bad.com", "bad-.com", "label..double.dot", "has space.com", "123.456"],
)
def test_validated_formats_extended_hostname_invalid(host):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "hostname": host})


@pytest.mark.parametrize(
    "ref",
    ["/path/to/resource", "https://example.com/x?y=1", "../relative", "#fragment"],
)
def test_validated_formats_extended_uri_ref_valid(ref):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "uri_ref": ref})
    assert m.uri_ref == ref


@pytest.mark.parametrize("ref", ["has space", "line\nnewline", "tab\there"])
def test_validated_formats_extended_uri_ref_invalid(ref):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "uri_ref": ref})


@pytest.mark.parametrize("addr", ["1.2.3.4", "::1", "example.com", "localhost"])
def test_validated_formats_extended_address_valid(addr):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "addr": addr})
    assert m.addr == addr


@pytest.mark.parametrize("addr", ["-bad-host", "has space", "label..double"])
def test_validated_formats_extended_address_invalid(addr):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "addr": addr})


@pytest.mark.parametrize(
    "u",
    ["550e8400e29b41d4a716446655440000", "6ba7b8109dad11d180b400c04fd430c8"],
)
def test_validated_formats_extended_tuuid_valid(u):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "tuuid": u})
    assert m.tuuid == u


@pytest.mark.parametrize(
    "u",
    [
        "550e8400-e29b-41d4-a716-446655440000",  # has dashes
        "short",
        "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",  # non-hex
    ],
)
def test_validated_formats_extended_tuuid_invalid(u):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "tuuid": u})


@pytest.mark.parametrize(
    "u",
    ["01ARZ3NDEKTSV4RRFFQ69G5FAV", "7ZZZZZZZZZZZZZZZZZZZZZZZZZ"],
)
def test_validated_formats_extended_ulid_valid(u):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ulid": u})
    assert m.ulid == u


@pytest.mark.parametrize(
    "u",
    [
        "INVALID_CHARS!!!!!!!!!!!!!",  # invalid characters
        "TOOSHORT",  # too short
        "01ARZ3NDEKTSV4RRFFQ69G5FAVXX",  # too long
        "8ZZZZZZZZZZZZZZZZZZZZZZZZ",  # timestamp overflow (first char > 7)
    ],
)
def test_validated_formats_extended_ulid_invalid(u):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ulid": u})


@pytest.mark.parametrize(
    "cidr",
    ["192.168.0.1/24", "10.0.0.1/8", "::1/128", "2001:db8::1/32"],
)
def test_validated_formats_extended_ip_with_prefixlen_valid(cidr):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr": cidr})
    assert m.cidr == cidr


@pytest.mark.parametrize("cidr", ["not/valid", "1.2.3.4/33", "999.999.999.999/24"])
def test_validated_formats_extended_ip_with_prefixlen_invalid(cidr):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr": cidr})


@pytest.mark.parametrize("cidr", ["192.168.0.1/24", "10.0.0.0/8"])
def test_validated_formats_extended_ipv4_with_prefixlen_valid(cidr):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr_v4": cidr})
    assert m.cidr_v4 == cidr


@pytest.mark.parametrize("cidr", ["::1/128", "not-an-ip/24", "1.2.3.4/33"])
def test_validated_formats_extended_ipv4_with_prefixlen_invalid(cidr):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr_v4": cidr})


@pytest.mark.parametrize("cidr", ["::1/128", "2001:db8::1/32"])
def test_validated_formats_extended_ipv6_with_prefixlen_valid(cidr):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr_v6": cidr})
    assert m.cidr_v6 == cidr


@pytest.mark.parametrize("cidr", ["192.168.0.1/24", "not-an-ip/32", "::1/129"])
def test_validated_formats_extended_ipv6_with_prefixlen_invalid(cidr):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "cidr_v6": cidr})


@pytest.mark.parametrize(
    "net",
    ["192.168.0.0/24", "10.0.0.0/8", "2001:db8::/32"],
)
def test_validated_formats_extended_ip_prefix_valid(net):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ip_net": net})
    assert m.ip_net == net


@pytest.mark.parametrize(
    "net",
    ["192.168.0.1/24", "not/valid"],  # host bits set → invalid network
)
def test_validated_formats_extended_ip_prefix_invalid(net):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ip_net": net})


@pytest.mark.parametrize("net", ["192.168.0.0/24", "10.0.0.0/8"])
def test_validated_formats_extended_ipv4_prefix_valid(net):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ipv4_net": net})
    assert m.ipv4_net == net


@pytest.mark.parametrize("net", ["192.168.0.1/24", "::1/128"])
def test_validated_formats_extended_ipv4_prefix_invalid(net):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ipv4_net": net})


@pytest.mark.parametrize("net", ["2001:db8::/32", "::/0"])
def test_validated_formats_extended_ipv6_prefix_valid(net):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ipv6_net": net})
    assert m.ipv6_net == net


@pytest.mark.parametrize("net", ["2001:db8::1/32", "192.168.0.0/24"])
def test_validated_formats_extended_ipv6_prefix_invalid(net):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "ipv6_net": net})


@pytest.mark.parametrize(
    "ep",
    ["example.com:80", "1.2.3.4:443", "[::1]:8080", "localhost:0"],
)
def test_validated_formats_extended_host_and_port_valid(ep):
    m = ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "endpoint": ep})
    assert m.endpoint == ep


@pytest.mark.parametrize(
    "ep",
    ["nocolon", "host:99999", "[::1", "example.com:abc"],
)
def test_validated_formats_extended_host_and_port_invalid(ep):
    with pytest.raises(ValidationError):
        ValidatedFormatsExtended(**{**_VALID_FORMATS_EXT, "endpoint": ep})


# ---------------------------------------------------------------------------
# ValidatedWellKnownRegex — well_known_regex enum validator
# ---------------------------------------------------------------------------


def test_validated_well_known_regex_defaults():
    # All three header fields are ConstrainedRequired — zero-arg construction fails.
    with pytest.raises(ValidationError):
        ValidatedWellKnownRegex()


@pytest.mark.parametrize("name", ["Content-Type", "X-Custom-Header", "Accept-Encoding"])
def test_validated_well_known_regex_header_name_valid(name):
    m = ValidatedWellKnownRegex(**{**_VALID_WKR, "header_name": name})
    assert m.header_name == name


@pytest.mark.parametrize("name", ["has space", "has:colon", "has\nnewline"])
def test_validated_well_known_regex_header_name_invalid(name):
    with pytest.raises(ValidationError):
        ValidatedWellKnownRegex(**{**_VALID_WKR, "header_name": name})


@pytest.mark.parametrize(
    "val", ["application/json", "gzip, deflate", "text/html; charset=utf-8"]
)
def test_validated_well_known_regex_header_value_valid(val):
    m = ValidatedWellKnownRegex(**{**_VALID_WKR, "header_value": val})
    assert m.header_value == val


@pytest.mark.parametrize("val", ["has\nnewline", "has\x00null"])
def test_validated_well_known_regex_header_value_invalid(val):
    with pytest.raises(ValidationError):
        ValidatedWellKnownRegex(**{**_VALID_WKR, "header_value": val})


# ---------------------------------------------------------------------------
# ValidatedNotContains — string.not_contains AfterValidator
# ---------------------------------------------------------------------------


def test_validated_not_contains_default():
    m = ValidatedNotContains()
    assert m.username == ""


@pytest.mark.parametrize("name", ["user", "alice", "bob123"])
def test_validated_not_contains_valid(name):
    m = ValidatedNotContains(username=name)
    assert m.username == name


@pytest.mark.parametrize("name", ["admin", "superadmin", "admin_user"])
def test_validated_not_contains_invalid(name):
    with pytest.raises(ValidationError):
        ValidatedNotContains(username=name)


# ---------------------------------------------------------------------------
# ValidatedFloatIn — float.in / double.not_in with float literals
# ---------------------------------------------------------------------------


def test_validated_float_in_defaults():
    # ratio (float.in, 0.0 not in allowed set) is ConstrainedRequired — zero-arg fails.
    with pytest.raises(ValidationError):
        ValidatedFloatIn()


@pytest.mark.parametrize("v", [0.25, 0.5, 0.75, 1.0])
def test_validated_float_in_ratio_valid(v):
    m = ValidatedFloatIn(ratio=v)
    assert m.ratio == pytest.approx(v)


@pytest.mark.parametrize("v", [0.3, 0.1, 2.0])
def test_validated_float_in_ratio_invalid(v):
    with pytest.raises(ValidationError):
        ValidatedFloatIn(ratio=v)


@pytest.mark.parametrize("v", [0.0, 1.0, 100.0])
def test_validated_float_in_score_valid(v):
    m = ValidatedFloatIn(ratio=0.25, score=v)
    assert m.score == pytest.approx(v)


@pytest.mark.parametrize("v", [-1.0, -2.0])
def test_validated_float_in_score_invalid(v):
    with pytest.raises(ValidationError):
        ValidatedFloatIn(ratio=0.25, score=v)


# ---------------------------------------------------------------------------
# ValidatedFloatExamples — float/double/bool/uint32 example annotations
# ---------------------------------------------------------------------------


def test_validated_float_examples_valid():
    m = ValidatedFloatExamples(ratio=1.5, score=3.14, flag=False, code=7)
    assert m.ratio == pytest.approx(1.5)
    assert m.score == pytest.approx(3.14)
    assert m.flag is False
    assert m.code == 7


def test_validated_float_examples_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "examples=[1.5, 0.25]" in text
    assert "examples=[3.14, 2.71]" in text
    assert "examples=[False, True]" in text
    assert "examples=[7, 42]" in text


def test_validated_float_examples_gt_enforced():
    # ratio, score, code are all ConstrainedRequired (gt=0 rejects zero value).
    with pytest.raises(ValidationError):
        ValidatedFloatExamples(ratio=0.0, score=1.0, code=1)
    with pytest.raises(ValidationError):
        ValidatedFloatExamples(ratio=1.0, score=0.0, code=1)
    with pytest.raises(ValidationError):
        ValidatedFloatExamples(ratio=1.0, score=1.0, code=0)


# ---------------------------------------------------------------------------
# ValidatedCEL — basic field-level CEL transpilation (existing message)
# ---------------------------------------------------------------------------


def test_validated_cel_default():
    # Default (age=0) is not explicitly validated by Pydantic — succeeds.
    m = ValidatedCEL()
    assert m.age == 0


def test_validated_cel_enforces_constraint():
    m = ValidatedCEL(age=1)
    assert m.age == 1


def test_validated_cel_rejects_negative():
    with pytest.raises(ValidationError):
        ValidatedCEL(age=-1)


def test_validated_cel_transpiled_not_dropped():
    # The simple "this > 0" on ValidatedCEL.age must be transpiled to a lambda,
    # not dropped. (cel inside repeated.items is still dropped — separate case.)
    text = _GEN_VALIDATE.read_text()
    assert '_make_cel_validator(lambda v: v > 0, "age must be positive")' in text


# ---------------------------------------------------------------------------
# ValidatedCELField — field-level CEL transpilation
# ---------------------------------------------------------------------------


def test_cel_field_age_valid():
    m = ValidatedCELField(age=5, name="Alice", code="XYZ")
    assert m.age == 5


def test_cel_field_age_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELField(age=-1, name="Alice", code="XYZ")


def test_cel_field_name_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELField(age=1, name="alice", code="XYZ")  # lowercase


def test_cel_field_code_prefix_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELField(age=1, name="Alice", code="ABC")  # wrong prefix


def test_cel_field_code_len_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELField(age=1, name="Alice", code="X")  # too short


# ---------------------------------------------------------------------------
# ValidatedCELMessage — message-level cross-field CEL
# ---------------------------------------------------------------------------


def test_cel_message_unique_valid():
    m = ValidatedCELMessage(bar=["a", "b"], baz=["c"])
    assert m.baz == ["c"]


def test_cel_message_unique_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELMessage(bar=["a"], baz=["a"])


def test_cel_message_unique_empty():
    m = ValidatedCELMessage()  # empty lists → unique trivially
    assert m.bar == []


# ---------------------------------------------------------------------------
# ValidatedCELHas — has() presence macro
# ---------------------------------------------------------------------------


def test_cel_has_first_name_set():
    m = ValidatedCELHas(first_name="Alice")
    assert m.first_name == "Alice"


def test_cel_has_last_name_set():
    m = ValidatedCELHas(last_name="Smith")
    assert m.last_name == "Smith"


def test_cel_has_neither_set():
    with pytest.raises(ValidationError):
        ValidatedCELHas()


# ---------------------------------------------------------------------------
# ValidatedCELCrossField — cross-field numeric comparison
# ---------------------------------------------------------------------------


def test_cel_cross_field_valid():
    m = ValidatedCELCrossField(min_val=1, max_val=10)
    assert m.min_val == 1


def test_cel_cross_field_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELCrossField(min_val=10, max_val=1)


# ---------------------------------------------------------------------------
# ValidatedCELEnumField — message-level CEL comparing enum field by .number
# ---------------------------------------------------------------------------


def test_cel_enum_field_valid_bread():
    m = ValidatedCELEnumField(food=ValidatedCELEnumField.Food.BREAD)
    assert m.food == "BREAD"


def test_cel_enum_field_valid_milk():
    m = ValidatedCELEnumField(food=ValidatedCELEnumField.Food.MILK)
    assert m.food == "MILK"


def test_cel_enum_field_invalid_eggs():
    with pytest.raises(ValidationError):
        ValidatedCELEnumField(food=ValidatedCELEnumField.Food.EGGS)


def test_cel_enum_field_unset_passes():
    # Unset enum (None) has number 0 (UNSPECIFIED), which satisfies 0 < 3.
    m = ValidatedCELEnumField()
    assert m.food is None


# ---------------------------------------------------------------------------
# ValidatedCELEnumAliased — enum field aliased due to Python reserved name
# ---------------------------------------------------------------------------


def test_cel_enum_aliased_valid_a():
    m = ValidatedCELEnumAliased(type=ValidatedCELEnumAliased.Kind.A)
    assert m.type_ == "A"


def test_cel_enum_aliased_valid_b():
    m = ValidatedCELEnumAliased(type=ValidatedCELEnumAliased.Kind.B)
    assert m.type_ == "B"


def test_cel_enum_aliased_invalid_c():
    with pytest.raises(ValidationError):
        ValidatedCELEnumAliased(type=ValidatedCELEnumAliased.Kind.C)


def test_cel_enum_aliased_unset_passes():
    m = ValidatedCELEnumAliased()
    assert m.type_ is None


# ---------------------------------------------------------------------------
# ValidatedCELReservedName — message-level CEL referencing reserved-name fields
# ---------------------------------------------------------------------------


def test_cel_reserved_name_unset_passes():
    # Both fields unset — has() guards skip the body, no error.
    m = ValidatedCELReservedName()
    assert m.bool_ is None
    assert m.float_ is None


def test_cel_reserved_name_bool_true_valid():
    m = ValidatedCELReservedName(**{"bool": True})
    assert m.bool_ is True


def test_cel_reserved_name_bool_false_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELReservedName(**{"bool": False})


def test_cel_reserved_name_float_positive_valid():
    m = ValidatedCELReservedName(**{"float": 1.5})
    assert m.float_ == 1.5


def test_cel_reserved_name_float_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELReservedName(**{"float": -0.5})


# ---------------------------------------------------------------------------
# ValidatedCELDropped — was the drop path; all() is now transpiled
# ---------------------------------------------------------------------------


def test_cel_dropped_now_validates():
    # After comprehension support, all() is transpiled and the constraint fires.
    m = ValidatedCELDropped(scores=[1, 2, 3])
    assert m.scores == [1, 2, 3]


def test_cel_dropped_now_rejects_negatives():
    with pytest.raises(ValidationError):
        ValidatedCELDropped(scores=[1, -2, 3])


def test_cel_dropped_no_longer_has_dropped_comment():
    # The "not translated" comment must not appear for this field any more.
    text = Path("gen/api/v1/validate_pydantic.py").read_text()
    assert 'cel id="all_positive" (not translated' not in text


# ---------------------------------------------------------------------------
# ValidatedCELAll — all() comprehension
# ---------------------------------------------------------------------------


def test_cel_all_valid():
    m = ValidatedCELAll(scores=[1, 2, 3])
    assert m.scores == [1, 2, 3]


def test_cel_all_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELAll(scores=[1, -1, 3])


def test_cel_all_empty_passes():
    # all() on an empty list is vacuously true.
    m = ValidatedCELAll(scores=[])
    assert m.scores == []


# ---------------------------------------------------------------------------
# ValidatedCELExists — exists() comprehension
# ---------------------------------------------------------------------------


def test_cel_exists_valid():
    m = ValidatedCELExists(tags=["user", "admin"])
    assert m.tags == ["user", "admin"]


def test_cel_exists_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExists(tags=["user", "moderator"])


def test_cel_exists_empty_invalid():
    # exists() on an empty list is vacuously false.
    with pytest.raises(ValidationError):
        ValidatedCELExists(tags=[])


# ---------------------------------------------------------------------------
# ValidatedCELExistsOne — exists_one() comprehension
# ---------------------------------------------------------------------------


def test_cel_exists_one_valid():
    m = ValidatedCELExistsOne(roles=["user", "admin"])
    assert m.roles == ["user", "admin"]


def test_cel_exists_one_invalid_none():
    with pytest.raises(ValidationError):
        ValidatedCELExistsOne(roles=["user", "moderator"])


def test_cel_exists_one_invalid_two():
    with pytest.raises(ValidationError):
        ValidatedCELExistsOne(roles=["admin", "admin"])


# ---------------------------------------------------------------------------
# ValidatedCELFilter — filter() comprehension chained with size()
# ---------------------------------------------------------------------------


def test_cel_filter_valid():
    m = ValidatedCELFilter(values=[1, -1, 2])  # 2 positives → passes
    assert m.values == [1, -1, 2]


def test_cel_filter_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELFilter(values=[1, -1, -2])  # only 1 positive → fails


def test_cel_filter_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELFilter(values=[])


# ---------------------------------------------------------------------------
# ValidatedCELMapAll — map() chained with all() (nested comprehension)
# ---------------------------------------------------------------------------


def test_cel_map_all_valid():
    m = ValidatedCELMapAll(words=["foo", "bar", "baz"])
    assert m.words == ["foo", "bar", "baz"]


def test_cel_map_all_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELMapAll(words=["ok", "no"])  # "no" has size 2 < 3


def test_cel_map_all_empty_passes():
    # all() on an empty mapped list is vacuously true.
    m = ValidatedCELMapAll(words=[])
    assert m.words == []


# ---------------------------------------------------------------------------
# ValidatedCELMessageAll — message-level all() comprehension
# ---------------------------------------------------------------------------


def test_cel_message_all_valid():
    m = ValidatedCELMessageAll(prices=[10, 20], quantities=[1, 2])
    assert m.prices == [10, 20]


def test_cel_message_all_invalid_price():
    with pytest.raises(ValidationError):
        ValidatedCELMessageAll(prices=[10, -5], quantities=[1, 2])


def test_cel_message_all_invalid_quantity():
    with pytest.raises(ValidationError):
        ValidatedCELMessageAll(prices=[10, 20], quantities=[1, -1])


def test_cel_message_all_empty_passes():
    m = ValidatedCELMessageAll()  # both empty → vacuously true
    assert m.prices == []


# ---------------------------------------------------------------------------
# ValidatedCELStillDropped — 'this > now' is now transpiled (not dropped)
# ---------------------------------------------------------------------------


def test_cel_still_dropped_now_transpiled():
    # 'now' is now supported; the dropped comment must be gone.
    text = Path("gen/api/v1/validate_pydantic.py").read_text()
    assert 'cel id="after_now" (not translated' not in text


def test_cel_still_dropped_none_valid():
    # Null-safe: an unset Timestamp field is always valid.
    m = ValidatedCELStillDropped()
    assert m.created is None


def test_cel_still_dropped_future_valid():
    future = _dt_datetime.now(tz=timezone.utc) + timedelta(days=1)
    m = ValidatedCELStillDropped(created=future)
    assert m.created == future


def test_cel_still_dropped_past_invalid():
    past = _dt_datetime(2020, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELStillDropped(created=past)


# ---------------------------------------------------------------------------
# ValidatedCELTimestamp — this > now
# ---------------------------------------------------------------------------


def test_cel_timestamp_none_valid():
    # Null-safe: unset Timestamp field passes.
    m = ValidatedCELTimestamp()
    assert m.deadline is None


def test_cel_timestamp_future_valid():
    future = _dt_datetime.now(tz=timezone.utc) + timedelta(days=1)
    m = ValidatedCELTimestamp(deadline=future)
    assert m.deadline == future


def test_cel_timestamp_past_invalid():
    past = _dt_datetime(2020, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTimestamp(deadline=past)


# ---------------------------------------------------------------------------
# ValidatedCELDuration — this > duration("0s")
# ---------------------------------------------------------------------------


def test_cel_duration_none_valid():
    m = ValidatedCELDuration()
    assert m.window is None


def test_cel_duration_positive_valid():
    m = ValidatedCELDuration(window=timedelta(seconds=30))
    assert m.window == timedelta(seconds=30)


def test_cel_duration_zero_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELDuration(window=timedelta(0))


def test_cel_duration_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELDuration(window=timedelta(seconds=-1))


# ---------------------------------------------------------------------------
# ValidatedCELDurationRange — this >= duration("1m") && this <= duration("1h")
# ---------------------------------------------------------------------------


def test_cel_duration_range_none_valid():
    m = ValidatedCELDurationRange()
    assert m.ttl is None


def test_cel_duration_range_mid_valid():
    m = ValidatedCELDurationRange(ttl=timedelta(minutes=30))
    assert m.ttl == timedelta(minutes=30)


def test_cel_duration_range_lower_bound_valid():
    m = ValidatedCELDurationRange(ttl=timedelta(minutes=1))
    assert m.ttl == timedelta(minutes=1)


def test_cel_duration_range_upper_bound_valid():
    m = ValidatedCELDurationRange(ttl=timedelta(hours=1))
    assert m.ttl == timedelta(hours=1)


def test_cel_duration_range_below_min_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELDurationRange(ttl=timedelta(seconds=30))


def test_cel_duration_range_above_max_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELDurationRange(ttl=timedelta(hours=2))


# ---------------------------------------------------------------------------
# ValidatedCELTimestampAfter — this >= timestamp("2020-01-01T00:00:00Z")
# ---------------------------------------------------------------------------


def test_cel_timestamp_after_none_valid():
    m = ValidatedCELTimestampAfter()
    assert m.created is None


def test_cel_timestamp_after_valid():
    ts = _dt_datetime(2024, 6, 1, tzinfo=timezone.utc)
    m = ValidatedCELTimestampAfter(created=ts)
    assert m.created == ts


def test_cel_timestamp_after_boundary_valid():
    boundary = _dt_datetime(2020, 1, 1, tzinfo=timezone.utc)
    m = ValidatedCELTimestampAfter(created=boundary)
    assert m.created == boundary


def test_cel_timestamp_after_invalid():
    old = _dt_datetime(2019, 12, 31, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTimestampAfter(created=old)


# ---------------------------------------------------------------------------
# ValidatedCELTimestampWindow — this <= now + duration("3600s")
# ---------------------------------------------------------------------------


def test_cel_timestamp_window_none_valid():
    m = ValidatedCELTimestampWindow()
    assert m.expires is None


def test_cel_timestamp_window_near_valid():
    soon = _dt_datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    m = ValidatedCELTimestampWindow(expires=soon)
    assert m.expires == soon


def test_cel_timestamp_window_too_far_invalid():
    far = _dt_datetime.now(tz=timezone.utc) + timedelta(hours=2)
    with pytest.raises(ValidationError):
        ValidatedCELTimestampWindow(expires=far)


# ---------------------------------------------------------------------------
# ValidatedCELStringReturn — string-returning CEL expression
# ---------------------------------------------------------------------------


def test_cel_string_return_valid():
    m = ValidatedCELStringReturn(value=5)
    assert m.value == 5


def test_cel_string_return_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELStringReturn(value=-1)


# ---------------------------------------------------------------------------
# ValidatedWellKnownRegex loose_header — strict=false drop
# ---------------------------------------------------------------------------


def test_validated_well_known_regex_loose_header_default():
    # All WKR header fields are ConstrainedRequired — zero-arg construction fails.
    with pytest.raises(ValidationError):
        ValidatedWellKnownRegex()


@pytest.mark.parametrize("name", ["Content-Type", "X-Custom-Header"])
def test_validated_well_known_regex_loose_header_valid(name):
    m = ValidatedWellKnownRegex(**{**_VALID_WKR, "loose_header": name})
    assert m.loose_header == name


@pytest.mark.parametrize("name", ["has space", "has\nnewline"])
def test_validated_well_known_regex_loose_header_invalid(name):
    with pytest.raises(ValidationError):
        ValidatedWellKnownRegex(**{**_VALID_WKR, "loose_header": name})


def test_validated_well_known_regex_loose_header_strict_false_comment():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: strict=false (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedConst uint32 code — Uint32Kind in formatScalarLiteral
# ---------------------------------------------------------------------------


def test_validated_const_code_default():
    m = ValidatedConst()
    assert m.code == 100


def test_validated_const_code_enforced():
    with pytest.raises(ValidationError):
        ValidatedConst(code=99)


def test_validated_const_code_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "_Literal[100]" in text


# ---------------------------------------------------------------------------
# ValidatedConst inactive — BoolKind false branch in formatScalarLiteral
# ---------------------------------------------------------------------------


def test_validated_const_inactive_default():
    m = ValidatedConst()
    assert m.inactive is False


def test_validated_const_inactive_enforced():
    with pytest.raises(ValidationError):
        ValidatedConst(inactive=True)


def test_validated_const_inactive_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "_Literal[False]" in text


# ---------------------------------------------------------------------------
# ValidatedUser role — EnumKind in formatExampleItem
# ---------------------------------------------------------------------------


def test_validated_user_role_example_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    # enum example annotation produces examples=[1]
    assert "examples=[1]" in text


# ---------------------------------------------------------------------------
# ValidatedIgnore — ignore = IGNORE_IF_ZERO_VALUE opts out of ConstrainedRequired
# ---------------------------------------------------------------------------


def test_validated_ignore_zero_arg():
    # Both fields keep their zero defaults because ignore = IGNORE_IF_ZERO_VALUE.
    m = ValidatedIgnore()
    assert m.email == ""
    assert m.age == 0


def test_validated_ignore_valid_values():
    m = ValidatedIgnore(email="user@example.com", age=5)
    assert m.email == "user@example.com"
    assert m.age == 5


def test_validated_ignore_invalid_nonzero():
    with pytest.raises(ValidationError):
        ValidatedIgnore(email="not-an-email")
    with pytest.raises(ValidationError):
        ValidatedIgnore(age=-1)


# ---------------------------------------------------------------------------
# ValidatedBytesIP — bytes.ip/ipv4/ipv6 (byte-length validators)
# ---------------------------------------------------------------------------


def test_validated_bytes_ip_valid_ipv4():
    m = ValidatedBytesIP(
        ip_addr=b"\x7f\x00\x00\x01",
        ipv4_addr=b"\x7f\x00\x00\x01",
        ipv6_addr=b"\x00" * 16,
    )
    assert m.ip_addr == b"\x7f\x00\x00\x01"


def test_validated_bytes_ip_valid_ipv6():
    m = ValidatedBytesIP(
        ip_addr=b"\x00" * 16,
        ipv4_addr=b"\x7f\x00\x00\x01",
        ipv6_addr=b"\x00" * 16,
    )
    assert m.ip_addr == b"\x00" * 16


def test_validated_bytes_ip_empty_skips_validation():
    # Empty bytes is the proto3 zero value; validator is skipped.
    m = ValidatedBytesIP(ip_addr=b"", ipv4_addr=b"", ipv6_addr=b"")
    assert m.ip_addr == b""


def test_validated_bytes_ip_wrong_length():
    with pytest.raises(ValidationError):
        ValidatedBytesIP(
            ip_addr=b"\x00" * 5,
            ipv4_addr=b"\x7f\x00\x00\x01",
            ipv6_addr=b"\x00" * 16,
        )


def test_validated_bytes_ipv4_wrong_length():
    with pytest.raises(ValidationError):
        ValidatedBytesIP(
            ip_addr=b"\x7f\x00\x00\x01",
            ipv4_addr=b"\x00" * 16,
            ipv6_addr=b"\x00" * 16,
        )


def test_validated_bytes_ipv6_wrong_length():
    with pytest.raises(ValidationError):
        ValidatedBytesIP(
            ip_addr=b"\x7f\x00\x00\x01",
            ipv4_addr=b"\x7f\x00\x00\x01",
            ipv6_addr=b"\x00" * 4,
        )


# ---------------------------------------------------------------------------
# ValidatedRepeatedItems — repeated.items per-element constraints
# ---------------------------------------------------------------------------


def test_repeated_items_valid():
    m = ValidatedRepeatedItems(tags=["hello"], scores=[1])
    assert m.tags == ["hello"]
    assert m.scores == [1]


def test_repeated_items_empty_list_valid():
    m = ValidatedRepeatedItems()  # empty lists, no items to validate
    assert m.tags == []


def test_repeated_items_tag_empty_string_invalid():
    with pytest.raises(ValidationError):
        ValidatedRepeatedItems(tags=[""])


def test_repeated_items_tag_too_long_invalid():
    with pytest.raises(ValidationError):
        ValidatedRepeatedItems(tags=["a" * 33])


def test_repeated_items_score_zero_invalid():
    with pytest.raises(ValidationError):
        ValidatedRepeatedItems(scores=[0])


def test_repeated_items_score_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedRepeatedItems(scores=[-1])


def test_repeated_items_email_valid():
    m = ValidatedRepeatedItems(emails=["user@example.com", "other@example.org"])
    assert m.emails == ["user@example.com", "other@example.org"]


def test_repeated_items_email_empty_list_valid():
    m = ValidatedRepeatedItems()
    assert m.emails == []


def test_repeated_items_email_invalid():
    with pytest.raises(ValidationError):
        ValidatedRepeatedItems(emails=["not-an-email"])


def test_repeated_items_email_skips_empty_string():
    # Empty string is the proto3 zero value; email validator is skipped.
    m = ValidatedRepeatedItems(emails=[""])
    assert m.emails == [""]


# --- ValidatedMapConstraints ---


def test_map_constraints_valid():
    m = ValidatedMapConstraints(labels={"env": "prod"})
    assert m.labels == {"env": "prod"}


def test_map_constraints_empty_dict_valid():
    # No min_pairs constraint; empty dict is allowed.
    m = ValidatedMapConstraints()
    assert m.labels == {}


def test_map_constraints_key_empty_fails():
    # Key "" violates min_len=1 on keys.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(labels={"": "prod"})


def test_map_constraints_key_too_long_fails():
    # Key of 64 chars violates max_len=63 on keys.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(labels={"a" * 64: "prod"})


def test_map_constraints_key_max_len_boundary_valid():
    # Key of exactly 63 chars is valid.
    m = ValidatedMapConstraints(labels={"a" * 63: "prod"})
    assert len(list(m.labels.keys())[0]) == 63


def test_map_constraints_value_empty_fails():
    # Value "" violates min_len=1 on values.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(labels={"env": ""})


def test_map_constraints_counters_valid():
    m = ValidatedMapConstraints(counters={"hits": 1})
    assert m.counters == {"hits": 1}


def test_map_constraints_counters_zero_fails():
    # Value 0 violates gt=0 on values.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(counters={"hits": 0})


def test_map_constraints_counters_negative_fails():
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(counters={"hits": -1})


def test_map_constraints_rules_valid():
    m = ValidatedMapConstraints(rules={"user@example.com": "hello"})
    assert m.rules == {"user@example.com": "hello"}


def test_map_constraints_rules_invalid_key_fails():
    # Key must be a valid email.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(rules={"not-an-email": "hello"})


def test_map_constraints_rules_invalid_value_fails():
    # Value must match "^[a-z]+$".
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(rules={"user@example.com": "UPPER"})


def test_map_constraints_key_min_len_boundary_valid():
    # Key of exactly 1 char satisfies min_len=1.
    m = ValidatedMapConstraints(labels={"a": "prod"})
    assert m.labels == {"a": "prod"}


def test_map_constraints_tagged_valid():
    # min_pairs=1 and keys.min_len=1 both satisfied.
    m = ValidatedMapConstraints(tagged={"env": "prod"})
    assert m.tagged == {"env": "prod"}


def test_map_constraints_tagged_empty_fails():
    # Violates min_pairs=1.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(tagged={})


def test_map_constraints_tagged_empty_key_fails():
    # Violates keys.min_len=1.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(tagged={"": "prod"})


def test_map_constraints_scores_valid():
    # Positive integer key and non-empty value.
    m = ValidatedMapConstraints(scores={1: "alice", 2: "bob"})
    assert m.scores == {1: "alice", 2: "bob"}


def test_map_constraints_scores_zero_key_fails():
    # Integer key 0 violates gt=0 on keys.
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(scores={0: "alice"})


def test_map_constraints_scores_negative_key_fails():
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(scores={-1: "alice"})


def test_map_constraints_scores_empty_value_fails():
    # Empty string value violates not_in=[""].
    with pytest.raises(ValidationError):
        ValidatedMapConstraints(scores={1: ""})


# -----------------------------------------------------------------------
# ValidatedStringBytes — string.min_bytes / max_bytes / len_bytes
# -----------------------------------------------------------------------


def test_validated_string_bytes_constrained_required():
    with pytest.raises(ValidationError):
        ValidatedStringBytes()


def test_validated_string_bytes_label_default():
    m = ValidatedStringBytes(**_VALID_STR_BYTES)
    assert m.label == ""


@pytest.mark.parametrize("payload", ["x", "a" * 255, "日"])  # 1, 255, 3 bytes
def test_validated_string_bytes_payload_valid(payload):
    m = ValidatedStringBytes(**{**_VALID_STR_BYTES, "payload": payload})
    assert m.payload == payload


def test_validated_string_bytes_payload_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "payload": ""})


def test_validated_string_bytes_token_exact():
    m = ValidatedStringBytes(**{**_VALID_STR_BYTES, "token": "a" * 32})
    assert m.token == "a" * 32


def test_validated_string_bytes_token_too_short():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "token": "a" * 31})


def test_validated_string_bytes_token_too_long():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "token": "a" * 33})


def test_validated_string_bytes_multibyte_token_wrong_bytes():
    # "日本語" is 3 codepoints but 9 UTF-8 bytes — fails len_bytes=32
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "token": "日本語"})


@pytest.mark.parametrize("label", ["", "x" * 255])
def test_validated_string_bytes_label_valid(label):
    m = ValidatedStringBytes(**{**_VALID_STR_BYTES, "label": label})
    assert m.label == label


def test_validated_string_bytes_label_multibyte_at_limit():
    # "日" is 3 UTF-8 bytes; 85 × 3 = 255 bytes — exactly at the max_bytes limit.
    m = ValidatedStringBytes(**{**_VALID_STR_BYTES, "label": "日" * 85})
    assert len(m.label.encode()) == 255


def test_validated_string_bytes_label_too_long():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "label": "x" * 256})


def test_validated_string_bytes_tag_valid():
    m = ValidatedStringBytes(**{**_VALID_STR_BYTES, "tag": "ab"})
    assert m.tag == "ab"


def test_validated_string_bytes_tag_too_short():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "tag": "a"})


def test_validated_string_bytes_tag_too_long():
    with pytest.raises(ValidationError):
        ValidatedStringBytes(**{**_VALID_STR_BYTES, "tag": "x" * 65})


def test_validated_string_bytes_in_generated_file():
    text = _GEN_VALIDATE.read_text()
    assert "_make_min_bytes_validator" in text
    assert "_make_max_bytes_validator" in text
    assert "_make_len_bytes_validator" in text


# ---------------------------------------------------------------------------
# ValidatedCELIsEmail — isEmail() in CEL
# ---------------------------------------------------------------------------


def test_cel_is_email_valid():
    m = ValidatedCELIsEmail(contact="user@example.com")
    assert m.contact == "user@example.com"


def test_cel_is_email_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsEmail(contact="notanemail")


# ---------------------------------------------------------------------------
# ValidatedCELIsIp — isIp() with version argument
# ---------------------------------------------------------------------------


def test_cel_is_ip_any_valid_v4():
    m = ValidatedCELIsIp(addr="1.2.3.4", addr_v4="1.2.3.4", addr_v6="::1")
    assert m.addr == "1.2.3.4"


def test_cel_is_ip_any_valid_v6():
    m = ValidatedCELIsIp(addr="::1", addr_v4="1.2.3.4", addr_v6="::1")
    assert m.addr == "::1"


def test_cel_is_ip_any_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsIp(addr="notanip", addr_v4="1.2.3.4", addr_v6="::1")


def test_cel_is_ip_v4_rejects_ipv6():
    with pytest.raises(ValidationError):
        ValidatedCELIsIp(addr="1.2.3.4", addr_v4="::1", addr_v6="::1")


def test_cel_is_ip_v6_rejects_ipv4():
    with pytest.raises(ValidationError):
        ValidatedCELIsIp(addr="1.2.3.4", addr_v4="1.2.3.4", addr_v6="1.2.3.4")


# ---------------------------------------------------------------------------
# ValidatedCELIsIpPrefix — isIpPrefix()
# ---------------------------------------------------------------------------


def test_cel_is_ip_prefix_valid_v4():
    m = ValidatedCELIsIpPrefix(prefix="10.0.0.0/8", prefix_v4="10.0.0.0/8")
    assert m.prefix == "10.0.0.0/8"


def test_cel_is_ip_prefix_valid_v6():
    m = ValidatedCELIsIpPrefix(prefix="2001:db8::/32", prefix_v4="10.0.0.0/8")
    assert m.prefix == "2001:db8::/32"


def test_cel_is_ip_prefix_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsIpPrefix(prefix="notaprefix", prefix_v4="10.0.0.0/8")


def test_cel_is_ip_prefix_v4_non_strict_allows_host_bits():
    # strict=False allows host bits set in the prefix
    m = ValidatedCELIsIpPrefix(prefix="10.0.0.0/8", prefix_v4="10.1.2.3/8")
    assert m.prefix_v4 == "10.1.2.3/8"


def test_cel_is_ip_prefix_v4_rejects_v6():
    with pytest.raises(ValidationError):
        ValidatedCELIsIpPrefix(prefix="10.0.0.0/8", prefix_v4="2001:db8::/32")


# ---------------------------------------------------------------------------
# ValidatedCELIsHostname — isHostname()
# ---------------------------------------------------------------------------


def test_cel_is_hostname_valid():
    m = ValidatedCELIsHostname(host="example.com")
    assert m.host == "example.com"


def test_cel_is_hostname_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsHostname(host="not a hostname!")


# ---------------------------------------------------------------------------
# ValidatedCELIsUri — isUri() and isUriRef()
# ---------------------------------------------------------------------------


def test_cel_is_uri_valid():
    m = ValidatedCELIsUri(link="https://example.com", ref="/path")
    assert m.link == "https://example.com"


def test_cel_is_uri_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsUri(link="not a uri", ref="/path")


def test_cel_is_uri_ref_valid_relative():
    m = ValidatedCELIsUri(link="https://example.com", ref="/relative/path")
    assert m.ref == "/relative/path"


def test_cel_is_uri_ref_valid_absolute():
    m = ValidatedCELIsUri(link="https://example.com", ref="https://example.com")
    assert m.ref == "https://example.com"


def test_cel_is_uri_ref_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsUri(link="https://example.com", ref="has\ncontrol\x00chars")


# ---------------------------------------------------------------------------
# ValidatedCELIsHostAndPort — isHostAndPort()
# ---------------------------------------------------------------------------


def test_cel_is_host_and_port_valid_hostname():
    m = ValidatedCELIsHostAndPort(endpoint="example.com:80")
    assert m.endpoint == "example.com:80"


def test_cel_is_host_and_port_valid_ip():
    m = ValidatedCELIsHostAndPort(endpoint="1.2.3.4:443")
    assert m.endpoint == "1.2.3.4:443"


def test_cel_is_host_and_port_missing_port():
    with pytest.raises(ValidationError):
        ValidatedCELIsHostAndPort(endpoint="example.com")


def test_cel_is_host_and_port_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsHostAndPort(endpoint="not!a!host:99")


# ---------------------------------------------------------------------------
# ValidatedCELIsNanInf — isNan() and isInf()
# ---------------------------------------------------------------------------


def test_cel_is_nan_valid():
    m = ValidatedCELIsNanInf(value=1.0, bounded=2.0)
    assert m.value == 1.0


def test_cel_is_nan_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsNanInf(value=float("nan"), bounded=2.0)


def test_cel_is_inf_valid():
    m = ValidatedCELIsNanInf(value=1.0, bounded=2.0)
    assert m.bounded == 2.0


def test_cel_is_inf_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsNanInf(value=1.0, bounded=float("inf"))


def test_cel_is_inf_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsNanInf(value=1.0, bounded=float("-inf"))


# ---------------------------------------------------------------------------
# ValidatedCELTsYear — getFullYear()
# ---------------------------------------------------------------------------


def test_cel_ts_year_none_valid():
    assert ValidatedCELTsYear().t is None


def test_cel_ts_year_valid():
    t = _dt_datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
    assert ValidatedCELTsYear(t=t).t == t


def test_cel_ts_year_invalid():
    t = _dt_datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTsYear(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsMonth — getMonth() (0-indexed, January == 0)
# ---------------------------------------------------------------------------


def test_cel_ts_month_none_valid():
    assert ValidatedCELTsMonth().t is None


def test_cel_ts_month_valid():
    t = _dt_datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc)  # January
    assert ValidatedCELTsMonth(t=t).t == t


def test_cel_ts_month_invalid():
    t = _dt_datetime(2024, 2, 15, 0, 0, tzinfo=timezone.utc)  # February = index 1
    with pytest.raises(ValidationError):
        ValidatedCELTsMonth(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsDayOfMonth — getDayOfMonth() (0-indexed, 1st == 0)
# ---------------------------------------------------------------------------


def test_cel_ts_dom_none_valid():
    assert ValidatedCELTsDayOfMonth().t is None


def test_cel_ts_dom_valid():
    t = _dt_datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc)  # 15th = index 14
    assert ValidatedCELTsDayOfMonth(t=t).t == t


def test_cel_ts_dom_invalid():
    t = _dt_datetime(2024, 1, 14, 0, 0, tzinfo=timezone.utc)  # 14th = index 13
    with pytest.raises(ValidationError):
        ValidatedCELTsDayOfMonth(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsDayOfWeek — getDayOfWeek() (Sun=0, Mon=1, …, Sat=6)
# ---------------------------------------------------------------------------


def test_cel_ts_dow_none_valid():
    assert ValidatedCELTsDayOfWeek().t is None


def test_cel_ts_dow_monday_valid():
    # 2024-01-15 is a Monday → getDayOfWeek() == 1
    t = _dt_datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert ValidatedCELTsDayOfWeek(t=t).t == t


def test_cel_ts_dow_friday_valid():
    # 2024-01-19 is a Friday → getDayOfWeek() == 5
    t = _dt_datetime(2024, 1, 19, 12, 0, tzinfo=timezone.utc)
    assert ValidatedCELTsDayOfWeek(t=t).t == t


def test_cel_ts_dow_sunday_invalid():
    # 2024-01-21 is a Sunday → getDayOfWeek() == 0
    t = _dt_datetime(2024, 1, 21, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTsDayOfWeek(t=t)


def test_cel_ts_dow_saturday_invalid():
    # 2024-01-20 is a Saturday → getDayOfWeek() == 6
    t = _dt_datetime(2024, 1, 20, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTsDayOfWeek(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsDayOfYear — getDayOfYear() (0-indexed, Jan 1 == 0)
# ---------------------------------------------------------------------------


def test_cel_ts_doy_none_valid():
    assert ValidatedCELTsDayOfYear().t is None


def test_cel_ts_doy_valid():
    # 2024-07-01 is day 183 (1-indexed) → index 182 — exactly the boundary
    t = _dt_datetime(2024, 7, 1, 0, 0, tzinfo=timezone.utc)
    assert ValidatedCELTsDayOfYear(t=t).t == t


def test_cel_ts_doy_invalid():
    # 2024-06-30 is day 182 (1-indexed) → index 181 < 182
    t = _dt_datetime(2024, 6, 30, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTsDayOfYear(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsHours — getHours() (UTC, 0–23)
# ---------------------------------------------------------------------------


def test_cel_ts_hours_none_valid():
    assert ValidatedCELTsHours().t is None


def test_cel_ts_hours_valid():
    t = _dt_datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)  # 14:00 UTC
    assert ValidatedCELTsHours(t=t).t == t


def test_cel_ts_hours_invalid():
    t = _dt_datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)  # 10:00 UTC
    with pytest.raises(ValidationError):
        ValidatedCELTsHours(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsMillis — getMilliseconds() (0–999)
# ---------------------------------------------------------------------------


def test_cel_ts_millis_none_valid():
    assert ValidatedCELTsMillis().t is None


def test_cel_ts_millis_valid():
    t = _dt_datetime(2024, 1, 15, 12, 0, 0, 0, tzinfo=timezone.utc)  # no sub-second
    assert ValidatedCELTsMillis(t=t).t == t


def test_cel_ts_millis_invalid():
    t = _dt_datetime(2024, 1, 15, 12, 0, 0, 500_000, tzinfo=timezone.utc)  # 500ms
    with pytest.raises(ValidationError):
        ValidatedCELTsMillis(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsHoursUTC — getHours("UTC") same as getHours()
# ---------------------------------------------------------------------------


def test_cel_ts_hours_utc_none_valid():
    assert ValidatedCELTsHoursUTC().t is None


def test_cel_ts_hours_utc_valid():
    t = _dt_datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc)
    assert ValidatedCELTsHoursUTC(t=t).t == t


def test_cel_ts_hours_utc_invalid():
    t = _dt_datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        ValidatedCELTsHoursUTC(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsHoursTZ — getHours("America/New_York")
# 2024-01-15T17:00:00Z == 12:00 EST (UTC-5, no DST in January) → passes
# 2024-01-15T16:00:00Z == 11:00 EST → fails
# ---------------------------------------------------------------------------


def test_cel_ts_hours_tz_none_valid():
    assert ValidatedCELTsHoursTZ().t is None


def test_cel_ts_hours_tz_valid():
    t = _dt_datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc)  # 12:00 EST
    assert ValidatedCELTsHoursTZ(t=t).t == t


def test_cel_ts_hours_tz_invalid():
    t = _dt_datetime(2024, 1, 15, 16, 0, tzinfo=timezone.utc)  # 11:00 EST
    with pytest.raises(ValidationError):
        ValidatedCELTsHoursTZ(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELDurGetHours — Duration.getHours() (total hours, truncated)
# ---------------------------------------------------------------------------


def test_cel_dur_get_hours_none_valid():
    assert ValidatedCELDurGetHours().d is None


def test_cel_dur_get_hours_valid():
    d = timedelta(hours=3)  # getHours() = 3 >= 2
    assert ValidatedCELDurGetHours(d=d).d == d


def test_cel_dur_get_hours_truncated_valid():
    d = timedelta(hours=2, minutes=30)  # getHours() = 2 (truncated) >= 2
    assert ValidatedCELDurGetHours(d=d).d == d


def test_cel_dur_get_hours_invalid():
    d = timedelta(hours=1, minutes=59)  # getHours() = 1 < 2
    with pytest.raises(ValidationError):
        ValidatedCELDurGetHours(d=d)


# ---------------------------------------------------------------------------
# ValidatedCELDurGetMinutes — Duration.getMinutes() (total minutes, truncated)
# ---------------------------------------------------------------------------


def test_cel_dur_get_minutes_none_valid():
    assert ValidatedCELDurGetMinutes().d is None


def test_cel_dur_get_minutes_valid():
    d = timedelta(hours=2)  # getMinutes() = 120 >= 90
    assert ValidatedCELDurGetMinutes(d=d).d == d


def test_cel_dur_get_minutes_exact_valid():
    d = timedelta(minutes=90)  # getMinutes() = 90 >= 90
    assert ValidatedCELDurGetMinutes(d=d).d == d


def test_cel_dur_get_minutes_invalid():
    d = timedelta(minutes=89, seconds=59)  # getMinutes() = 89 < 90
    with pytest.raises(ValidationError):
        ValidatedCELDurGetMinutes(d=d)


# ---------------------------------------------------------------------------
# ValidatedCELDurGetSeconds — Duration.getSeconds() (total seconds, truncated)
# ---------------------------------------------------------------------------


def test_cel_dur_get_seconds_none_valid():
    assert ValidatedCELDurGetSeconds().d is None


def test_cel_dur_get_seconds_valid():
    d = timedelta(hours=1)  # getSeconds() = 3600 == 3600
    assert ValidatedCELDurGetSeconds(d=d).d == d


def test_cel_dur_get_seconds_invalid():
    d = timedelta(minutes=59)  # getSeconds() = 3540 != 3600
    with pytest.raises(ValidationError):
        ValidatedCELDurGetSeconds(d=d)


# ---------------------------------------------------------------------------
# ValidatedCELDurGetMillis — Duration.getMilliseconds() (total ms, truncated)
# ---------------------------------------------------------------------------


def test_cel_dur_get_millis_none_valid():
    assert ValidatedCELDurGetMillis().d is None


def test_cel_dur_get_millis_valid():
    d = timedelta(seconds=2)  # getMilliseconds() = 2000 >= 1500
    assert ValidatedCELDurGetMillis(d=d).d == d


def test_cel_dur_get_millis_exact_valid():
    d = timedelta(milliseconds=1500)  # getMilliseconds() = 1500 >= 1500
    assert ValidatedCELDurGetMillis(d=d).d == d


def test_cel_dur_get_millis_invalid():
    d = timedelta(milliseconds=1499)  # getMilliseconds() = 1499 < 1500
    with pytest.raises(ValidationError):
        ValidatedCELDurGetMillis(d=d)


# ---------------------------------------------------------------------------
# ValidatedCELEndsWith — endsWith() member function
# ---------------------------------------------------------------------------


def test_cel_ends_with_valid():
    m = ValidatedCELEndsWith(filename="schema.proto")
    assert m.filename == "schema.proto"


def test_cel_ends_with_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELEndsWith(filename="schema.py")


def test_cel_ends_with_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELEndsWith(filename="")


# ---------------------------------------------------------------------------
# ValidatedCELContains — contains() member function
# ---------------------------------------------------------------------------


def test_cel_contains_valid():
    m = ValidatedCELContains(tag="user@org")
    assert m.tag == "user@org"


def test_cel_contains_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELContains(tag="no-at-sign")


def test_cel_contains_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELContains(tag="")


# ---------------------------------------------------------------------------
# ValidatedCELNegate — unary negate; -1 is Negate(Literal(1)) in CEL AST
# ---------------------------------------------------------------------------


def test_cel_negate_zero_valid():
    m = ValidatedCELNegate(value=0)  # 0 > -1 → passes
    assert m.value == 0


def test_cel_negate_positive_valid():
    m = ValidatedCELNegate(value=5)
    assert m.value == 5


def test_cel_negate_minus_one_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELNegate(value=-1)  # -1 > -1 is False


def test_cel_negate_minus_two_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELNegate(value=-2)


# ---------------------------------------------------------------------------
# ValidatedCELIndex — index operator this[i]
# ---------------------------------------------------------------------------


def test_cel_index_valid():
    m = ValidatedCELIndex(items=["admin", "user"])
    assert m.items == ["admin", "user"]


def test_cel_index_wrong_first_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIndex(items=["user", "admin"])


def test_cel_index_empty_invalid():
    # size() > 0 is False → whole conjunction is False → raises
    with pytest.raises(ValidationError):
        ValidatedCELIndex(items=[])


# ---------------------------------------------------------------------------
# ValidatedCELInList — in operator with list literal
# ---------------------------------------------------------------------------


def test_cel_in_list_admin_valid():
    m = ValidatedCELInList(role="admin")
    assert m.role == "admin"


def test_cel_in_list_editor_valid():
    m = ValidatedCELInList(role="editor")
    assert m.role == "editor"


def test_cel_in_list_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELInList(role="superuser")


# ---------------------------------------------------------------------------
# ValidatedCELNullCheck — null ident: this.name != null at message level
# ---------------------------------------------------------------------------


def test_cel_null_check_set_valid():
    m = ValidatedCELNullCheck(name="Alice")
    assert m.name == "Alice"


def test_cel_null_check_none_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELNullCheck()  # name is None → self.name != None is False


# ---------------------------------------------------------------------------
# ValidatedCELUint — uint32 field; uint64 literal in CEL AST
# ---------------------------------------------------------------------------


def test_cel_uint_positive_valid():
    m = ValidatedCELUint(count=10)
    assert m.count == 10


def test_cel_uint_explicit_zero_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELUint(count=0)


def test_cel_uint_default_not_validated():
    m = ValidatedCELUint()  # default 0 is not explicitly validated
    assert m.count == 0


# ---------------------------------------------------------------------------
# ValidatedCELFloatLiteral — float64 literal (0.5) in CEL expression
# ---------------------------------------------------------------------------


def test_cel_float_literal_valid():
    m = ValidatedCELFloatLiteral(score=0.6)
    assert m.score == 0.6


def test_cel_float_literal_exact_invalid():
    # 0.5 is not strictly greater than 0.5
    with pytest.raises(ValidationError):
        ValidatedCELFloatLiteral(score=0.5)


def test_cel_float_literal_below_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELFloatLiteral(score=0.1)


# ---------------------------------------------------------------------------
# ValidatedCELGlobalSize — size() as a global call (not member form)
# ---------------------------------------------------------------------------


def test_cel_global_size_valid():
    m = ValidatedCELGlobalSize(tags=["x", "y"])
    assert m.tags == ["x", "y"]


def test_cel_global_size_explicit_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELGlobalSize(tags=[])


def test_cel_global_size_default_not_validated():
    m = ValidatedCELGlobalSize()  # default [] not validated
    assert m.tags == []


# ---------------------------------------------------------------------------
# ValidatedCELCastInt — int() global type-cast function
# ---------------------------------------------------------------------------


def test_cel_cast_int_positive_valid():
    m = ValidatedCELCastInt(fraction=2.9)  # int(2.9) = 2 >= 0 → passes
    assert m.fraction == 2.9


def test_cel_cast_int_zero_fraction_valid():
    m = ValidatedCELCastInt(fraction=0.9)  # int(0.9) = 0 >= 0 → passes
    assert m.fraction == 0.9


def test_cel_cast_int_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELCastInt(fraction=-1.5)  # int(-1.5) = -1 < 0 → fails


# ---------------------------------------------------------------------------
# ValidatedCELIsInfDir — isInf(direction) 1-arg form
# ---------------------------------------------------------------------------


def test_cel_is_inf_dir_normal_valid():
    m = ValidatedCELIsInfDir(value=1.0, magnitude=2.0)
    assert m.value == 1.0


def test_cel_is_inf_dir_neg_inf_value_valid():
    # value field forbids +inf; -inf is fine
    m = ValidatedCELIsInfDir(value=float("-inf"), magnitude=1.0)
    assert m.value == float("-inf")


def test_cel_is_inf_dir_pos_inf_value_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsInfDir(value=float("inf"), magnitude=1.0)


def test_cel_is_inf_dir_pos_inf_magnitude_valid():
    # magnitude field forbids -inf; +inf is fine
    m = ValidatedCELIsInfDir(value=1.0, magnitude=float("inf"))
    assert m.magnitude == float("inf")


def test_cel_is_inf_dir_neg_inf_magnitude_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsInfDir(value=1.0, magnitude=float("-inf"))


# ---------------------------------------------------------------------------
# ValidatedCELIsIpPrefixV6 — isIpPrefix(version) 1-arg form
# ---------------------------------------------------------------------------


def test_cel_is_ip_prefix_v6_valid():
    m = ValidatedCELIsIpPrefixV6(prefix="2001:db8::/32")
    assert m.prefix == "2001:db8::/32"


def test_cel_is_ip_prefix_v6_ipv4_rejected():
    with pytest.raises(ValidationError):
        ValidatedCELIsIpPrefixV6(prefix="192.168.0.0/24")  # IPv4, not IPv6


def test_cel_is_ip_prefix_v6_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELIsIpPrefixV6(prefix="notaprefix")


# ---------------------------------------------------------------------------
# ValidatedCELTsDate — getDate() (1-indexed, distinct from getDayOfMonth)
# ---------------------------------------------------------------------------


def test_cel_ts_date_none_valid():
    assert ValidatedCELTsDate().t is None


def test_cel_ts_date_valid():
    t = _dt_datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc)  # day 15 → v.day==15
    assert ValidatedCELTsDate(t=t).t == t


def test_cel_ts_date_invalid():
    t = _dt_datetime(2024, 1, 14, 0, 0, tzinfo=timezone.utc)  # day 14 → fails
    with pytest.raises(ValidationError):
        ValidatedCELTsDate(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsMinutes — getMinutes() on Timestamp
# ---------------------------------------------------------------------------


def test_cel_ts_minutes_none_valid():
    assert ValidatedCELTsMinutes().t is None


def test_cel_ts_minutes_valid():
    t = _dt_datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)  # minute=0
    assert ValidatedCELTsMinutes(t=t).t == t


def test_cel_ts_minutes_invalid():
    t = _dt_datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)  # minute=30
    with pytest.raises(ValidationError):
        ValidatedCELTsMinutes(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELTsSeconds — getSeconds() on Timestamp
# ---------------------------------------------------------------------------


def test_cel_ts_seconds_none_valid():
    assert ValidatedCELTsSeconds().t is None


def test_cel_ts_seconds_valid():
    t = _dt_datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # second=0
    assert ValidatedCELTsSeconds(t=t).t == t


def test_cel_ts_seconds_invalid():
    t = _dt_datetime(2024, 1, 1, 12, 0, 45, tzinfo=timezone.utc)  # second=45
    with pytest.raises(ValidationError):
        ValidatedCELTsSeconds(t=t)


# ---------------------------------------------------------------------------
# ValidatedCELBool — bool field; exercises celTypeForKind BoolKind
# ---------------------------------------------------------------------------


def test_cel_bool_true_valid():
    m = ValidatedCELBool(active=True)
    assert m.active is True


def test_cel_bool_default_not_validated():
    m = ValidatedCELBool()  # default False is not explicitly validated
    assert m.active is False


def test_cel_bool_explicit_false_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELBool(active=False)


# ---------------------------------------------------------------------------
# ValidatedCELBytes — bytes field; exercises celTypeForKind BytesKind
# ---------------------------------------------------------------------------


def test_cel_bytes_valid():
    m = ValidatedCELBytes(data=b"hello")
    assert m.data == b"hello"


def test_cel_bytes_default_not_validated():
    m = ValidatedCELBytes()  # default b"" is not explicitly validated
    assert m.data == b""


def test_cel_bytes_explicit_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELBytes(data=b"")


# ---------------------------------------------------------------------------
# ValidatedCELMapLiteral — map literal {k: v}; covers mapExpr (was 0%)
# ---------------------------------------------------------------------------


def test_cel_map_literal_admin_valid():
    m = ValidatedCELMapLiteral(role="admin")
    assert m.role == "admin"


def test_cel_map_literal_editor_valid():
    m = ValidatedCELMapLiteral(role="editor")
    assert m.role == "editor"


def test_cel_map_literal_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELMapLiteral(role="superuser")


def test_cel_map_literal_default_not_validated():
    m = ValidatedCELMapLiteral()  # default "" not validated
    assert m.role == ""


# ---------------------------------------------------------------------------
# ValidatedCELCastDouble — double() global cast
# ---------------------------------------------------------------------------


def test_cel_cast_double_valid():
    m = ValidatedCELCastDouble(value=5)  # float(5) = 5.0 < 10.0
    assert m.value == 5


def test_cel_cast_double_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELCastDouble(value=15)  # 15.0 < 10.0 is False


def test_cel_cast_double_default_not_validated():
    m = ValidatedCELCastDouble()  # default 0 not validated
    assert m.value == 0


# ---------------------------------------------------------------------------
# ValidatedCELCastString — string() global cast
# ---------------------------------------------------------------------------


def test_cel_cast_string_valid():
    m = ValidatedCELCastString(code=5)  # str(5)="5", "5"!="0"
    assert m.code == 5


def test_cel_cast_string_zero_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELCastString(code=0)  # str(0)="0", "0"!="0" is False


def test_cel_cast_string_default_not_validated():
    m = ValidatedCELCastString()  # default 0 not validated
    assert m.code == 0


# ---------------------------------------------------------------------------
# ValidatedCELCastUint — uint() global cast
# ---------------------------------------------------------------------------


def test_cel_cast_uint_valid():
    m = ValidatedCELCastUint(count=5)  # int(5) > 0
    assert m.count == 5


def test_cel_cast_uint_zero_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELCastUint(count=0)  # int(0) > 0 is False


def test_cel_cast_uint_default_not_validated():
    m = ValidatedCELCastUint()  # default 0 not validated
    assert m.count == 0


# ---------------------------------------------------------------------------
# ValidatedCELMapField — map<K,V> field; covers celFieldKey/celTypeForField IsMap
# ---------------------------------------------------------------------------


def test_cel_map_field_valid():
    m = ValidatedCELMapField(labels={"env": 1})
    assert m.labels == {"env": 1}


def test_cel_map_field_explicit_empty_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELMapField(labels={})


def test_cel_map_field_default_not_validated():
    m = ValidatedCELMapField()  # default {} not validated
    assert m.labels == {}


# ---------------------------------------------------------------------------
# ValidatedCELEnum — enum field; covers celTypeForKind EnumKind
# The constraint string(this) != "" trivially passes for all enum members;
# these tests verify the class is generated correctly and importable.
# ---------------------------------------------------------------------------


def test_cel_enum_default_valid():
    m = ValidatedCELEnum()  # priority=None; str(None)="None", "None"!="" → True
    assert m.priority is None


def test_cel_enum_set_valid():
    m = ValidatedCELEnum(priority=ValidatedCELEnum.Priority.HIGH)
    assert m.priority == ValidatedCELEnum.Priority.HIGH


# ---------------------------------------------------------------------------
# ValidatedCELExprField — field-level cel_expression shorthand (int32)
# ---------------------------------------------------------------------------


def test_cel_expr_field_valid():
    m = ValidatedCELExprField(age=1)
    assert m.age == 1


def test_cel_expr_field_zero_default_not_validated():
    # Proto3 zero default is not validated by Pydantic by default.
    m = ValidatedCELExprField()
    assert m.age == 0


def test_cel_expr_field_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExprField(age=-1)


def test_cel_expr_field_zero_explicit_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExprField(age=0)


def test_cel_expr_field_no_dropped_comment():
    # cel_expression shorthand must be transpiled, not dropped.
    text = _GEN_VALIDATE.read_text()
    assert 'cel id="this > 0" (not translated' not in text


def test_cel_expr_field_error_message_is_expression():
    # The validation error message must contain the CEL expression itself.
    with pytest.raises(ValidationError) as exc_info:
        ValidatedCELExprField(age=-1)
    assert "this > 0" in str(exc_info.value)


# ---------------------------------------------------------------------------
# ValidatedCELExprFieldString — cel_expression shorthand (string, size check)
# ---------------------------------------------------------------------------


def test_cel_expr_field_string_valid():
    m = ValidatedCELExprFieldString(label="hello")
    assert m.label == "hello"


def test_cel_expr_field_string_too_short_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExprFieldString(label="ab")


def test_cel_expr_field_string_exact_boundary_invalid():
    # size() > 3 means exactly 3 chars is still invalid.
    with pytest.raises(ValidationError):
        ValidatedCELExprFieldString(label="abc")


def test_cel_expr_field_string_four_chars_valid():
    m = ValidatedCELExprFieldString(label="abcd")
    assert m.label == "abcd"


# ---------------------------------------------------------------------------
# ValidatedCELExprFieldMulti — two cel_expression entries on the same field
# ---------------------------------------------------------------------------


def test_cel_expr_field_multi_valid():
    m = ValidatedCELExprFieldMulti(score=50)
    assert m.score == 50


def test_cel_expr_field_multi_lower_bound_invalid():
    # this > 0 fails for score=0.
    with pytest.raises(ValidationError):
        ValidatedCELExprFieldMulti(score=0)


def test_cel_expr_field_multi_negative_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExprFieldMulti(score=-1)


def test_cel_expr_field_multi_upper_bound_invalid():
    # this <= 100 fails for score=101.
    with pytest.raises(ValidationError):
        ValidatedCELExprFieldMulti(score=101)


def test_cel_expr_field_multi_boundary_valid():
    m = ValidatedCELExprFieldMulti(score=100)
    assert m.score == 100


# ---------------------------------------------------------------------------
# ValidatedCELExprMessage — message-level cel_expression cross-field rule
# ---------------------------------------------------------------------------


def test_cel_expr_message_valid():
    m = ValidatedCELExprMessage(min_val=1, max_val=5)
    assert m.min_val == 1
    assert m.max_val == 5


def test_cel_expr_message_equal_valid():
    # min_val <= max_val also allows equality.
    m = ValidatedCELExprMessage(min_val=3, max_val=3)
    assert m.min_val == 3


def test_cel_expr_message_inverted_invalid():
    with pytest.raises(ValidationError):
        ValidatedCELExprMessage(min_val=5, max_val=1)


def test_cel_expr_message_no_dropped_comment():
    text = _GEN_VALIDATE.read_text()
    assert 'cel id="this.min_val <= this.max_val" (not translated' not in text


def test_cel_expr_message_error_message_is_expression():
    # The validation error message must contain the CEL expression itself.
    with pytest.raises(ValidationError) as exc_info:
        ValidatedCELExprMessage(min_val=5, max_val=1)
    assert "this.min_val <= this.max_val" in str(exc_info.value)


# ---------------------------------------------------------------------------
# ValidatedCELExprMessageMulti — two message-level cel_expression entries
# ---------------------------------------------------------------------------


def test_cel_expr_message_multi_valid():
    m = ValidatedCELExprMessageMulti(a=1, b=2, c=3)
    assert m.a == 1


def test_cel_expr_message_multi_all_equal_valid():
    m = ValidatedCELExprMessageMulti(a=2, b=2, c=2)
    assert m.b == 2


def test_cel_expr_message_multi_first_rule_invalid():
    # a <= b fails: a=5, b=2.
    with pytest.raises(ValidationError):
        ValidatedCELExprMessageMulti(a=5, b=2, c=3)


def test_cel_expr_message_multi_second_rule_invalid():
    # b <= c fails: b=3, c=1.
    with pytest.raises(ValidationError):
        ValidatedCELExprMessageMulti(a=1, b=3, c=1)


# ---------------------------------------------------------------------------
# ValidatedCELExprFieldDropped — untranslatable field-level cel_expression
# ---------------------------------------------------------------------------


def test_cel_expr_field_dropped_accepts_any_value():
    # The cel_expression cannot be transpiled; no validator is generated.
    m = ValidatedCELExprFieldDropped(tag="hello")
    assert m.tag == "hello"


def test_cel_expr_field_dropped_comment_in_generated_file():
    # The drop path must emit a # buf.validate comment with the expression id.
    text = _GEN_VALIDATE.read_text()
    assert 'cel id="this.lowerAscii() != \\"\\""' in text


# ---------------------------------------------------------------------------
# ValidatedCELExprMessageDropped — untranslatable message-level cel_expression
# ---------------------------------------------------------------------------


def test_cel_expr_message_dropped_accepts_any_value():
    # The cel_expression cannot be transpiled; no @model_validator is generated.
    m = ValidatedCELExprMessageDropped(name="hello")
    assert m.name == "hello"


def test_cel_expr_message_dropped_comment_in_generated_file():
    # The drop path must emit a # buf.validate comment with the expression id.
    text = _GEN_VALIDATE.read_text()
    assert 'cel id="this.name.lowerAscii() != \\"\\""' in text


# ---------------------------------------------------------------------------
# ValidatedCELInsideItems — cel / cel_expression inside repeated.items
# ---------------------------------------------------------------------------


def test_cel_inside_items_accepts_values():
    # No validators are generated — the constraints are dropped with comments.
    m = ValidatedCELInsideItems(scores=[0, -1], ratings=[0, -1])
    assert m.scores == [0, -1]
    assert m.ratings == [0, -1]


def test_cel_inside_items_cel_drop_comment():
    # cel inside repeated.items must emit a # buf.validate: cel (not translated) comment.
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: cel (not translated)" in text


def test_cel_inside_items_cel_expression_drop_comment():
    # cel_expression inside repeated.items must emit a drop comment, not be silently ignored.
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: cel_expression (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedCELInsideMapValues — cel_expression inside map.values
# ---------------------------------------------------------------------------


def test_cel_inside_map_values_accepts_values():
    # No validators generated — dropped with a comment.
    m = ValidatedCELInsideMapValues(counters={"x": 0, "y": -1})
    assert m.counters == {"x": 0, "y": -1}


def test_cel_inside_map_values_drop_comment():
    # cel_expression inside map.values must emit a drop comment on the outer field.
    text = _GEN_VALIDATE.read_text()
    # The comment appears once for items (scores field) and once here; check presence.
    assert text.count("# buf.validate: cel_expression (not translated)") >= 2
