import subprocess


def test_ty(generated_file):
    """Generated code must be ty clean."""
    result = subprocess.run(
        ["ty", "check", str(generated_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"ty errors:\n{result.stderr or result.stdout}"
