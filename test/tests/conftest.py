import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from api.v1.enums_pydantic import Enum
from api.v1.messages_pydantic import Message
from api.v1.scalars_pydantic import Scalars

# Directory paths relative to the test root (test/)
_TEST_ROOT = Path(__file__).resolve().parent.parent
_GEN_PB2_DIR = _TEST_ROOT / "gen_pb2"
_PROTO_DIR = _TEST_ROOT / "proto"

_GENERATED_FILES = sorted(
    list(Path("gen").rglob("*_pydantic.py"))
    + list(Path("gen_options").rglob("*_pydantic.py"))
    + list(Path("gen").rglob("_proto_types.py"))
    + list(Path("gen_options").rglob("_proto_types.py"))
)


@pytest.fixture(params=_GENERATED_FILES, ids=str)
def generated_file(request):
    return request.param


def pytest_configure(config):
    """Generate protobuf Python files on-the-fly before test collection."""
    if _GEN_PB2_DIR.exists():
        return
    _GEN_PB2_DIR.mkdir(parents=True, exist_ok=True)

    def _has_bsr_imports(p: Path) -> bool:
        import re

        return bool(re.search(r'^\s*import\s+"buf/', p.read_text(), re.MULTILINE))

    proto_files = [p for p in _PROTO_DIR.rglob("*.proto") if not _has_bsr_imports(p)]
    subprocess.check_call(
        [
            "protoc",
            f"--proto_path={_PROTO_DIR}",
            f"--python_out={_GEN_PB2_DIR}",
            *[str(p.relative_to(_PROTO_DIR)) for p in proto_files],
        ],
    )


@pytest.fixture(scope="session")
def load_module():
    return _load_module


def _load_module(name, filepath):
    """Load a module from an arbitrary path under a unique name to avoid conflicts."""
    full_name = f"gen_options_test.{name}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {filepath}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def make_scalars(**overrides):
    """Create a Scalars instance with non-zero defaults; override as needed."""
    defaults = dict(
        int32=1,
        int64=2,
        uint32=3,
        uint64=4,
        fixed32=5,
        fixed64=6,
        sint32=7,
        sint64=8,
        sfixed32=9,
        sfixed64=10,
        bool_=True,
        float_=1.5,
        double=2.5,
        string="hello",
        bytes_=b"world",
        enum=Enum.ACTIVE,
        nested_enum=Scalars.NestedEnum.ACTIVE,
        message=Message(first_name="John", last_name="Doe"),
        nested_message=Scalars.NestedMessage(first_name="Jane", last_name="Doe"),
    )
    return Scalars(**{**defaults, **overrides})


def make_collections(**overrides):
    """Create a Collections instance with sample data; override as needed."""
    from api.v1.collections_pydantic import Collections

    defaults = dict(
        int32_repeated=[1, 2],
        int64_repeated=[3, 4],
        uint32_repeated=[5],
        uint64_repeated=[6],
        fixed32_repeated=[7],
        fixed64_repeated=[8],
        sint32_repeated=[9],
        sint64_repeated=[10],
        sfixed32_repeated=[11],
        sfixed64_repeated=[12],
        bool_repeated=[True, False],
        float_repeated=[1.0],
        double_repeated=[2.0],
        string_repeated=["a"],
        bytes_repeated=[b"b"],
        enum_repeated=[Enum.INACTIVE],
        nested_enum_repeated=[Scalars.NestedEnum.INACTIVE],
        message_repeated=[Message(first_name="John", last_name="Doe")],
        nested_message_repeated=[
            Scalars.NestedMessage(first_name="Jane", last_name="Doe")
        ],
        int32_map_key={1: "a"},
        int64_map_key={2: "b"},
        uint32_map_key={3: "c"},
        uint64_map_key={4: "d"},
        fixed32_map_key={5: "e"},
        fixed64_map_key={6: "f"},
        sint32_map_key={7: "g"},
        sint64_map_key={8: "h"},
        sfixed32_map_key={9: "i"},
        sfixed64_map_key={10: "j"},
        bool_map_key={True: "k"},
        string_map_key={"key": "val"},
        int32_map_value={"a": 1},
        int64_map_value={"a": 2},
        uint32_map_value={"a": 3},
        uint64_map_value={"a": 4},
        fixed32_map_value={"a": 5},
        fixed64_map_value={"a": 6},
        sint32_map_value={"a": 7},
        sint64_map_value={"a": 8},
        sfixed32_map_value={"a": 9},
        sfixed64_map_value={"a": 10},
        bool_map_value={"a": True},
        float_map_value={"a": 1.0},
        double_map_value={"a": 2.0},
        string_map_value={"a": "b"},
        bytes_map_value={"a": b"c"},
        enum_map_value={"a": Enum.ACTIVE},
        nested_enum_map_value={"a": Scalars.NestedEnum.ACTIVE},
        message_map_value={"a": Message(first_name="John", last_name="Doe")},
        nested_message_map_value={
            "a": Scalars.NestedMessage(first_name="Jane", last_name="Doe")
        },
    )
    return Collections(**{**defaults, **overrides})


@pytest.fixture
def message():
    return Message(first_name="John", last_name="Doe")


@pytest.fixture
def nested_message():
    return Scalars.NestedMessage(first_name="Jane", last_name="Doe")
