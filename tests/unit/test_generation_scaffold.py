"""Tests for generation/scaffold.py — all WP-CLI calls are mocked; no real WP install required."""

import os
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runner():
    """Return a mock runner that records every call."""
    return MagicMock(return_value=None)


def _called_args(runner) -> list[list[str]]:
    """Extract the positional args list from each call to a mock runner."""
    return [c.args[0] for c in runner.call_args_list]


# ---------------------------------------------------------------------------
# get_site_path
# ---------------------------------------------------------------------------

def test_get_site_path_default_is_generated_site_in_repo_root():
    from generation.scaffold import DEFAULT_SITE_PATH, get_site_path
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("WP_GENERATED_SITE_PATH", None)
        result = get_site_path()
    assert result == DEFAULT_SITE_PATH
    assert result.endswith("generated-site")


def test_get_site_path_uses_env_var():
    from generation.scaffold import get_site_path
    with patch.dict(os.environ, {"WP_GENERATED_SITE_PATH": "/tmp/custom-wp"}):
        result = get_site_path()
    assert result == "/tmp/custom-wp"


# ---------------------------------------------------------------------------
# install_wordpress
# ---------------------------------------------------------------------------

def test_install_wordpress_calls_core_download_first():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/wp", site_title="My Site", runner=runner)
    calls = _called_args(runner)
    assert len(calls) >= 1
    first_cmd = calls[0]
    assert "core" in first_cmd
    assert "download" in first_cmd


def test_install_wordpress_passes_path_to_core_download():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/my-site", site_title="Test", runner=runner)
    calls = _called_args(runner)
    download_cmd = calls[0]
    assert any("--path=/tmp/my-site" in arg for arg in download_cmd)


def test_install_wordpress_calls_core_install_second():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/wp", site_title="My Site", runner=runner)
    calls = _called_args(runner)
    assert len(calls) >= 2
    second_cmd = calls[1]
    assert "core" in second_cmd
    assert "install" in second_cmd


def test_install_wordpress_passes_site_title():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/wp", site_title="Jane Doe Books", runner=runner)
    calls = _called_args(runner)
    install_cmd = calls[1]
    assert any("--title=Jane Doe Books" in arg for arg in install_cmd)


def test_install_wordpress_passes_default_admin_credentials():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/wp", site_title="Test", runner=runner)
    calls = _called_args(runner)
    install_cmd = calls[1]
    assert any("--admin_user=admin" in arg for arg in install_cmd)
    assert any("--admin_password=admin" in arg for arg in install_cmd)
    assert any("--admin_email=admin@example.com" in arg for arg in install_cmd)


def test_install_wordpress_accepts_custom_admin_credentials():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(
        site_path="/tmp/wp",
        site_title="Test",
        admin_user="myuser",
        admin_password="secret",
        admin_email="me@example.com",
        runner=runner,
    )
    calls = _called_args(runner)
    install_cmd = calls[1]
    assert any("--admin_user=myuser" in arg for arg in install_cmd)
    assert any("--admin_password=secret" in arg for arg in install_cmd)
    assert any("--admin_email=me@example.com" in arg for arg in install_cmd)


def test_install_wordpress_passes_path_to_core_install():
    from generation.scaffold import install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/my-site", site_title="Test", runner=runner)
    calls = _called_args(runner)
    install_cmd = calls[1]
    assert any("--path=/tmp/my-site" in arg for arg in install_cmd)


def test_install_wordpress_uses_wpcli_binary():
    from generation.scaffold import WP_CLI, install_wordpress
    runner = _make_runner()
    install_wordpress(site_path="/tmp/wp", site_title="Test", runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI


# ---------------------------------------------------------------------------
# configure_wordpress
# ---------------------------------------------------------------------------

def test_configure_wordpress_sets_blogname():
    from generation.scaffold import configure_wordpress
    runner = _make_runner()
    configure_wordpress(
        site_path="/tmp/wp", site_title="Jane Doe", site_tagline="Writing stories", runner=runner
    )
    calls = _called_args(runner)
    blogname_call = next(c for c in calls if "blogname" in c)
    assert "Jane Doe" in blogname_call


def test_configure_wordpress_sets_blogdescription():
    from generation.scaffold import configure_wordpress
    runner = _make_runner()
    configure_wordpress(
        site_path="/tmp/wp", site_title="Jane Doe", site_tagline="My tagline here", runner=runner
    )
    calls = _called_args(runner)
    desc_call = next(c for c in calls if "blogdescription" in c)
    assert "My tagline here" in desc_call


def test_configure_wordpress_sets_permalink_structure():
    from generation.scaffold import configure_wordpress
    runner = _make_runner()
    configure_wordpress(site_path="/tmp/wp", site_title="Test", site_tagline="Tag", runner=runner)
    calls = _called_args(runner)
    rewrite_call = next(c for c in calls if "rewrite" in c)
    assert "/%postname%/" in rewrite_call


def test_configure_wordpress_passes_path_to_all_calls():
    from generation.scaffold import configure_wordpress
    runner = _make_runner()
    configure_wordpress(
        site_path="/tmp/special-path", site_title="T", site_tagline="T", runner=runner
    )
    for cmd in _called_args(runner):
        assert any("/tmp/special-path" in arg for arg in cmd)


def test_configure_wordpress_uses_wpcli_binary():
    from generation.scaffold import WP_CLI, configure_wordpress
    runner = _make_runner()
    configure_wordpress(site_path="/tmp/wp", site_title="T", site_tagline="T", runner=runner)
    for cmd in _called_args(runner):
        assert cmd[0] == WP_CLI


# ---------------------------------------------------------------------------
# is_wordpress_installed
# ---------------------------------------------------------------------------

def test_is_wordpress_installed_returns_true_when_version_php_exists(tmp_path):
    from generation.scaffold import is_wordpress_installed
    wp_includes = tmp_path / "wp-includes"
    wp_includes.mkdir()
    (wp_includes / "version.php").write_text("<?php $wp_version = '6.5'; ?>")
    assert is_wordpress_installed(str(tmp_path)) is True


def test_is_wordpress_installed_returns_false_when_directory_empty(tmp_path):
    from generation.scaffold import is_wordpress_installed
    assert is_wordpress_installed(str(tmp_path)) is False


def test_is_wordpress_installed_returns_false_when_path_does_not_exist():
    from generation.scaffold import is_wordpress_installed
    assert is_wordpress_installed("/nonexistent/path/to/site") is False


def test_is_wordpress_installed_returns_false_when_wp_includes_missing(tmp_path):
    from generation.scaffold import is_wordpress_installed
    # Create something else but not wp-includes/version.php
    (tmp_path / "index.php").write_text("<?php ?>")
    assert is_wordpress_installed(str(tmp_path)) is False
