"""Tests for generation/subprocess_runner.py.

Covers: stderr capture, configurable timeouts, and DEBUG/ERROR logging.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from generation.subprocess_runner import (
    GenerationTimeoutError,
    default_capture_runner,
    default_runner,
)


class TestDefaultRunner:
    def test_successful_run_returns_none(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = default_runner(["echo", "hello"])
        assert result is None

    def test_successful_run_calls_subprocess_with_args(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            default_runner(["wp", "core", "download"])
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["wp", "core", "download"]

    def test_nonzero_exit_raises_with_stderr(self):
        error = subprocess.CalledProcessError(1, ["wp", "plugin", "install"])
        error.stdout = "some stdout"
        error.stderr = "Fatal error: plugin not found"
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                default_runner(["wp", "plugin", "install"])
        raised = exc_info.value
        assert raised.stderr == "Fatal error: plugin not found"
        assert raised.stdout == "some stdout"

    def test_timeout_raises_generation_timeout_error(self):
        expired = subprocess.TimeoutExpired(["wp", "core", "download"], 120)
        with patch("subprocess.run", side_effect=expired):
            with pytest.raises(GenerationTimeoutError) as exc_info:
                default_runner(["wp", "core", "download"])
        assert "wp" in str(exc_info.value)

    def test_timeout_message_includes_timeout_value(self):
        expired = subprocess.TimeoutExpired(["wp", "core", "download"], 300)
        with patch("subprocess.run", side_effect=expired):
            with pytest.raises(GenerationTimeoutError) as exc_info:
                default_runner(["wp", "core", "download"], timeout=300)
        assert "300" in str(exc_info.value)

    def test_default_timeout_is_120(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            default_runner(["echo", "hi"])
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 120

    def test_custom_timeout_is_passed_to_subprocess(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            default_runner(["wp", "core", "download"], timeout=300)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 300

    def test_failure_is_logged_at_error_level(self, caplog):
        import logging
        error = subprocess.CalledProcessError(1, ["wp", "plugin", "install"])
        error.stdout = ""
        error.stderr = "fatal: permission denied"
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(subprocess.CalledProcessError):
                with caplog.at_level(logging.ERROR, logger="generation.subprocess_runner"):
                    default_runner(["wp", "plugin", "install"])
        assert any("fatal: permission denied" in r.message for r in caplog.records)

    def test_invocation_logged_at_debug_level(self, caplog):
        import logging
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with caplog.at_level(logging.DEBUG, logger="generation.subprocess_runner"):
                default_runner(["wp", "cache", "flush"])
        assert any("wp" in r.message for r in caplog.records if r.levelno == logging.DEBUG)


class TestDefaultCaptureRunner:
    def test_returns_last_nonempty_stdout_line(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\n", stderr="")
            result = default_capture_runner(["wp", "option", "get", "siteurl"])
        assert result == "line2"

    def test_strips_php_warnings_from_stdout(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="PHP Deprecated: something\nhttps://example.com\n",
                stderr="",
            )
            result = default_capture_runner(["wp", "option", "get", "siteurl"])
        assert result == "https://example.com"

    def test_returns_empty_string_when_stdout_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = default_capture_runner(["wp", "option", "get", "siteurl"])
        assert result == ""

    def test_nonzero_exit_raises_with_stderr(self):
        error = subprocess.CalledProcessError(1, ["wp", "option", "get", "siteurl"])
        error.stdout = ""
        error.stderr = "Error: Site not found"
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                default_capture_runner(["wp", "option", "get", "siteurl"])
        assert exc_info.value.stderr == "Error: Site not found"

    def test_timeout_raises_generation_timeout_error(self):
        expired = subprocess.TimeoutExpired(["wp", "option", "get"], 120)
        with patch("subprocess.run", side_effect=expired):
            with pytest.raises(GenerationTimeoutError):
                default_capture_runner(["wp", "option", "get", "siteurl"])

    def test_default_timeout_is_120(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="result\n", stderr="")
            default_capture_runner(["wp", "option", "get", "siteurl"])
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 120

    def test_custom_timeout_passed_through(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="result\n", stderr="")
            default_capture_runner(["wp", "core", "download"], timeout=300)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 300

    def test_invocation_logged_at_debug_level(self, caplog):
        import logging
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
            with caplog.at_level(logging.DEBUG, logger="generation.subprocess_runner"):
                default_capture_runner(["wp", "option", "get", "siteurl"])
        assert any("wp" in r.message for r in caplog.records if r.levelno == logging.DEBUG)

    def test_failure_logged_at_error_level(self, caplog):
        import logging
        error = subprocess.CalledProcessError(2, ["wp", "option", "get"])
        error.stdout = ""
        error.stderr = "critical: db connection failed"
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(subprocess.CalledProcessError):
                with caplog.at_level(logging.ERROR, logger="generation.subprocess_runner"):
                    default_capture_runner(["wp", "option", "get", "siteurl"])
        assert any("critical: db connection failed" in r.message for r in caplog.records)


class TestGenerationTimeoutError:
    def test_is_exception(self):
        err = GenerationTimeoutError("timed out")
        assert isinstance(err, Exception)

    def test_message_preserved(self):
        err = GenerationTimeoutError("command took too long")
        assert "command took too long" in str(err)
