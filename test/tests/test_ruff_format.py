import subprocess
from pathlib import Path

import pytest

GENERATED_FILES = sorted(
    list(Path("gen").rglob("*_pydantic.py"))
    + list(Path("gen_options").rglob("*_pydantic.py"))
    + list(Path("gen").rglob("_proto_types.py"))
    + list(Path("gen_options").rglob("_proto_types.py"))
)


@pytest.mark.parametrize("file_path", GENERATED_FILES, ids=lambda p: str(p))
def test_ruff_format(file_path):
    """Generated code must be ruff-format clean."""
    result = subprocess.run(
        ["ruff", "format", "--check", str(file_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"ruff format diff:\n{result.stderr or result.stdout}"
    )
