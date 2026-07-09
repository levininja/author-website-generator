import json
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from django.core.files.uploadedfile import UploadedFile
from django.db import DatabaseError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.datastructures import MultiValueDict
from django.views.decorators.http import require_GET, require_POST
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from models.onboarding import DIVI_TEMPLATES, GenreTree, OnboardingForm, validate_genre_tree
from onboarding.models import Author, Book
from onboarding.services import (
    genre_tree_from_database,
    persist_onboarding,
    serialize_author,
    serialize_book,
)

IMAGE_LIMIT = 10 * 1024 * 1024
PDF_LIMIT = 20 * 1024 * 1024
IMAGE_TYPES = {
    "image/jpeg": ({".jpg", ".jpeg"}, "JPEG"),
    "image/png": ({".png"}, "PNG"),
    "image/webp": ({".webp"}, "WEBP"),
}


def index(request: HttpRequest) -> HttpResponse:
    """Redirect the site root to the onboarding page."""
    return redirect("/onboard")


def onboard(request: HttpRequest) -> HttpResponse:
    """Render the public onboarding form."""
    return render(request, "onboarding/onboard.html", {"divi_templates": DIVI_TEMPLATES})


def _format_validation_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"]) or "form"
        message = error["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        errors[field] = message
    return errors


def _load_genre_tree() -> GenreTree:
    return validate_genre_tree(genre_tree_from_database())


def _validate_image(upload: UploadedFile) -> str | None:
    if upload.size > IMAGE_LIMIT:
        return "Images must be 10 MB or smaller."

    expected = IMAGE_TYPES.get(upload.content_type)
    if expected is None:
        return "Use a JPG, PNG, or WebP image."

    extensions, expected_format = expected
    if Path(upload.name).suffix.lower() not in extensions:
        return "Image extension does not match its file type."

    try:
        image = Image.open(upload)
        image.verify()
        actual_format = image.format
    except (UnidentifiedImageError, OSError, SyntaxError):
        return "The uploaded file is not a valid image."
    finally:
        upload.seek(0)

    if actual_format != expected_format:
        return "Image content does not match its declared file type."
    return None


def _validate_pdf(upload: UploadedFile) -> str | None:
    if upload.size > PDF_LIMIT:
        return "PDF files must be 20 MB or smaller."
    if upload.content_type != "application/pdf" or Path(upload.name).suffix.lower() != ".pdf":
        return "Sample chapters must be PDF files."

    signature = upload.read(5)
    upload.seek(0)
    if signature != b"%PDF-":
        return "The uploaded file is not a valid PDF."
    return None


def _validate_file_reference(
    files: MultiValueDict[str, UploadedFile],
    errors: dict[str, str],
    logical_path: str,
    supplied_key: str | None,
    expected_key: str,
    validator: Callable[[UploadedFile], str | None],
    missing_message: str,
) -> None:
    if supplied_key != expected_key:
        errors[logical_path] = "Invalid upload reference."
        return

    upload = files.get(expected_key)
    if upload is None:
        errors[logical_path] = missing_message
        return

    error = validator(upload)
    if error:
        errors[expected_key] = error


def _validate_uploaded_files(
    form: OnboardingForm,
    files: MultiValueDict[str, UploadedFile],
) -> dict[str, str]:
    errors: dict[str, str] = {}
    for book_index, book in enumerate(form.books):
        _validate_file_reference(
            files,
            errors,
            f"books.{book_index}.cover_image_key",
            book.cover_image_key,
            f"book_{book_index}_cover_image",
            _validate_image,
            "A cover image is required.",
        )

        for review_type, reviews in (
            ("editorial_review", book.editorial_reviews),
            ("other_review", book.other_reviews),
        ):
            for review_index, review in enumerate(reviews):
                if review.photo_key is not None:
                    _validate_file_reference(
                        files,
                        errors,
                        (
                            f"books.{book_index}.{review_type}s."
                            f"{review_index}.photo_key"
                        ),
                        review.photo_key,
                        (
                            f"book_{book_index}_{review_type}_"
                            f"{review_index}_photo"
                        ),
                        _validate_image,
                        "The selected reviewer photo is missing.",
                    )

        for award_index, award in enumerate(book.awards):
            _validate_file_reference(
                files,
                errors,
                f"books.{book_index}.awards.{award_index}.icon_key",
                award.icon_key,
                f"book_{book_index}_award_{award_index}_icon",
                _validate_image,
                "An award icon is required.",
            )

        if book.sample_chapter_key is not None:
            _validate_file_reference(
                files,
                errors,
                f"books.{book_index}.sample_chapter_key",
                book.sample_chapter_key,
                f"book_{book_index}_sample_chapter",
                _validate_pdf,
                "The selected sample chapter is missing.",
            )

    if form.author_headshot_key is not None:
        _validate_file_reference(
            files,
            errors,
            "author_headshot_key",
            form.author_headshot_key,
            "author_headshot",
            _validate_image,
            "An author photo is required.",
        )

    return errors


@require_POST
def create_onboarding(request: HttpRequest) -> JsonResponse:
    """Validate and persist a multipart onboarding submission."""
    if request.content_type != "multipart/form-data":
        return JsonResponse(
            {"message": "Request body must be multipart form data."},
            status=400,
        )

    raw_payload = request.POST.get("payload")
    if raw_payload is None:
        return JsonResponse({"message": "Payload must be valid JSON."}, status=400)

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Payload must be valid JSON."}, status=400)

    try:
        genre_tree = _load_genre_tree()
    except ValueError:
        return JsonResponse(
            {"message": "Genre catalog is not configured."},
            status=503,
        )

    try:
        form = OnboardingForm.model_validate(
            payload,
            context={"genre_tree": genre_tree},
        )
    except ValidationError as exc:
        return JsonResponse(
            {
                "message": "Please correct the highlighted fields.",
                "errors": _format_validation_errors(exc),
            },
            status=400,
        )

    file_errors = _validate_uploaded_files(form, request.FILES)
    if file_errors:
        return JsonResponse(
            {
                "message": "Please correct the highlighted fields.",
                "errors": file_errors,
            },
            status=400,
        )

    replace_author = None
    replace_id = request.POST.get("replace_author_id")
    if replace_id:
        replace_author = Author.objects.filter(pk=replace_id).first()

    try:
        author = persist_onboarding(
            form,
            request.FILES,
            replace_author=replace_author,
        )
    except (DatabaseError, OSError, ValueError):
        return JsonResponse(
            {"message": "We could not save your information. Please try again."},
            status=500,
        )

    return JsonResponse(
        {
            "status": "ok",
            "author_id": str(author.pk),
            "author_url": f"/authors/{author.pk}",
            "books_url": f"/authors/{author.pk}/books",
        },
        status=201,
    )


@require_GET
def genres(request: HttpRequest) -> JsonResponse:
    """Return the configured onboarding genre catalog."""
    try:
        tree = _load_genre_tree()
    except ValueError:
        return JsonResponse(
            {"message": "Genre catalog is not configured."},
            status=503,
        )
    return JsonResponse(tree)


@require_GET
def author_detail(request: HttpRequest, author_id: UUID) -> JsonResponse:
    """Return one persisted author's review data."""
    author = (
        Author.objects.prefetch_related(
            "authorcategory_set__category",
            "authorgenre_set__genre",
            "authorsubgenre_set__subgenre",
        )
        .filter(pk=author_id)
        .first()
    )
    if author is None:
        return JsonResponse({"message": "Author not found."}, status=404)
    return JsonResponse(serialize_author(author))


@require_GET
def author_books(request: HttpRequest, author_id: UUID) -> JsonResponse:
    """Return all persisted books for an author."""
    if not Author.objects.filter(pk=author_id).exists():
        return JsonResponse({"message": "Author not found."}, status=404)
    books = (
        Book.objects.filter(author_id=author_id)
        .select_related("genre__category", "subgenre", "series")
        .prefetch_related(
            "reviews",
            "awards",
        )
    )
    return JsonResponse([serialize_book(book) for book in books], safe=False)


@require_GET
def book_detail(request: HttpRequest, book_id: UUID) -> JsonResponse:
    """Return one persisted book's review data."""
    book = (
        Book.objects.select_related("genre__category", "subgenre", "series")
        .prefetch_related(
            "reviews",
            "awards",
        )
        .filter(pk=book_id)
        .first()
    )
    if book is None:
        return JsonResponse({"message": "Book not found."}, status=404)
    return JsonResponse(serialize_book(book))


@require_GET
def download_sample_chapter(request: HttpRequest, book_id: UUID) -> FileResponse:
    """Stream a persisted sample chapter PDF for download."""
    book = (
        Book.objects.filter(pk=book_id)
        .only("sample_chapter_path", "sample_chapter_name")
        .first()
    )
    if book is None or not book.sample_chapter_path:
        raise Http404

    try:
        chapter = book.sample_chapter_path.open("rb")
    except (FileNotFoundError, OSError) as exc:
        raise Http404 from exc

    return FileResponse(
        chapter,
        as_attachment=True,
        filename=book.sample_chapter_name or "sample-chapter.pdf",
        content_type="application/pdf",
    )


@require_POST
def generate(request: HttpRequest) -> JsonResponse:
    """Validate a saved author before starting the generation flow."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}

    try:
        author_id = UUID(str(payload.get("author_id")))
    except (TypeError, ValueError, AttributeError):
        author_id = None
    author = Author.objects.filter(pk=author_id).first()
    if author is None:
        return JsonResponse({"message": "Author not found."}, status=404)

    return JsonResponse(
        {
            "status": "ok",
            "author_id": str(author.pk),
        }
    )
