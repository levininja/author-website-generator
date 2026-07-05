"""API contract tests for onboarding orchestration and author/book resources."""

import base64
import json
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import Client

from onboarding.models import Author, Book, Series
from onboarding.services import sync_genre_catalog


pytestmark = pytest.mark.django_db

GENRE_TREE = {
    "Fiction": {
        "Science Fiction": ["Cyberpunk", "Space Opera"],
    },
    "Nonfiction": {
        "Biography & Memoir": ["Biography", "Memoir"],
    },
}

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture(autouse=True)
def catalog_and_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    sync_genre_catalog(GENRE_TREE)


@pytest.fixture
def client():
    return Client()


def onboarding_payload():
    return {
        "author_name": "Jane Doe",
        "author_email": "contact@example.com",
        "site_domain": "janedoe.com",
        "genres": ["Fiction", "Science Fiction", "Cyberpunk"],
        "books": [
            {
                "title": "The Midnight Code",
                "cover_image_key": "book_0_cover_image",
                "description": "A technological thriller.",
                "buy_links": ["https://example.com/buy"],
                "category": "Fiction",
                "genre": "Science Fiction",
                "subgenre": "Cyberpunk",
                "series_type": "series",
                "series_name": "The Signal Cycle",
                "book_number": 2,
                "series_length": 4,
                "series_is_complete": True,
            }
        ],
    }


def create_onboarding(client, payload=None, **files):
    data = {"payload": json.dumps(payload or onboarding_payload())}
    data.update(
        files
        or {
            "book_0_cover_image": SimpleUploadedFile(
                "cover.png",
                PNG_BYTES,
                content_type="image/png",
            )
        }
    )
    return client.post("/onboarding", data=data)


def test_onboarding_creates_author_and_books_then_resources_read_separately(client):
    response = create_onboarding(client)

    assert response.status_code == 201
    author_id = response.json()["author_id"]
    assert response.json()["author_url"] == f"/authors/{author_id}"
    assert response.json()["books_url"] == f"/authors/{author_id}/books"

    author_response = client.get(f"/authors/{author_id}")
    books_response = client.get(f"/authors/{author_id}/books")

    assert author_response.status_code == 200
    assert author_response.json()["name"] == "Jane Doe"
    assert "books" not in author_response.json()
    assert books_response.status_code == 200
    assert books_response.json()[0]["title"] == "The Midnight Code"
    assert books_response.json()[0]["onboarding_position"] == 1
    assert books_response.json()[0]["category"]["name"] == "Fiction"
    assert books_response.json()[0]["genre"]["name"] == "Science Fiction"
    assert books_response.json()[0]["subgenre"]["name"] == "Cyberpunk"
    assert books_response.json()[0]["series"] == {
        "id": str(Series.objects.get().pk),
        "name": "The Signal Cycle",
        "total_books": 4,
        "is_complete": True,
    }
    assert books_response.json()[0]["number_in_series"] == 2


def test_book_resource_and_generation_use_book_and_author_ids(client):
    created = create_onboarding(client)
    author_id = created.json()["author_id"]
    book = Book.objects.get()

    book_response = client.get(f"/books/{book.pk}")
    generated = client.post(
        "/generate",
        data=json.dumps({"author_id": author_id}),
        content_type="application/json",
    )

    assert book_response.status_code == 200
    assert book_response.json()["id"] == str(book.pk)
    assert generated.status_code == 200
    assert generated.json() == {"status": "ok", "author_id": author_id}


def test_obsolete_submission_endpoints_are_not_available(client):
    assert client.post("/submissions").status_code == 404
    assert (
        client.get("/submissions/00000000-0000-0000-0000-000000000000").status_code
        == 404
    )


def test_onboarding_rolls_back_author_when_book_persistence_fails(client):
    with patch(
        "onboarding.views.persist_onboarding",
        side_effect=DatabaseError("book write failed"),
    ):
        response = create_onboarding(client)

    assert response.status_code == 500
    assert Author.objects.count() == 0
    assert Book.objects.count() == 0


def test_genres_endpoint_reads_normalized_catalog(client):
    response = client.get("/genres")

    assert response.status_code == 200
    assert response.json() == GENRE_TREE
