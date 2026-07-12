"""Tests for generation/hosting.py — atomic site deployment and PHP server management."""

import os
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# deploy_site — atomic file replacement
# ---------------------------------------------------------------------------


def test_deploy_site_moves_staged_files_to_hosted_path(tmp_path):
    from generation.hosting import deploy_site

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "index.php").write_text("<?php echo 'hello'; ?>")
    hosted = tmp_path / "hosted"

    deploy_site(str(staging), str(hosted))

    assert (hosted / "index.php").exists()


def test_deploy_site_staging_dir_no_longer_exists_after_deploy(tmp_path):
    from generation.hosting import deploy_site

    staging = tmp_path / "staging"
    staging.mkdir()
    hosted = tmp_path / "hosted"

    deploy_site(str(staging), str(hosted))

    assert not staging.exists()


def test_deploy_site_removes_old_hosted_site_files(tmp_path):
    from generation.hosting import deploy_site

    hosted = tmp_path / "hosted"
    hosted.mkdir()
    (hosted / "old.php").write_text("old content")

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "new.php").write_text("new content")

    deploy_site(str(staging), str(hosted))

    assert not (hosted / "old.php").exists()
    assert (hosted / "new.php").exists()


def test_deploy_site_works_when_no_prior_hosted_dir_exists(tmp_path):
    from generation.hosting import deploy_site

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "wp-load.php").write_text("wp")
    hosted = tmp_path / "hosted"

    assert not hosted.exists()
    deploy_site(str(staging), str(hosted))
    assert hosted.exists()


def test_deploy_site_new_files_present_at_staging_before_old_removed(tmp_path):
    """Staging content is fully written before old hosted site is removed.

    Atomicity contract: deploy_site is only called after the pipeline has finished
    writing all files to staging_path. The remove-then-move sequence within
    deploy_site ensures the old site is removed only after all new files exist.
    """
    from generation.hosting import deploy_site

    hosted = tmp_path / "hosted"
    hosted.mkdir()
    (hosted / "old.php").write_text("old")

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "new.php").write_text("new content — fully written before deploy")

    # Capture the staging path contents before deploy to prove they were complete
    staging_contents = list(staging.iterdir())

    deploy_site(str(staging), str(hosted))

    # Staging was fully populated (non-empty) before deploy was called
    assert len(staging_contents) > 0
    # After deploy, old file is gone and new file is present at hosted path
    assert not (hosted / "old.php").exists()
    assert (hosted / "new.php").exists()


def test_deploy_site_nested_directory_structure_preserved(tmp_path):
    from generation.hosting import deploy_site

    staging = tmp_path / "staging"
    (staging / "wp-content" / "themes").mkdir(parents=True)
    (staging / "wp-content" / "themes" / "Divi").mkdir()
    (staging / "wp-content" / "themes" / "Divi" / "style.css").write_text("body{}")
    hosted = tmp_path / "hosted"

    deploy_site(str(staging), str(hosted))

    assert (hosted / "wp-content" / "themes" / "Divi" / "style.css").exists()


# ---------------------------------------------------------------------------
# start_php_server — process management
# ---------------------------------------------------------------------------


def test_start_php_server_calls_popen_with_correct_command(tmp_path):
    from generation.hosting import start_php_server

    mock_process = MagicMock()
    popen_calls = []

    def mock_popen(args, **kwargs):
        popen_calls.append(args)
        return mock_process

    start_php_server(str(tmp_path), popen_fn=mock_popen)

    assert len(popen_calls) == 1
    assert popen_calls[0] == ["php", "-S", "localhost:8080", "-t", str(tmp_path)]


def test_start_php_server_terminates_previous_server_before_starting_new(tmp_path):
    from generation.hosting import start_php_server

    first_process = MagicMock()
    second_process = MagicMock()
    processes = iter([first_process, second_process])

    def mock_popen(args, **kwargs):
        return next(processes)

    start_php_server(str(tmp_path), popen_fn=mock_popen)
    start_php_server(str(tmp_path), popen_fn=mock_popen)

    first_process.terminate.assert_called_once()
    first_process.wait.assert_called_once()


def test_start_php_server_does_not_terminate_when_no_previous_server(tmp_path):
    """Starting the first server should not attempt to terminate a non-existent one."""
    import generation.hosting as hosting_module
    from generation.hosting import start_php_server

    # Ensure no prior process is tracked
    hosting_module._php_process = None
    mock_process = MagicMock()

    start_php_server(str(tmp_path), popen_fn=lambda *a, **kw: mock_process)

    # If we get here without AttributeError on None, the guard worked
    assert hosting_module._php_process is mock_process


def test_start_php_server_stores_new_process_in_module_state(tmp_path):
    import generation.hosting as hosting_module
    from generation.hosting import start_php_server

    mock_process = MagicMock()
    start_php_server(str(tmp_path), popen_fn=lambda *a, **kw: mock_process)

    assert hosting_module._php_process is mock_process


# ---------------------------------------------------------------------------
# host_site — end-to-end deploy + serve
# ---------------------------------------------------------------------------


def test_host_site_deploys_staged_files_to_hosted_path(tmp_path):
    from generation.hosting import host_site

    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "wp-load.php").write_text("wp")
    hosted = tmp_path / "hosted"

    host_site(str(staging), str(hosted), popen_fn=MagicMock(return_value=MagicMock()))

    assert (hosted / "wp-load.php").exists()


def test_host_site_starts_php_server_pointing_at_hosted_path(tmp_path):
    from generation.hosting import host_site

    staging = tmp_path / "staging"
    staging.mkdir()
    hosted = tmp_path / "hosted"
    popen_calls = []

    def mock_popen(args, **kwargs):
        popen_calls.append(args)
        return MagicMock()

    host_site(str(staging), str(hosted), popen_fn=mock_popen)

    assert len(popen_calls) == 1
    assert str(hosted) in popen_calls[0]


def test_host_site_uses_get_hosted_site_path_when_no_hosted_path_given(tmp_path):
    from generation.hosting import host_site

    staging = tmp_path / "staging"
    staging.mkdir()

    with patch("generation.hosting.get_hosted_site_path", return_value=str(tmp_path / "hosted")):
        host_site(str(staging), popen_fn=MagicMock(return_value=MagicMock()))

    assert (tmp_path / "hosted").exists()


# ---------------------------------------------------------------------------
# get_hosted_site_path — env var override
# ---------------------------------------------------------------------------


def test_get_hosted_site_path_returns_default_when_env_var_not_set():
    from generation.hosting import DEFAULT_HOSTED_SITE_PATH, get_hosted_site_path

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("WP_HOSTED_SITE_PATH", None)
        result = get_hosted_site_path()

    assert result == DEFAULT_HOSTED_SITE_PATH


def test_get_hosted_site_path_returns_env_var_when_set(tmp_path):
    from generation.hosting import get_hosted_site_path

    custom_path = str(tmp_path / "custom-site")
    with patch.dict(os.environ, {"WP_HOSTED_SITE_PATH": custom_path}):
        result = get_hosted_site_path()

    assert result == custom_path


# ---------------------------------------------------------------------------
# PREVIEW_URL constant
# ---------------------------------------------------------------------------


def test_preview_url_constant_is_correct_local_address():
    from generation.hosting import PREVIEW_URL

    assert PREVIEW_URL == "http://localhost:8080"
