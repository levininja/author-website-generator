"""Tests for generation/divi.py — all WP-CLI calls are mocked; no real WP install required."""

import os
from unittest.mock import MagicMock, patch

SITE_PATH = "/tmp/test-wp-site"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runner():
    return MagicMock(return_value=None)


def _make_capture_runner(return_value="42"):
    return MagicMock(return_value=return_value)


def _called_args(mock) -> list[list[str]]:
    return [c.args[0] for c in mock.call_args_list]


def _any_call_contains(calls: list[list[str]], *tokens: str) -> bool:
    """Return True if any single call contains all of the given tokens."""
    for call in calls:
        joined = " ".join(call)
        if all(t in joined for t in tokens):
            return True
    return False


# ---------------------------------------------------------------------------
# install_divi
# ---------------------------------------------------------------------------

def test_install_divi_calls_theme_install_with_zip_path():
    from generation.divi import install_divi
    runner = _make_runner()
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        install_divi(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "theme", "install", "/srv/themes/Divi.zip")


def test_install_divi_calls_theme_activate():
    from generation.divi import DIVI_THEME_SLUG, install_divi
    runner = _make_runner()
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        install_divi(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "theme", "activate", DIVI_THEME_SLUG)


def test_install_divi_activate_comes_after_install():
    from generation.divi import install_divi
    runner = _make_runner()
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        install_divi(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    install_idx = next(i for i, c in enumerate(calls) if "install" in c and "theme" in c)
    activate_idx = next(i for i, c in enumerate(calls) if "activate" in c and "theme" in c)
    assert install_idx < activate_idx


def test_install_divi_passes_site_path_to_all_calls():
    from generation.divi import install_divi
    runner = _make_runner()
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        install_divi(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


def test_install_divi_uses_wpcli_binary():
    from generation.divi import WP_CLI, install_divi
    runner = _make_runner()
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        install_divi(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI


# ---------------------------------------------------------------------------
# configure_divi_fonts
# ---------------------------------------------------------------------------

def test_configure_divi_fonts_updates_body_font():
    from generation.divi import DIVI_OPTION_KEY, configure_divi_fonts
    runner = _make_runner()
    configure_divi_fonts(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "option", "patch", "update", DIVI_OPTION_KEY, "body_font")


def test_configure_divi_fonts_updates_header_font():
    from generation.divi import DIVI_OPTION_KEY, configure_divi_fonts
    runner = _make_runner()
    configure_divi_fonts(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "option", "patch", "update", DIVI_OPTION_KEY, "header_font")


def test_configure_divi_fonts_passes_site_path():
    from generation.divi import configure_divi_fonts
    runner = _make_runner()
    configure_divi_fonts(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


def test_configure_divi_fonts_uses_wpcli_binary():
    from generation.divi import WP_CLI, configure_divi_fonts
    runner = _make_runner()
    configure_divi_fonts(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI


# ---------------------------------------------------------------------------
# configure_divi_colors
# ---------------------------------------------------------------------------

def test_configure_divi_colors_sets_primary_color():
    from generation.divi import DIVI_OPTION_KEY, configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "#FF0000", "#0000FF", runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "option", "patch", DIVI_OPTION_KEY, "#FF0000")


def test_configure_divi_colors_sets_secondary_color():
    from generation.divi import DIVI_OPTION_KEY, configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "#FF0000", "#0000FF", runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "option", "patch", DIVI_OPTION_KEY, "#0000FF")


def test_configure_divi_colors_skips_empty_primary():
    from generation.divi import DIVI_OPTION_KEY, configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "", "#0000FF", runner=runner)
    calls = _called_args(runner)
    # Must still set secondary but should not set an empty primary
    primary_calls = [c for c in calls if "" in c and DIVI_OPTION_KEY in c and "accent_color" in c]
    assert not any("" == tok for call in primary_calls for tok in call if call.count("") > 1)


def test_configure_divi_colors_skips_empty_secondary():
    from generation.divi import configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "#FF0000", "", runner=runner)
    calls = _called_args(runner)
    # Only one option patch call (for primary) — secondary is empty and skipped
    patch_calls = [c for c in calls if "patch" in c]
    assert len(patch_calls) == 1


def test_configure_divi_colors_skips_both_when_empty():
    from generation.divi import configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "", "", runner=runner)
    calls = _called_args(runner)
    patch_calls = [c for c in calls if "patch" in c]
    assert len(patch_calls) == 0


def test_configure_divi_colors_passes_site_path():
    from generation.divi import configure_divi_colors
    runner = _make_runner()
    configure_divi_colors(SITE_PATH, "#FF0000", "#0000FF", runner=runner)
    for cmd in _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


# ---------------------------------------------------------------------------
# configure_divi_logo
# ---------------------------------------------------------------------------

def test_configure_divi_logo_imports_media_and_sets_option():
    from generation.divi import configure_divi_logo
    runner = _make_runner()
    capture = _make_capture_runner("99\n")
    configure_divi_logo(
        SITE_PATH,
        logo_url="https://example.com/logo.png",
        runner=runner,
        capture_runner=capture,
    )
    capture_calls = _called_args(capture)
    assert _any_call_contains(capture_calls, "media", "import", "https://example.com/logo.png")
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "option", "update", "site_logo", "99")


def test_configure_divi_logo_skips_when_logo_url_is_none():
    from generation.divi import configure_divi_logo
    runner = _make_runner()
    capture = _make_capture_runner()
    configure_divi_logo(SITE_PATH, logo_url=None, runner=runner, capture_runner=capture)
    assert capture.call_count == 0
    assert runner.call_count == 0


