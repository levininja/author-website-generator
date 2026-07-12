from django.apps import AppConfig


def cleanup_stale_jobs() -> None:
    """Reset any job stuck in 'running' to 'failed'.

    Called from AppConfig.ready() on every server start. A job left in 'running'
    means the server died mid-generation; the thread is gone so the job can never
    complete on its own.
    """
    from django.db import OperationalError, ProgrammingError
    from django.utils import timezone

    from onboarding.models import GenerationJob

    try:
        GenerationJob.objects.filter(status=GenerationJob.STATUS_RUNNING).update(
            status=GenerationJob.STATUS_FAILED,
            error_message="Server restarted during generation.",
            completed_at=timezone.now(),
        )
    except (OperationalError, ProgrammingError):
        # Table may not exist yet (e.g., before the first migration runs).
        pass


class OnboardingConfig(AppConfig):
    """Configure the onboarding Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "onboarding"

    def ready(self) -> None:
        """Reset stale running jobs to failed on server startup."""
        cleanup_stale_jobs()
