import subprocess
from typing import Sequence


def default_runner(args: Sequence[str]) -> None:
    subprocess.run(list(args), check=True, capture_output=True, text=True)


def default_capture_runner(args: Sequence[str]) -> str:
    result = subprocess.run(list(args), check=True, capture_output=True, text=True)
    # WP-CLI may emit PHP deprecation warnings to stdout before the actual output.
    # Take the last non-empty line, which is always the real porcelain result.
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return lines[-1].strip() if lines else ""
