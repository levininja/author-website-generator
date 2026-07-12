"""Wire the generation pipeline together and track job state in GenerationJob."""

import os
import shutil
import uuid
from collections.abc import Callable, Sequence

from django.utils import timezone

from generation.books_cpt import write_books_cpt
from generation.divi import setup_divi
from generation.header_footer import setup_header_footer
from generation.hosting import PREVIEW_URL, get_hosted_site_path, host_site
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
    On failure, any partially-written staging directory is removed before updating
    the job record. runner/capture_runner are injectable for unit-test isolation.

    Pipeline order:
      1. install_wordpress     — download WP core and run the installer
      2. configure_wordpress   — set site name, tagline, permalinks
      3. setup_divi            — install/activate Divi before pages are generated
      4. write_books_cpt       — register the Books custom post type
      5. generate_pages        — generate all author pages via WP-CLI
      6. setup_header_footer   — create nav menu and footer social links
      7. host_site             — atomically deploy and start PHP preview server

    Connection cleanup (connection.close()) is the caller's responsibility — the
    view wraps this function in a thread that closes the connection after it returns.
    """
    # Local imports avoid circular app-registry issues at module load time.
    from onboarding.models import Author, GenerationJob
    from onboarding.services import serialize_author, serialize_book

    job = GenerationJob.objects.get(pk=job_id)
    job.status = GenerationJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    # Pipeline writes to a per-job staging directory so the old hosted site
    # remains intact until all new files are fully written (atomic replace).
    staging_path = os.path.join(get_site_path(), f"staging-{job_id}")
    hosted_path = get_hosted_site_path()

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
            staging_path,
            site_title=serialized_author["name"],
            admin_email=serialized_author["contact_email"],
            site_url=f"https://{serialized_author['site_domain']}",
            runner=runner,
        )
        configure_wordpress(
            staging_path,
            site_title=serialized_author["name"],
            site_tagline=serialized_author.get("site_tagline", ""),
            runner=runner,
        )
        # Divi must be installed before pages are generated so pages render
        # against the correct theme from the moment they are created.
        setup_divi(
            staging_path,
            serialized_author,
            runner=runner,
            capture_runner=capture_runner,
        )
        write_books_cpt(staging_path)
        generate_pages(
            staging_path,
            serialized_author,
            serialized_books,
            runner=runner,
            capture_runner=capture_runner,
        )
        setup_header_footer(
            staging_path,
            serialized_author,
            runner=runner,
            capture_runner=capture_runner,
        )
        # Atomically replace the previously-hosted site and start the PHP server.
        host_site(staging_path, hosted_path)

        job.status = GenerationJob.STATUS_COMPLETE
        job.preview_url = PREVIEW_URL
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "preview_url", "completed_at"])

    except Exception as exc:
        if os.path.exists(staging_path):
            shutil.rmtree(staging_path, ignore_errors=True)
        job.status = GenerationJob.STATUS_FAILED
        job.error_message = str(exc) or "Generation failed."
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
