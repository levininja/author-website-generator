import subprocess
from typing import Sequence


def default_runner(args: Sequence[str]) -> None:
    subprocess.run(list(args), check=True, capture_output=True, text=True)


def default_capture_runner(args: Sequence[str]) -> str:
    result = subprocess.run(list(args), check=True, capture_output=True, text=True)
    return result.stdout.strip()
