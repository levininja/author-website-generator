"""Tests for GenerationJob model, cleanup_stale_jobs(), and run_generation_job() pipeline wiring."""

import uuid
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def author():
    from onboarding.models import Author
    return Author.objects.create(
        name="Jane Doe",
        contact_email="jane@example.com",
        site_domain="janedoe.com",
    )


# ---------------------------------------------------------------------------
# GenerationJob model
# ---------------------------------------------------------------------------


def test_generation_job_default_status_is_pending(author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    assert job.status == GenerationJob.STATUS_PENDING


def test_generation_job_has_uuid_primary_key(author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    assert isinstance(job.pk, uuid.UUID)


def test_generation_job_created_at_is_set_automatically(author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    assert job.created_at is not None


def test_generation_job_started_at_and_completed_at_default_to_null(author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    assert job.started_at is None
    assert job.completed_at is None


def test_generation_job_error_message_defaults_to_null(author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    assert job.error_message is None


def test_generation_job_db_table_is_generation_job(author):
    from onboarding.models import GenerationJob
    assert GenerationJob._meta.db_table == "generation_job"


def test_generation_job_status_choices_include_all_four_states():
    from onboarding.models import GenerationJob
    statuses = {choice[0] for choice in GenerationJob.STATUS_CHOICES}
    assert statuses == {"pending", "running", "complete", "failed"}


# ---------------------------------------------------------------------------
# cleanup_stale_jobs
# ---------------------------------------------------------------------------


def test_cleanup_stale_jobs_resets_running_jobs_to_failed(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_RUNNING)
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_FAILED


def test_cleanup_stale_jobs_sets_human_readable_error_message(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_RUNNING)
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert "restarted" in job.error_message.lower()


def test_cleanup_stale_jobs_sets_completed_at_on_reset_jobs(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_RUNNING)
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert job.completed_at is not None


def test_cleanup_stale_jobs_does_not_affect_pending_jobs(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_PENDING)
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_PENDING


def test_cleanup_stale_jobs_does_not_affect_complete_jobs(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_COMPLETE)
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_COMPLETE


def test_cleanup_stale_jobs_does_not_modify_prior_failed_error_message(author):
    from onboarding.apps import cleanup_stale_jobs
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(
        author=author,
        status=GenerationJob.STATUS_FAILED,
        error_message="Previous error.",
    )
    cleanup_stale_jobs()
    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_FAILED
    assert job.error_message == "Previous error."


# ---------------------------------------------------------------------------
# run_generation_job — happy path
# ---------------------------------------------------------------------------


def test_run_generation_job_transitions_pending_to_running_then_complete(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress"),
        patch("generation.jobs.configure_wordpress"),
        patch("generation.jobs.setup_divi"),
        patch("generation.jobs.write_books_cpt"),
        patch("generation.jobs.generate_pages"),
        patch("generation.jobs.setup_header_footer"),
        patch("generation.jobs.host_site"),
    ):
        run_generation_job(job.pk, author.pk)

    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_COMPLETE
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.error_message is None


def test_run_generation_job_sets_preview_url_on_complete(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress"),
        patch("generation.jobs.configure_wordpress"),
        patch("generation.jobs.setup_divi"),
        patch("generation.jobs.write_books_cpt"),
        patch("generation.jobs.generate_pages"),
        patch("generation.jobs.setup_header_footer"),
        patch("generation.jobs.host_site"),
    ):
        run_generation_job(job.pk, author.pk)

    job.refresh_from_db()
    assert job.preview_url == "http://localhost:8080"


def test_run_generation_job_calls_pipeline_functions_in_order(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    order = []

    def _record(name):
        return lambda *a, **kw: order.append(name)

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress", side_effect=_record("install")),
        patch("generation.jobs.configure_wordpress", side_effect=_record("configure")),
        patch("generation.jobs.setup_divi", side_effect=_record("divi")),
        patch("generation.jobs.write_books_cpt", side_effect=_record("books_cpt")),
        patch("generation.jobs.generate_pages", side_effect=_record("pages")),
        patch("generation.jobs.setup_header_footer", side_effect=_record("header_footer")),
        patch("generation.jobs.host_site", side_effect=_record("host")),
    ):
        run_generation_job(job.pk, author.pk)

    assert order == ["install", "configure", "divi", "books_cpt", "pages", "header_footer", "host"]


def test_run_generation_job_uses_author_name_as_site_title(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress") as mock_install,
        patch("generation.jobs.configure_wordpress"),
        patch("generation.jobs.setup_divi"),
        patch("generation.jobs.write_books_cpt"),
        patch("generation.jobs.generate_pages"),
        patch("generation.jobs.setup_header_footer"),
        patch("generation.jobs.host_site"),
    ):
        run_generation_job(job.pk, author.pk)

    assert mock_install.call_args.kwargs["site_title"] == "Jane Doe"


# ---------------------------------------------------------------------------
# run_generation_job — failure path
# ---------------------------------------------------------------------------


def test_run_generation_job_marks_job_failed_on_pipeline_error(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.install_wordpress", side_effect=RuntimeError("WP-CLI failed")),
    ):
        run_generation_job(job.pk, author.pk)

    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_FAILED
    assert "WP-CLI failed" in job.error_message
    assert job.completed_at is not None


def test_run_generation_job_cleans_up_site_files_on_failure(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    # Pre-create partial staging files to simulate install_wordpress partially completing.
    # Staging path is get_site_path() / "staging-{job_id}".
    staging_dir = tmp_path / f"staging-{job.pk}"
    staging_dir.mkdir()
    (staging_dir / "partial_file.php").write_text("partial")

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress", side_effect=RuntimeError("oops")),
    ):
        run_generation_job(job.pk, author.pk)

    assert not staging_dir.exists()


def test_run_generation_job_does_not_raise_even_if_no_site_files_to_clean(author, tmp_path):
    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)

    # No staging directory exists — cleanup should handle this gracefully
    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress", side_effect=RuntimeError("no files yet")),
    ):
        run_generation_job(job.pk, author.pk)

    job.refresh_from_db()
    assert job.status == GenerationJob.STATUS_FAILED


def test_run_generation_job_accepts_runner_and_capture_runner_for_testability(author, tmp_path):
    from unittest.mock import MagicMock

    from generation.jobs import run_generation_job
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author)
    runner = MagicMock(return_value=None)
    capture_runner = MagicMock(return_value="1")

    with (
        patch("generation.jobs.get_site_path", return_value=str(tmp_path)),
        patch("generation.jobs.get_hosted_site_path", return_value=str(tmp_path / "hosted")),
        patch("generation.jobs.install_wordpress") as mock_install,
        patch("generation.jobs.configure_wordpress"),
        patch("generation.jobs.setup_divi") as mock_divi,
        patch("generation.jobs.write_books_cpt"),
        patch("generation.jobs.generate_pages") as mock_pages,
        patch("generation.jobs.setup_header_footer") as mock_header_footer,
        patch("generation.jobs.host_site"),
    ):
        run_generation_job(job.pk, author.pk, runner=runner, capture_runner=capture_runner)

    assert mock_install.call_args.kwargs.get("runner") is runner
    assert mock_divi.call_args.kwargs.get("runner") is runner
    assert mock_divi.call_args.kwargs.get("capture_runner") is capture_runner
    assert mock_pages.call_args.kwargs.get("runner") is runner
    assert mock_pages.call_args.kwargs.get("capture_runner") is capture_runner
    assert mock_header_footer.call_args.kwargs.get("runner") is runner
    assert mock_header_footer.call_args.kwargs.get("capture_runner") is capture_runner
