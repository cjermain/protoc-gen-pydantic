import subprocess


def test_ruff_format(generated_file):
    """Generated code must be ruff-format clean."""
    result = subprocess.run(
        ["ruff", "format", "--check", str(generated_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"ruff format diff:\n{result.stderr or result.stdout}"
    )
