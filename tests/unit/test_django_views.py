"""Django view tests for the onboarding app."""

import base64
import json
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import Client
from PIL import Image

from onboarding.models import Author
from onboarding.services import sync_genre_catalog


pytestmark = pytest.mark.django_db


GENRE_TREE = {
    "Fiction": {
        "Science Fiction": ["Cyberpunk", "Space Opera"],
        "Fantasy": ["Epic Fantasy"],
    },
    "Nonfiction": {
        "Biography & Memoir": ["Biography", "Memoir"],
    },
}

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture(autouse=True)
def configured_genres(tmp_path, settings):
    sync_genre_catalog(GENRE_TREE)
    settings.MEDIA_ROOT = tmp_path / "media"


def valid_payload(**overrides):
    payload = {
        "author_name": "Jane Doe",
        "author_email": "contact@example.com",
        "site_domain": "janedoe.com",
        "genres": ["Science Fiction", "Cyberpunk"],
        "books": [
            {
                "title": "The Midnight Code",
                "cover_image_key": "book_0_cover_image",
                "description": "A technological thriller.",
                "buy_links": ["https://example.com/buy"],
                "category": "Fiction",
                "genre": "Science Fiction",
                "subgenre": "Cyberpunk",
                "series_type": "standalone",
            }
        ],
    }
    payload.update(overrides)
    return payload


def image_upload(name="cover.png", content=PNG_BYTES, content_type="image/png"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def generated_image_upload(image_format, extension, content_type):
    content = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(content, format=image_format)
    return image_upload(f"cover.{extension}", content.getvalue(), content_type)


def post_onboarding(client, payload=None, **files):
    data = {"payload": json.dumps(payload or valid_payload())}
    data.update(files or {"book_0_cover_image": image_upload()})
    return client.post("/onboarding", data=data)


@pytest.mark.django_db
def test_onboard_returns_200_and_loads_react_mount(client):
    response = client.get("/onboard")

    assert response.status_code == 200
    assert b'id="onboarding-root"' in response.content
    assert b"/static/onboarding/dist/onboard.js" in response.content


@pytest.mark.django_db
def test_root_redirects_to_onboard(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == "/onboard"


@pytest.mark.django_db
def test_submission_accepts_valid_multipart_data_and_persists_it(client):
    response = post_onboarding(client)

    assert response.status_code == 201
    submission = Author.objects.get()
    assert response.json() == {
        "status": "ok",
        "author_id": str(submission.pk),
        "author_url": f"/authors/{submission.pk}",
        "books_url": f"/authors/{submission.pk}/books",
    }
    assert submission.name == "Jane Doe"
    assert submission.site_domain == "janedoe.com"
    assert submission.books.get().title == "The Midnight Code"
    assert submission.books.get().cover_image.name.startswith(
        f"authors/{submission.pk}/books/"
    )
    assert "cover.png" not in submission.books.get().cover_image.name


def test_submission_rejects_non_post_requests(client):
    assert client.get("/onboarding").status_code == 405


def test_submission_rejects_json_instead_of_multipart(client):
    response = client.post(
        "/onboarding",
        data=json.dumps(valid_payload()),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Request body must be multipart form data."


def test_submission_rejects_missing_or_malformed_payload(client):
    missing = client.post("/onboarding", data={"book_0_cover_image": image_upload()})
    malformed = client.post(
        "/onboarding",
        data={"payload": "{invalid", "book_0_cover_image": image_upload()},
    )

    assert missing.status_code == 400
    assert malformed.status_code == 400
    assert malformed.json()["message"] == "Payload must be valid JSON."


@pytest.mark.django_db
def test_submission_does_not_persist_invalid_submission(client):
    payload = valid_payload(author_email="not-an-email")

    response = post_onboarding(client, payload)

    assert response.status_code == 400
    assert Author.objects.count() == 0


@pytest.mark.django_db
def test_submission_returns_safe_json_when_persistence_fails(client):
    with patch(
        "onboarding.views.persist_onboarding",
        side_effect=DatabaseError("database details"),
    ):
        response = post_onboarding(client)

    assert response.status_code == 500
    assert response.json() == {
        "message": "We could not save your information. Please try again."
    }
    assert Author.objects.count() == 0


def test_submission_reports_missing_genre_catalog(client, configured_genres):
    sync_genre_catalog({})

    response = post_onboarding(client)

    assert response.status_code == 503
    assert response.json()["message"] == "Genre catalog is not configured."


@pytest.mark.parametrize(
    "field",
    ["author_name", "author_email", "site_domain", "genres", "books"],
)
def test_submission_reports_missing_required_fields(client, field):
    payload = valid_payload()
    del payload[field]

    response = post_onboarding(client, payload)

    assert response.status_code == 400
    assert response.json()["message"] == "Please correct the highlighted fields."
    assert field in response.json()["errors"]


def test_submission_requires_declared_book_cover(client):
    response = post_onboarding(client, valid_payload(), unrelated=image_upload())

    assert response.status_code == 400
    assert response.json()["errors"]["books.0.cover_image_key"] == (
        "A cover image is required."
    )


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("cover.svg", b"<svg></svg>", "image/svg+xml"),
        ("cover.png", b"not an image", "image/png"),
        ("cover.txt", b"text", "text/plain"),
    ],
)
def test_submission_rejects_invalid_image_uploads(
    client, filename, content, content_type
):
    response = post_onboarding(
        client,
        valid_payload(),
        book_0_cover_image=image_upload(filename, content, content_type),
    )

    assert response.status_code == 400
    assert "book_0_cover_image" in response.json()["errors"]


def test_submission_rejects_image_over_10_mb(client):
    response = post_onboarding(
        client,
        valid_payload(),
        book_0_cover_image=image_upload(content=b"x" * (10 * 1024 * 1024 + 1)),
    )

    assert response.status_code == 400
    assert response.json()["errors"]["book_0_cover_image"] == (
        "Images must be 10 MB or smaller."
    )


@pytest.mark.parametrize(
    ("image_format", "extension", "content_type"),
    [
        ("JPEG", "jpg", "image/jpeg"),
        ("PNG", "png", "image/png"),
        ("WEBP", "webp", "image/webp"),
    ],
)
def test_submission_accepts_supported_image_types(
    client, image_format, extension, content_type
):
    response = post_onboarding(
        client,
        valid_payload(),
        book_0_cover_image=generated_image_upload(
            image_format,
            extension,
            content_type,
        ),
    )

    assert response.status_code == 201


def test_submission_persists_multiple_books_in_form_order(client):
    payload = valid_payload()
    second_book = {
        **payload["books"][0],
        "title": "Ghost Signal",
        "cover_image_key": "book_1_cover_image",
    }
    payload["books"].append(second_book)

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_1_cover_image=image_upload("second.png"),
    )

    assert response.status_code == 201
    submission = Author.objects.get()
    assert list(submission.books.values_list("title", flat=True)) == [
        "The Midnight Code",
        "Ghost Signal",
    ]


