import os
from collections.abc import Callable, Sequence
from pathlib import Path

from generation.subprocess_runner import default_runner

WP_CLI = "/usr/local/bin/wp"

# Default generated-site folder lives two levels up from this file (repo root).
DEFAULT_SITE_PATH = str(Path(__file__).parent.parent / "generated-site")


def get_site_path() -> str:
    """Return the generated-site path, overridable via WP_GENERATED_SITE_PATH env var."""
    return os.environ.get("WP_GENERATED_SITE_PATH", DEFAULT_SITE_PATH)


def install_wordpress(
    site_path: str,
    site_title: str,
    admin_user: str = "admin",
    admin_password: str = "admin",
    admin_email: str = "admin@example.com",
    site_url: str = "http://localhost:8080",
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Download WP core and run the installer into site_path."""
    run = runner or default_runner

    run([WP_CLI, "core", "download", f"--path={site_path}"])

    run([
        WP_CLI, "core", "install",
        f"--path={site_path}",
        f"--url={site_url}",
        f"--title={site_title}",
        f"--admin_user={admin_user}",
        f"--admin_password={admin_password}",
        f"--admin_email={admin_email}",
        "--skip-email",
    ])


def configure_wordpress(
    site_path: str,
    site_title: str,
    site_tagline: str,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Apply baseline WordPress configuration: site name, tagline, and pretty permalinks."""
    run = runner or default_runner

    run([WP_CLI, "option", "update", "blogname", site_title, f"--path={site_path}"])
    run([WP_CLI, "option", "update", "blogdescription", site_tagline, f"--path={site_path}"])
    run([WP_CLI, "rewrite", "structure", "/%postname%/", f"--path={site_path}"])


def is_wordpress_installed(site_path: str) -> bool:
    """Return True if WP core files are present at site_path."""
    return (Path(site_path) / "wp-includes" / "version.php").exists()
