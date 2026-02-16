from foo.bar.v1.cross_options_pydantic import Language


def test_cross_proto_display_name():
    assert Language.PYTHON.options.display_name == "Python"
    assert Language.GOLANG.options.display_name == "Golang"
    assert Language.RUST.options.display_name == "Rust"


def test_cross_proto_priority():
    assert Language.RUST.options.priority == 1
    assert Language.PYTHON.options.priority is None


def test_cross_proto_defaults_none():
    assert Language.UNSPECIFIED.options.display_name is None
    assert Language.UNSPECIFIED.options.priority is None
    assert Language.UNSPECIFIED.options.is_default is None