def test_submission_persists_all_nested_book_data_and_uploads(client):
    payload = valid_payload()
    payload["books"][0].update(
        {
            "other_reviews": [
                {
                    "stars": 5,
                    "photo_key": "book_0_other_review_0_photo",
                    "reviewer_name": "Reader One",
                    "quotation": "Excellent.",
                }
            ],
            "awards": [
                {
                    "name": "Best Debut",
                    "icon_key": "book_0_award_0_icon",
                }
            ],
            "sample_chapter_key": "book_0_sample_chapter",
        }
    )

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_other_review_0_photo=image_upload("reader.png"),
        book_0_award_0_icon=image_upload("award.png"),
        book_0_sample_chapter=SimpleUploadedFile(
            "chapter.pdf",
            b"%PDF-1.7\nsample",
            content_type="application/pdf",
        ),
    )

    assert response.status_code == 201
    submission = Author.objects.get()
    book = submission.books.get()
    assert book.reviews.get().reviewer_name == "Reader One"
    assert book.reviews.get().photo_path
    assert book.awards.get().name == "Best Debut"
    assert book.awards.get().icon_path
    assert book.sample_chapter_path


def test_submission_rejects_non_pdf_sample_chapter(client):
    payload = valid_payload()
    payload["books"][0]["sample_chapter_key"] = "book_0_sample_chapter"

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_sample_chapter=SimpleUploadedFile(
            "chapter.pdf",
            b"not a pdf",
            content_type="application/pdf",
        ),
    )

    assert response.status_code == 400
    assert "book_0_sample_chapter" in response.json()["errors"]


