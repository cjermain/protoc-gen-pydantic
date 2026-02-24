from pathlib import Path

import pytest
from pydantic import ValidationError

import datetime

from api.v1.validate_pydantic import (
    ValidatedBytes,
    ValidatedConst,
    ValidatedDropped,
    ValidatedDuration,
    ValidatedExamples,
    ValidatedIn,
    ValidatedMap,
    ValidatedOneof,
    ValidatedRepeated,
    ValidatedReserved,
    ValidatedScalars,
    ValidatedFormats,
    ValidatedStringAffix,
    ValidatedStringContains,
    ValidatedStringLen,
    ValidatedStrings,
    ValidatedTimestamp,
    ValidatedUnique,
)


# ---------------------------------------------------------------------------
# ValidatedScalars
# ---------------------------------------------------------------------------


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
    # required = true is not translated; default empty string is accepted.
    d = ValidatedDropped()
    assert d.name == ""


def test_validated_dropped_bytes_const_not_enforced():
    # bytes.const is not translated (bytes kind unsupported); any bytes value is accepted.
    d = ValidatedDropped(blob=b"\xff")
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
    # Default empty strings skip validation (proto3 zero-value semantics).
    d = ValidatedFormats()
    assert d.email == ""
    assert d.website == ""
    assert d.address == ""
    assert d.token == ""
    assert d.host_v4 == ""
    assert d.host_v6 == ""
    assert d.ratio == pytest.approx(0.0)


def test_validated_format_finite_enforced_inf():
    with pytest.raises(ValidationError):
        ValidatedFormats(ratio=float("inf"))


def test_validated_format_finite_enforced_nan():
    with pytest.raises(ValidationError):
        ValidatedFormats(ratio=float("nan"))


def test_validated_format_finite_valid():
    d = ValidatedFormats(ratio=1.0)
    assert d.ratio == pytest.approx(1.0)


@pytest.mark.parametrize("email", ["user@example.com", "a@b.co", "x.y+z@domain.org"])
def test_validated_format_email_valid(email):
    d = ValidatedFormats(email=email)
    assert d.email == email


@pytest.mark.parametrize("email", ["notanemail", "@domain.com", "user@", "nodot@nodot"])
def test_validated_format_email_invalid(email):
    with pytest.raises(ValidationError):
        ValidatedFormats(email=email)


@pytest.mark.parametrize("uri", ["https://example.com", "http://x.org/path?q=1"])
def test_validated_format_uri_valid(uri):
    d = ValidatedFormats(website=uri)
    assert d.website == uri


@pytest.mark.parametrize("uri", ["notauri", "example.com", "ftp//missing-colon"])
def test_validated_format_uri_invalid(uri):
    with pytest.raises(ValidationError):
        ValidatedFormats(website=uri)


@pytest.mark.parametrize("addr", ["1.2.3.4", "::1", "2001:db8::1"])
def test_validated_format_ip_valid(addr):
    d = ValidatedFormats(address=addr)
    assert d.address == addr


@pytest.mark.parametrize("addr", ["999.0.0.1", "not-an-ip", "256.1.1.1"])
def test_validated_format_ip_invalid(addr):
    with pytest.raises(ValidationError):
        ValidatedFormats(address=addr)


@pytest.mark.parametrize("v4", ["192.168.1.1", "0.0.0.0", "255.255.255.255"])
def test_validated_format_ipv4_valid(v4):
    d = ValidatedFormats(host_v4=v4)
    assert d.host_v4 == v4


@pytest.mark.parametrize("v4", ["::1", "not-an-ip", "256.0.0.1"])
def test_validated_format_ipv4_invalid(v4):
    with pytest.raises(ValidationError):
        ValidatedFormats(host_v4=v4)


@pytest.mark.parametrize("v6", ["::1", "2001:db8::1", "fe80::1"])
def test_validated_format_ipv6_valid(v6):
    d = ValidatedFormats(host_v6=v6)
    assert d.host_v6 == v6


@pytest.mark.parametrize("v6", ["1.2.3.4", "not-an-ip", "gggg::1"])
def test_validated_format_ipv6_invalid(v6):
    with pytest.raises(ValidationError):
        ValidatedFormats(host_v6=v6)


