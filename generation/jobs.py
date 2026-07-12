"""Wire the generation pipeline together and track job state in GenerationJob."""

import os
import shutil
import uuid
from collections.abc import Callable, Sequence

from django.utils import timezone

from generation.books_cpt import write_books_cpt
from generation.pages import generate_pages
from generation.scaffold import configure_wordpress, get_site_path, install_wordpress


def run_generation_job(
    job_id: uuid.UUID,
    author_id: uuid.UUID,
    runner: Callable[[Sequence[str]], None] | None = None,
    capture_runner: Callable[[Sequence[str]], str] | None = None,
) -> None:
    """Run the full site generation pipeline and persist final state to GenerationJob.

    Transitions: pending → running → complete, or running → failed on any error.
    On failure, any partially-written site directory is removed before updating the job.
    The runner/capture_runner parameters are injectable for unit-test isolation.

    Connection cleanup (connection.close()) is the caller's responsibility — the view
    wraps this function in a thread that closes the connection after it returns.
    """
    # Local imports avoid circular app-registry issues at module load time.
    from onboarding.models import Author, GenerationJob
    from onboarding.services import serialize_author, serialize_book

    job = GenerationJob.objects.get(pk=job_id)
    job.status = GenerationJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    site_path = os.path.join(get_site_path(), str(author_id))

    try:
        author = (
            Author.objects
            .prefetch_related(
                "authorcategory_set__category",
                "authorgenre_set__genre",
                "authorsubgenre_set__subgenre",
            )
            .get(pk=author_id)
        )
        books = list(
            author.books
            .select_related("genre__category", "subgenre", "series")
            .prefetch_related("reviews", "awards")
        )
        serialized_author = serialize_author(author)
        serialized_books = [serialize_book(book) for book in books]

        install_wordpress(
            site_path,
            site_title=serialized_author["name"],
            admin_email=serialized_author["contact_email"],
            site_url=f"https://{serialized_author['site_domain']}",
            runner=runner,
        )
        configure_wordpress(
            site_path,
            site_title=serialized_author["name"],
            site_tagline=serialized_author.get("site_tagline", ""),
            runner=runner,
        )
        write_books_cpt(site_path)
        generate_pages(
            site_path,
            serialized_author,
            serialized_books,
            runner=runner,
            capture_runner=capture_runner,
        )

        job.status = GenerationJob.STATUS_COMPLETE
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "completed_at"])

    except Exception as exc:
        if os.path.exists(site_path):
            shutil.rmtree(site_path, ignore_errors=True)
        job.status = GenerationJob.STATUS_FAILED
        job.error_message = str(exc) or "Generation failed."
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
