import subprocess
from collections.abc import Sequence


def default_runner(args: Sequence[str]) -> None:
    """Run a subprocess command and raise if it fails."""
    subprocess.run(list(args), check=True, capture_output=True, text=True)


def default_capture_runner(args: Sequence[str]) -> str:
    """Run a subprocess command and return its final non-empty stdout line."""
    result = subprocess.run(list(args), check=True, capture_output=True, text=True)
    # WP-CLI may emit PHP deprecation warnings to stdout before the actual output.
    # Take the last non-empty line, which is always the real porcelain result.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return lines[-1].strip() if lines else ""
