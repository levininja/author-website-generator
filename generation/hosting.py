"""Atomic site deployment and local PHP preview server management."""

import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

PHP_SERVER_HOST = "localhost"
PHP_SERVER_PORT = 8080
PREVIEW_URL = f"http://{PHP_SERVER_HOST}:{PHP_SERVER_PORT}"

DEFAULT_HOSTED_SITE_PATH = str(Path(__file__).parent.parent / "hosted-site")

# Module-level reference to the currently-running PHP preview server process.
# Only one site is hosted at a time, so a single process handle is sufficient.
_php_process: subprocess.Popen | None = None


def get_hosted_site_path() -> str:
    """Return the fixed path where the hosted site lives, overridable via env var."""
    return os.environ.get("WP_HOSTED_SITE_PATH", DEFAULT_HOSTED_SITE_PATH)


def deploy_site(staging_path: str, hosted_path: str) -> None:
    """Atomically replace the hosted site with the fully-written staged site.

    The old hosted directory is only removed AFTER staging_path is known to be
    complete (the caller's responsibility — deploy_site must not be called until
    the generation pipeline has finished writing all files). staging_path is
    consumed (moved) so callers must not reference it after this returns.
    """
    if os.path.exists(hosted_path):
        shutil.rmtree(hosted_path)
    shutil.move(staging_path, hosted_path)


def start_php_server(
    hosted_path: str,
    popen_fn: Callable | None = None,
) -> None:
    """Start the PHP built-in server to serve hosted_path on port 8080.

    Terminates any previously-started PHP preview server before launching the new
    one. popen_fn is injectable so unit tests do not spawn a real OS process.
    """
    global _php_process
    if _php_process is not None:
        _php_process.terminate()
        _php_process.wait()
        _php_process = None

    popen = popen_fn or subprocess.Popen
    _php_process = popen(
        ["php", "-S", f"{PHP_SERVER_HOST}:{PHP_SERVER_PORT}", "-t", hosted_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def host_site(
    staging_path: str,
    hosted_path: str | None = None,
    popen_fn: Callable | None = None,
) -> None:
    """Deploy the staged site atomically and start the PHP preview server.

    Called after the generation pipeline completes successfully.
    hosted_path defaults to get_hosted_site_path() when not supplied.
    """
    if hosted_path is None:
        hosted_path = get_hosted_site_path()
    deploy_site(staging_path, hosted_path)
    start_php_server(hosted_path, popen_fn=popen_fn)
