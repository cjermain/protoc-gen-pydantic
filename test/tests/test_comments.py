from api.v1.comments_pydantic import CommentedMessage, Outer


# --- CommentedMessage (top-level) ---


def test_commented_message_docstring():
    doc = CommentedMessage.__doc__
    assert "Leading comment on CommentedMessage." in doc
    assert "CommentedMessage exercises all comment positions." in doc


def test_commented_message_field_descriptions():
    first = CommentedMessage.model_fields["first_name"].description
    assert "Leading comment on first_name." in first
    assert "The given name of the person." in first

    last = CommentedMessage.model_fields["last_name"].description
    assert "Leading comment on last_name." in last
    assert "The family name of the person." in last


# --- CommentedMessage.NestedMessage ---


def test_nested_message_docstring():
    doc = CommentedMessage.NestedMessage.__doc__
    assert "Leading comment on NestedMessage." in doc
    assert "A message nested inside CommentedMessage." in doc


def test_nested_message_field_descriptions():
    first = CommentedMessage.NestedMessage.model_fields["first_name"].description
    assert "Leading comment on nested first_name." in first
    assert "The given name in the nested message." in first


# --- CommentedMessage.NestedEnum ---


def test_nested_enum_docstring():
    doc = CommentedMessage.NestedEnum.__doc__
    assert "Leading comment on NestedEnum." in doc
    assert "An enum nested inside CommentedMessage." in doc


# --- Outer/Inner/Deepest hierarchy ---


def test_outer_message_comments():
    assert "Outer message comment." in Outer.__doc__
    assert "Outer field comment." in Outer.model_fields["outer_field"].description


def test_inner_message_comments():
    assert "Inner message comment." in Outer.Inner.__doc__
    assert "Inner field comment." in Outer.Inner.model_fields["inner_field"].description


def test_deepest_message_comments():
    assert "Deepest message comment." in Outer.Inner.Deepest.__doc__
    assert (
        "Deepest field comment."
        in Outer.Inner.Deepest.model_fields["deepest_field"].description
    )


def test_outer_enum_comments():
    assert "Outer enum comment." in Outer.OuterEnum.__doc__


def test_inner_enum_comments():
    assert "Inner enum comment." in Outer.Inner.InnerEnum.__doc__