def test_submission_rejects_pdf_over_20_mb(client):
    payload = valid_payload()
    payload["books"][0]["sample_chapter_key"] = "book_0_sample_chapter"

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_sample_chapter=SimpleUploadedFile(
            "chapter.pdf",
            b"%PDF-" + b"x" * (20 * 1024 * 1024),
            content_type="application/pdf",
        ),
    )

    assert response.status_code == 400
    assert response.json()["errors"]["book_0_sample_chapter"] == (
        "PDF files must be 20 MB or smaller."
    )


def test_submission_accepts_valid_headshot(client):
    payload = valid_payload(author_headshot_key="author_headshot")

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        author_headshot=image_upload("headshot.png"),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "ok"
    assert Author.objects.filter(
        pk=response.json()["author_id"]
    ).exists()


def test_submission_requires_file_when_headshot_key_is_declared(client):
    payload = valid_payload(author_headshot_key="author_headshot")

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
    )

    assert response.status_code == 400
    assert response.json()["errors"]["author_headshot_key"] == (
        "An author photo is required."
    )


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("headshot.svg", b"<svg></svg>", "image/svg+xml"),
        ("headshot.png", b"not an image", "image/png"),
        ("headshot.txt", b"text", "text/plain"),
    ],
)
def test_submission_rejects_invalid_headshot_image_type(
    client, filename, content, content_type
):
    payload = valid_payload(author_headshot_key="author_headshot")

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        author_headshot=image_upload(filename, content, content_type),
    )

    assert response.status_code == 400
    assert "author_headshot" in response.json()["errors"]


def test_submission_rejects_headshot_over_10_mb(client):
    payload = valid_payload(author_headshot_key="author_headshot")

    response = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        author_headshot=image_upload(content=b"x" * (10 * 1024 * 1024 + 1)),
    )

    assert response.status_code == 400
    assert response.json()["errors"]["author_headshot"] == (
        "Images must be 10 MB or smaller."
    )


def test_submission_accepts_submission_without_headshot_key(client):
    response = post_onboarding(client)

    assert response.status_code == 201


def test_submission_readback_loads_everything_from_the_database(client):
    payload = valid_payload(
        site_tagline="Code after dark",
        author_bio_short="Short biography.",
        author_bio_long="Long biography.",
        primary_color="#112233",
        secondary_color="#abcdef",
        newsletter_link="kit-form-123",
        social_links={
            "twitter": "https://example.com/twitter",
            "goodreads": "https://example.com/goodreads",
        },
    )
    payload["books"][0].update(
        {
            "editorial_reviews": [
                {
                    "reviewer_name": "Kirkus",
                    "quotation": "A sharp debut.",
                    "original_review_url": "https://example.com/review",
                }
            ],
            "other_reviews": [
                {
                    "reviewer_name": "Reader One",
                    "quotation": "Read this.",
                }
            ],
            "perfect_for": "Readers who like code.",
            "enjoy_if": "You enjoy thrillers.",
            "sample_chapter_key": "book_0_sample_chapter",
        }
    )
    created = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_sample_chapter=SimpleUploadedFile(
            "chapter.pdf",
            b"%PDF-1.7\nsample",
            content_type="application/pdf",
        ),
    )
    author_id = created.json()["author_id"]

    author_response = client.get(f"/authors/{author_id}")
    books_response = client.get(f"/authors/{author_id}/books")

    assert author_response.status_code == 200
    assert books_response.status_code == 200
    author_data = author_response.json()
    book_data = books_response.json()[0]
    assert author_data["name"] == "Jane Doe"
    assert author_data["site_tagline"] == "Code after dark"
    assert author_data["genres"] == ["Science Fiction", "Cyberpunk"]
    assert author_data["social_links"]["goodreads"] == "https://example.com/goodreads"
    assert book_data["title"] == "The Midnight Code"
    assert book_data["cover_image_url"].startswith("/media/")
    assert book_data["sample_chapter_url"].startswith("/books/")
    assert book_data["editorial_reviews"][0]["reviewer_name"] == "Kirkus"
    assert book_data["other_reviews"][0]["reviewer_name"] == "Reader One"


