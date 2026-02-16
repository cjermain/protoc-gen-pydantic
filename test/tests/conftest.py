import datetime
import subprocess
from pathlib import Path

import pytest

from api.v1.enums_pydantic import Enum
from api.v1.types_pydantic import Foo, Foo_NestedEnum, Foo_NestedMessage, Message

# Directory paths relative to the test root (test/)
_TEST_ROOT = Path(__file__).resolve().parent.parent
_GEN_PB2_DIR = _TEST_ROOT / "gen_pb2"
_PROTO_DIR = _TEST_ROOT / "proto"


def pytest_configure(config):
    """Generate protobuf Python files on-the-fly before test collection."""
    if _GEN_PB2_DIR.exists():
        return
    _GEN_PB2_DIR.mkdir(parents=True, exist_ok=True)
    proto_files = list(_PROTO_DIR.rglob("*.proto"))
    subprocess.check_call(
        [
            "protoc",
            f"--proto_path={_PROTO_DIR}",
            f"--python_out={_GEN_PB2_DIR}",
            *[str(p.relative_to(_PROTO_DIR)) for p in proto_files],
        ],
    )


@pytest.fixture
def timestamp():
    return datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=datetime.timezone.utc)


@pytest.fixture
def message():
    return Message(first_name="John", last_name="Doe")


@pytest.fixture
def nested_message():
    return Foo_NestedMessage(first_name="Jane", last_name="Doe")


@pytest.fixture
def foo_kwargs(timestamp, message, nested_message):
    return dict(
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
        nested_enum=Foo_NestedEnum.ACTIVE,
        message=message,
        nested_message=nested_message,
        wkt_timestamp=timestamp,
        # repeated
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
        nested_enum_repeated=[Foo_NestedEnum.INACTIVE],
        message_repeated=[message],
        nested_message_repeated=[nested_message],
        wkt_timestamp_repeated=[timestamp],
        # maps – key types
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
        # maps – value types
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
        nested_enum_map_value={"a": Foo_NestedEnum.ACTIVE},
        message_map_value={"a": message},
        nested_message_map_value={"a": nested_message},
        wkt_timestamp_map_value={"a": timestamp},
    )


@pytest.fixture
def foo(foo_kwargs):
    return Foo(**foo_kwargs)
