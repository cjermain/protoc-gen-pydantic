from api.v1.nested_comments_pydantic import (
    Outer,
    Outer_Inner,
    Outer_Inner_Deepest,
    Outer_Inner_InnerEnum,
    Outer_OuterEnum,
)


def test_outer_message_comments():
    assert "Outer message comment." in Outer.__doc__
    assert "Outer field comment." in Outer.model_fields["outer_field"].description


def test_inner_message_comments():
    assert "Inner message comment." in Outer_Inner.__doc__
    assert "Inner field comment." in Outer_Inner.model_fields["inner_field"].description


def test_deepest_message_comments():
    assert "Deepest message comment." in Outer_Inner_Deepest.__doc__
    assert (
        "Deepest field comment."
        in Outer_Inner_Deepest.model_fields["deepest_field"].description
    )


def test_outer_enum_comments():
    assert "Outer enum comment." in Outer_OuterEnum.__doc__


def test_inner_enum_comments():
    assert "Inner enum comment." in Outer_Inner_InnerEnum.__doc__