def test_sample_chapter_preserves_original_name_and_downloads_with_it(client):
    payload = valid_payload()
    payload["books"][0]["sample_chapter_key"] = "book_0_sample_chapter"
    created = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_sample_chapter=SimpleUploadedFile(
            "My Sample Chapter.pdf",
            b"%PDF-1.7\nsample chapter",
            content_type="application/pdf",
        ),
    )
    author = Author.objects.get(pk=created.json()["author_id"])
    book = author.books.get()

    assert book.sample_chapter_name == "My Sample Chapter.pdf"
    assert book.sample_chapter_path.name.endswith(".pdf")
    assert not book.sample_chapter_path.name.endswith("My Sample Chapter.pdf")

    detail = client.get(f"/books/{book.pk}").json()
    assert detail["sample_chapter_name"] == (
        "My Sample Chapter.pdf"
    )
    assert detail["sample_chapter_url"] == f"/books/{book.pk}/sample-chapter"

    response = client.get(detail["sample_chapter_url"])

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == (
        'attachment; filename="My Sample Chapter.pdf"'
    )
    assert b"".join(response.streaming_content) == b"%PDF-1.7\nsample chapter"


def test_sample_chapter_download_uses_fallback_name_for_legacy_record(client):
    payload = valid_payload()
    payload["books"][0]["sample_chapter_key"] = "book_0_sample_chapter"
    created = post_onboarding(
        client,
        payload,
        book_0_cover_image=image_upload(),
        book_0_sample_chapter=SimpleUploadedFile(
            "chapter.pdf",
            b"%PDF-1.7\nsample",
            content_type="application/pdf",
        ),
    )
    author = Author.objects.get(pk=created.json()["author_id"])
    book = author.books.get()
    book.sample_chapter_name = ""
    book.save(update_fields=["sample_chapter_name"])

    response = client.get(
        f"/books/{book.pk}/sample-chapter"
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == (
        'attachment; filename="sample-chapter.pdf"'
    )
    response.close()


def test_sample_chapter_download_returns_404_when_book_or_file_is_missing(client):
    created = post_onboarding(client)
    author = Author.objects.get(pk=created.json()["author_id"])
    book = author.books.get()

    missing_file = client.get(f"/books/{book.pk}/sample-chapter")
    unknown_book = client.get(
        "/books/00000000-0000-0000-0000-000000000000/sample-chapter"
    )

    assert missing_file.status_code == 404
    assert unknown_book.status_code == 404


def test_author_readback_returns_404_for_unknown_id(client):
    response = client.get("/authors/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_generate_is_a_no_op_for_an_existing_author(client):
    created = post_onboarding(client)
    author_id = created.json()["author_id"]
    before = Author.objects.count()

    response = client.post(
        "/generate",
        data=json.dumps({"author_id": author_id}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "author_id": author_id,
    }
    assert Author.objects.count() == before


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"author_id": "not-a-uuid"},
        {"author_id": "00000000-0000-0000-0000-000000000000"},
    ],
)
def test_generate_rejects_missing_malformed_or_unknown_author(client, body):
    response = client.post(
        "/generate",
        data=json.dumps(body),
        content_type="application/json",
    )

    assert response.status_code == 404
    assert response.json() == {"message": "Author not found."}


def test_submission_cleans_up_database_and_files_when_nested_persistence_fails(
    client, settings
):
    payload = valid_payload()
    payload["books"][0]["awards"] = [
        {"name": "Best Debut", "icon_key": "book_0_award_0_icon"}
    ]

    with patch(
        "onboarding.services.BookAward.save",
        side_effect=DatabaseError("database details"),
    ):
        response = post_onboarding(
            client,
            payload,
            book_0_cover_image=image_upload(),
            book_0_award_0_icon=image_upload("award.png"),
        )

    assert response.status_code == 500
    assert Author.objects.count() == 0
    assert not list(settings.MEDIA_ROOT.rglob("*"))


def test_submission_accepts_valid_selected_template(client):
    payload = valid_payload(selected_template="Classic")
    response = post_onboarding(client, payload)

    assert response.status_code == 201


def test_submission_accepts_submission_without_selected_template(client):
    response = post_onboarding(client)

    assert response.status_code == 201


def test_submission_rejects_unknown_template(client):
    payload = valid_payload(selected_template="NonExistent Template")
    response = post_onboarding(client, payload)

    assert response.status_code == 400
