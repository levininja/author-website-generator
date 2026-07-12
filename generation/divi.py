"""Install and configure the Divi theme on a generated WordPress site via WP-CLI."""

import os
from collections.abc import Callable, Sequence

from generation.subprocess_runner import default_capture_runner, default_runner

WP_CLI = "/usr/local/bin/wp"

DIVI_THEME_SLUG = "Divi"

# Divi stores global settings in this WordPress option as a serialized array.
# Exact sub-keys below are placeholders pending R001 (Divi option-key research).
DIVI_OPTION_KEY = "et_divi"


def _wp_flags(site_path: str) -> list[str]:
    return [f"--path={site_path}", "--allow-root"]


def install_divi(
    site_path: str,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Install and activate the Divi theme.

    Reads the zip path from DIVI_ZIP_PATH env var — must point to a real
    Elegant Themes zip in production (the var is intentionally required at
    runtime, not hard-coded here).
    """
    run = runner or default_runner
    divi_zip = os.environ.get("DIVI_ZIP_PATH", "")

    run([WP_CLI, "theme", "install", divi_zip, *_wp_flags(site_path)])
    run([WP_CLI, "theme", "activate", DIVI_THEME_SLUG, *_wp_flags(site_path)])


def configure_divi_fonts(
    site_path: str,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Set Divi global font settings via et_divi option patches.

    Sub-keys body_font / header_font are placeholder names pending R001.
    R001 will confirm exact keys in the et_divi serialized array.
    """
    run = runner or default_runner

    run([WP_CLI, "option", "patch", "update", DIVI_OPTION_KEY,
         "body_font", "Open Sans", *_wp_flags(site_path)])
    run([WP_CLI, "option", "patch", "update", DIVI_OPTION_KEY,
         "header_font", "Playfair Display", *_wp_flags(site_path)])


def configure_divi_colors(
    site_path: str,
    primary_color: str,
    secondary_color: str,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Set Divi global color palette from author brand colors.

    Sub-keys accent_color / secondary_nav_text_color are placeholder names
    pending R001. R001 will confirm exact keys in the et_divi serialized array.
    Skips empty color values rather than writing blank strings to the option.
    """
    run = runner or default_runner

    if primary_color:
        # Placeholder key — R001 will confirm exact Divi accent color key
        run([WP_CLI, "option", "patch", "update", DIVI_OPTION_KEY,
             "accent_color", primary_color, *_wp_flags(site_path)])
    if secondary_color:
        # Placeholder key — R001 will confirm exact Divi secondary color key
        run([WP_CLI, "option", "patch", "update", DIVI_OPTION_KEY,
             "secondary_nav_text_color", secondary_color, *_wp_flags(site_path)])


def configure_divi_logo(
    site_path: str,
    logo_url: str | None,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Import logo as a media attachment and set the site_logo option.

    Skips entirely when logo_url is absent or empty — no WP-CLI calls are made.
    logo_url will come from a future logo field on the Author model; for now
    serialize_author does not emit this key so callers pass None and this is a no-op.
    """
    if not logo_url:
        return

    run = runner or default_runner
    capture = capture_runner or default_capture_runner

    media_id = capture([
        WP_CLI, "media", "import", logo_url,
        "--return=id",
        "--porcelain",
        *_wp_flags(site_path),
    ]).strip()
    run([WP_CLI, "option", "update", "site_logo", media_id, *_wp_flags(site_path)])


def configure_divi_favicon(
    site_path: str,
    favicon_url: str | None,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Import favicon as a media attachment and set the site_icon option.

    Skips entirely when favicon_url is absent or empty — no WP-CLI calls are made.
    favicon_url will come from a future favicon field on the Author model; for now
    serialize_author does not emit this key so callers pass None and this is a no-op.
    """
    if not favicon_url:
        return

    run = runner or default_runner
    capture = capture_runner or default_capture_runner

    media_id = capture([
        WP_CLI, "media", "import", favicon_url,
        "--return=id",
        "--porcelain",
        *_wp_flags(site_path),
    ]).strip()
    run([WP_CLI, "option", "update", "site_icon", media_id, *_wp_flags(site_path)])


def configure_permalinks(
    site_path: str,
    runner: Callable[[Sequence[str]], None] | None = None,
) -> None:
    """Set WordPress permalink structure to /%postname%/."""
    run = runner or default_runner
    run([WP_CLI, "rewrite", "structure", "/%postname%/", *_wp_flags(site_path)])


def setup_divi(
    site_path: str,
    serialized_author: dict,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Install Divi and apply all baseline configuration for the given author.

    Reads logo_url and favicon_url from serialized_author; both keys are optional
    and will be skipped gracefully when absent. These keys will be populated once
    the Author model gains dedicated logo/favicon file fields.
    """
    install_divi(site_path, runner)
    configure_divi_fonts(site_path, runner)
    configure_divi_colors(
        site_path,
        serialized_author.get("primary_color", ""),
        serialized_author.get("secondary_color", ""),
        runner,
    )
    configure_divi_logo(
        site_path,
        serialized_author.get("logo_url"),
        runner,
        capture_runner,
    )
    configure_divi_favicon(
        site_path,
        serialized_author.get("favicon_url"),
        runner,
        capture_runner,
    )
    configure_permalinks(site_path, runner)