def test_configure_divi_logo_skips_when_logo_url_is_empty_string():
    from generation.divi import configure_divi_logo
    runner = _make_runner()
    capture = _make_capture_runner()
    configure_divi_logo(SITE_PATH, logo_url="", runner=runner, capture_runner=capture)
    assert capture.call_count == 0
    assert runner.call_count == 0


def test_configure_divi_logo_passes_site_path():
    from generation.divi import configure_divi_logo
    runner = _make_runner()
    capture = _make_capture_runner("10\n")
    configure_divi_logo(
        SITE_PATH,
        logo_url="https://example.com/logo.png",
        runner=runner,
        capture_runner=capture,
    )
    for cmd in _called_args(capture) + _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


# ---------------------------------------------------------------------------
# configure_divi_favicon
# ---------------------------------------------------------------------------

def test_configure_divi_favicon_imports_media_and_sets_option():
    from generation.divi import configure_divi_favicon
    runner = _make_runner()
    capture = _make_capture_runner("55\n")
    configure_divi_favicon(
        SITE_PATH,
        favicon_url="https://example.com/favicon.png",
        runner=runner,
        capture_runner=capture,
    )
    capture_calls = _called_args(capture)
    assert _any_call_contains(capture_calls, "media", "import", "https://example.com/favicon.png")
    run_calls = _called_args(runner)
    assert _any_call_contains(run_calls, "option", "update", "site_icon", "55")


def test_configure_divi_favicon_skips_when_favicon_url_is_none():
    from generation.divi import configure_divi_favicon
    runner = _make_runner()
    capture = _make_capture_runner()
    configure_divi_favicon(SITE_PATH, favicon_url=None, runner=runner, capture_runner=capture)
    assert capture.call_count == 0
    assert runner.call_count == 0


def test_configure_divi_favicon_skips_when_favicon_url_is_empty_string():
    from generation.divi import configure_divi_favicon
    runner = _make_runner()
    capture = _make_capture_runner()
    configure_divi_favicon(SITE_PATH, favicon_url="", runner=runner, capture_runner=capture)
    assert capture.call_count == 0
    assert runner.call_count == 0


def test_configure_divi_favicon_passes_site_path():
    from generation.divi import configure_divi_favicon
    runner = _make_runner()
    capture = _make_capture_runner("5\n")
    configure_divi_favicon(
        SITE_PATH,
        favicon_url="https://example.com/favicon.png",
        runner=runner,
        capture_runner=capture,
    )
    for cmd in _called_args(capture) + _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


# ---------------------------------------------------------------------------
# configure_permalinks
# ---------------------------------------------------------------------------

def test_configure_permalinks_sets_postname_structure():
    from generation.divi import configure_permalinks
    runner = _make_runner()
    configure_permalinks(SITE_PATH, runner=runner)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "rewrite", "structure", "/%postname%/")


def test_configure_permalinks_passes_site_path():
    from generation.divi import configure_permalinks
    runner = _make_runner()
    configure_permalinks(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert any(SITE_PATH in arg for arg in cmd)


def test_configure_permalinks_uses_wpcli_binary():
    from generation.divi import WP_CLI, configure_permalinks
    runner = _make_runner()
    configure_permalinks(SITE_PATH, runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI


# ---------------------------------------------------------------------------
# setup_divi — orchestration
# ---------------------------------------------------------------------------

AUTHOR_WITH_BRANDING = {
    "primary_color": "#C0392B",
    "secondary_color": "#2980B9",
    "logo_url": "https://example.com/logo.png",
    "favicon_url": "https://example.com/favicon.png",
}

AUTHOR_WITHOUT_OPTIONAL_ASSETS = {
    "primary_color": "#C0392B",
    "secondary_color": "#2980B9",
}


def test_setup_divi_installs_theme():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "theme", "install")


def test_setup_divi_activates_theme():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "theme", "activate")


def test_setup_divi_configures_fonts():
    from generation.divi import DIVI_OPTION_KEY, setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "option", "patch", DIVI_OPTION_KEY, "body_font")


def test_setup_divi_configures_colors():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "#C0392B")
    assert _any_call_contains(calls, "#2980B9")


def test_setup_divi_imports_logo_when_present():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("7\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    capture_calls = _called_args(capture)
    assert _any_call_contains(capture_calls, "media", "import", "https://example.com/logo.png")


def test_setup_divi_imports_favicon_when_present():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("8\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    capture_calls = _called_args(capture)
    assert _any_call_contains(capture_calls, "media", "import", "https://example.com/favicon.png")


def test_setup_divi_skips_logo_when_missing():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITHOUT_OPTIONAL_ASSETS, runner=runner, capture_runner=capture)
    capture_calls = _called_args(capture)
    assert not _any_call_contains(capture_calls, "media", "import")
    run_calls = _called_args(runner)
    assert not _any_call_contains(run_calls, "site_logo")


def test_setup_divi_skips_favicon_when_missing():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITHOUT_OPTIONAL_ASSETS, runner=runner, capture_runner=capture)
    run_calls = _called_args(runner)
    assert not _any_call_contains(run_calls, "site_icon")


def test_setup_divi_configures_permalinks():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    calls = _called_args(runner)
    assert _any_call_contains(calls, "rewrite", "structure", "/%postname%/")


def test_setup_divi_passes_site_path_to_all_calls():
    from generation.divi import setup_divi
    runner = _make_runner()
    capture = _make_capture_runner("1\n")
    with patch.dict(os.environ, {"DIVI_ZIP_PATH": "/srv/themes/Divi.zip"}):
        setup_divi(SITE_PATH, AUTHOR_WITH_BRANDING, runner=runner, capture_runner=capture)
    for cmd in _called_args(runner) + _called_args(capture):
        assert any(SITE_PATH in arg for arg in cmd), f"Missing site path in: {cmd}"
