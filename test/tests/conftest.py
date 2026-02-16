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
    return Message(firstName="John", lastName="Doe")


@pytest.fixture
def nested_message():
    return Foo_NestedMessage(firstName="Jane", lastName="Doe")


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
        nestedEnum=Foo_NestedEnum.ACTIVE,
        message=message,
        nestedMessage=nested_message,
        wktTimestamp=timestamp,
        # repeated
        int32Repeated=[1, 2],
        int64Repeated=[3, 4],
        uint32Repeated=[5],
        uint64Repeated=[6],
        fixed32Repeated=[7],
        fixed64Repeated=[8],
        sint32Repeated=[9],
        sint64Repeated=[10],
        sfixed32Repeated=[11],
        sfixed64Repeated=[12],
        boolRepeated=[True, False],
        floatRepeated=[1.0],
        doubleRepeated=[2.0],
        stringRepeated=["a"],
        bytesRepeated=[b"b"],
        enumRepeated=[Enum.INACTIVE],
        nestedEnumRepeated=[Foo_NestedEnum.INACTIVE],
        messageRepeated=[message],
        nestedMessageRepeated=[nested_message],
        wktTimestampRepeated=[timestamp],
        # maps – key types
        int32MapKey={1: "a"},
        int64MapKey={2: "b"},
        uint32MapKey={3: "c"},
        uint64MapKey={4: "d"},
        fixed32MapKey={5: "e"},
        fixed64MapKey={6: "f"},
        sint32MapKey={7: "g"},
        sint64MapKey={8: "h"},
        sfixed32MapKey={9: "i"},
        sfixed64MapKey={10: "j"},
        boolMapKey={True: "k"},
        stringMapKey={"key": "val"},
        # maps – value types
        int32MapValue={"a": 1},
        int64MapValue={"a": 2},
        uint32MapValue={"a": 3},
        uint64MapValue={"a": 4},
        fixed32MapValue={"a": 5},
        fixed64MapValue={"a": 6},
        sint32MapValue={"a": 7},
        sint64MapValue={"a": 8},
        sfixed32MapValue={"a": 9},
        sfixed64MapValue={"a": 10},
        boolMapValue={"a": True},
        floatMapValue={"a": 1.0},
        doubleMapValue={"a": 2.0},
        stringMapValue={"a": "b"},
        bytesMapValue={"a": b"c"},
        enumMapValue={"a": Enum.ACTIVE},
        nestedEnumMapValue={"a": Foo_NestedEnum.ACTIVE},
        messageMapValue={"a": message},
        nestedMessageMapValue={"a": nested_message},
        wktTimestampMapValue={"a": timestamp},
    )


@pytest.fixture
def foo(foo_kwargs):
    return Foo(**foo_kwargs)