@pytest.mark.parametrize(
    "u",
    [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    ],
)
def test_validated_format_uuid_valid(u):
    d = ValidatedFormats(token=u)
    assert d.token == u


@pytest.mark.parametrize(
    "u", ["not-a-uuid", "12345", "550e8400-zzzz-41d4-a716-446655440000"]
)
def test_validated_format_uuid_invalid(u):
    with pytest.raises(ValidationError):
        ValidatedFormats(token=u)


# ---------------------------------------------------------------------------
# ValidatedStringLen — string.len → min_length=N, max_length=N (P2)
# ---------------------------------------------------------------------------


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


def test_validated_string_affix_prefix_valid():
    m = ValidatedStringAffix(url="https://example.com")
    assert m.url == "https://example.com"


def test_validated_string_affix_prefix_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(url="http://example.com")


def test_validated_string_affix_suffix_valid():
    m = ValidatedStringAffix(filename="main.go")
    assert m.filename == "main.go"


def test_validated_string_affix_suffix_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(filename="main.py")


def test_validated_string_affix_prefix_and_suffix_valid():
    m = ValidatedStringAffix(path="/home/user/notes.txt")
    assert m.path == "/home/user/notes.txt"


def test_validated_string_affix_prefix_and_suffix_invalid_prefix():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(path="/tmp/notes.txt")


def test_validated_string_affix_prefix_and_suffix_invalid_suffix():
    with pytest.raises(ValidationError):
        ValidatedStringAffix(path="/home/user/notes.py")


def test_validated_string_affix_conflict_pattern_wins():
    # content has both pattern and prefix; pattern is translated, prefix is dropped.
    # The explicit pattern ^[a-z]+$ is enforced.
    ValidatedStringAffix(content="abc")
    with pytest.raises(ValidationError):
        ValidatedStringAffix(content="ABC")


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
    assert "_Literal['fixed']" in text


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
    m = ValidatedIn(status="active")
    assert m.status == "active"


def test_validated_in_status_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(status="banned")


def test_validated_in_not_in_code_valid():
    m = ValidatedIn(code="approved")
    assert m.code == "approved"


def test_validated_in_not_in_code_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(code="deleted")


def test_validated_in_priority_valid():
    m = ValidatedIn(priority=1)
    assert m.priority == 1


def test_validated_in_priority_invalid():
    with pytest.raises(ValidationError):
        ValidatedIn(priority=5)


def test_validated_in_default_accepted():
    # AfterValidator does not run on defaults in Pydantic v2 — no error expected.
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


def test_validated_string_contains_topic_valid():
    m = ValidatedStringContains(topic="protobuf guide")
    assert m.topic == "protobuf guide"


def test_validated_string_contains_topic_invalid():
    with pytest.raises(ValidationError):
        ValidatedStringContains(topic="avro guide")


def test_validated_string_contains_label_prefix_only():
    # prefix is used; contains conflicts with prefix and is dropped
    m = ValidatedStringContains(label="env-prod-us")
    assert m.label == "env-prod-us"


def test_validated_string_contains_label_dropped_comment():
    text = _GEN_VALIDATE.read_text()
    assert "# buf.validate: contains (not translated)" in text


# ---------------------------------------------------------------------------
# ValidatedBytes — bytes min_len / len / max_len → min_length / max_length
# ---------------------------------------------------------------------------


def test_validated_bytes_token_valid():
    m = ValidatedBytes(token=b"x" * 16)
    assert m.token == b"x" * 16


def test_validated_bytes_token_too_short():
    with pytest.raises(ValidationError):
        ValidatedBytes(token=b"short")


def test_validated_bytes_hash_exact():
    # `hash` is a Python builtin → renamed to `hash_` with alias
    m = ValidatedBytes(hash=b"x" * 32)
    assert m.hash_ == b"x" * 32


def test_validated_bytes_hash_wrong_length():
    with pytest.raises(ValidationError):
        ValidatedBytes(hash=b"x" * 31)


def test_validated_bytes_payload_valid():
    m = ValidatedBytes(payload=b"x" * 1024)
    assert m.payload == b"x" * 1024


def test_validated_bytes_payload_too_large():
    with pytest.raises(ValidationError):
        ValidatedBytes(payload=b"x" * 1025)
