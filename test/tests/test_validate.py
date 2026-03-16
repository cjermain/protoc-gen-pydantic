from pathlib import Path

import pytest
from pydantic import ValidationError

import datetime

from api.v1.validate_pydantic import (
    ValidatedBytes,
    ValidatedBytesIP,
    ValidatedCEL,
    ValidatedCELCrossField,
    ValidatedCELDropped,
    ValidatedCELField,
    ValidatedCELHas,
    ValidatedCELIsEmail,
    ValidatedCELIsHostAndPort,
    ValidatedCELIsHostname,
    ValidatedCELIsIp,
    ValidatedCELIsIpPrefix,
    ValidatedCELIsNanInf,
    ValidatedCELIsUri,
    ValidatedCELMessage,
    ValidatedCELStringReturn,
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


def test_validated_cel_no_dropped_comment():
    # After transpilation the simple "this > 0" should not appear as dropped.
    text = _GEN_VALIDATE.read_text()
    # The old generic drop comment must not appear for the simple CEL case.
    assert "# buf.validate: cel (not translated)" not in text


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
# ValidatedCELDropped — drop path for unsupported CEL (comprehension)
# ---------------------------------------------------------------------------


def test_cel_dropped_comment_in_generated_file():
    text = Path("gen/api/v1/validate_pydantic.py").read_text()
    assert 'cel id="all_positive" (not translated' in text


def test_cel_dropped_no_validation():
    # Unsupported CEL (comprehension) is dropped; the field has no constraint.
    m = ValidatedCELDropped(scores=[1, -2, 3])
    assert m.scores == [1, -2, 3]  # no error — constraint was not translated


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
