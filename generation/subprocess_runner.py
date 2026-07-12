import logging
import subprocess
from collections.abc import Sequence

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120


class GenerationTimeoutError(Exception):
    """Raised when a subprocess exceeds its allowed timeout."""


def default_runner(args: Sequence[str], timeout: int = DEFAULT_TIMEOUT) -> None:
    """Run a subprocess command and raise if it fails."""
    cmd = list(args)
    logger.debug("Running subprocess: %s", cmd)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise GenerationTimeoutError(
            f"Command {cmd} timed out after {timeout}s"
        ) from exc
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Subprocess failed (exit %d): %s\nstdout: %s\nstderr: %s",
            exc.returncode,
            cmd,
            exc.stdout,
            exc.stderr,
        )
        raise


def default_capture_runner(args: Sequence[str], timeout: int = DEFAULT_TIMEOUT) -> str:
    """Run a subprocess command and return its final non-empty stdout line."""
    cmd = list(args)
    logger.debug("Running subprocess: %s", cmd)
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise GenerationTimeoutError(
            f"Command {cmd} timed out after {timeout}s"
        ) from exc
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Subprocess failed (exit %d): %s\nstdout: %s\nstderr: %s",
            exc.returncode,
            cmd,
            exc.stdout,
            exc.stderr,
        )
        raise
    # WP-CLI may emit PHP deprecation warnings to stdout before the actual output.
    # Take the last non-empty line, which is always the real porcelain result.
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return lines[-1].strip() if lines else ""
