"""Tests for POST /generate and GET /generate/<job_id>/status endpoints."""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def author():
    from onboarding.models import Author
    return Author.objects.create(
        name="Jane Doe",
        contact_email="jane@example.com",
        site_domain="janedoe.com",
    )


def post_generate(client, author_id):
    return client.post(
        "/generate",
        data=json.dumps({"author_id": str(author_id)}),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# POST /generate — happy path
# ---------------------------------------------------------------------------


def test_post_generate_returns_202_and_job_id_for_valid_author(client, author):
    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    uuid.UUID(data["job_id"])  # must be a valid UUID


def test_post_generate_creates_pending_generation_job_in_database(client, author):
    from onboarding.models import GenerationJob
    with patch("onboarding.views.threading.Thread"):
        post_generate(client, author.pk)

    job = GenerationJob.objects.get(author=author)
    assert job.status == GenerationJob.STATUS_PENDING


def test_post_generate_returned_job_id_matches_database_record(client, author):
    from onboarding.models import GenerationJob
    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    job_id = response.json()["job_id"]
    assert GenerationJob.objects.filter(pk=job_id).exists()


def test_post_generate_spawns_a_background_thread(client, author):
    with patch("onboarding.views.threading.Thread") as mock_thread_cls:
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread
        post_generate(client, author.pk)

    assert mock_thread.start.called


# ---------------------------------------------------------------------------
# POST /generate — validation errors
# ---------------------------------------------------------------------------


def test_post_generate_returns_404_for_unknown_author_id(client):
    response = post_generate(client, uuid.uuid4())

    assert response.status_code == 404
    assert response.json() == {"message": "Author not found."}


def test_post_generate_returns_404_for_malformed_author_id(client):
    response = client.post(
        "/generate",
        data=json.dumps({"author_id": "not-a-uuid"}),
        content_type="application/json",
    )

    assert response.status_code == 404


def test_post_generate_returns_404_when_author_id_is_missing(client):
    response = client.post(
        "/generate",
        data=json.dumps({}),
        content_type="application/json",
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /generate — duplicate job rejection
# ---------------------------------------------------------------------------


def test_post_generate_rejects_when_pending_job_already_exists(client, author):
    from onboarding.models import GenerationJob
    GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_PENDING)

    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    assert response.status_code == 409
    assert "job" in response.json().get("message", "").lower()


def test_post_generate_rejects_when_running_job_already_exists(client, author):
    from onboarding.models import GenerationJob
    GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_RUNNING)

    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    assert response.status_code == 409


def test_post_generate_allows_new_job_when_previous_job_is_complete(client, author):
    from onboarding.models import GenerationJob
    GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_COMPLETE)

    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    assert response.status_code == 202


def test_post_generate_allows_new_job_when_previous_job_is_failed(client, author):
    from onboarding.models import GenerationJob
    GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_FAILED)

    with patch("onboarding.views.threading.Thread"):
        response = post_generate(client, author.pk)

    assert response.status_code == 202


# ---------------------------------------------------------------------------
# GET /generate/<job_id>/status
# ---------------------------------------------------------------------------


def test_get_job_status_returns_200_and_pending_for_pending_job(client, author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_PENDING)

    response = client.get(f"/generate/{job.pk}/status")

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_get_job_status_returns_running_for_running_job(client, author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_RUNNING)

    response = client.get(f"/generate/{job.pk}/status")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_get_job_status_includes_null_preview_url_on_complete_when_not_set(client, author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(author=author, status=GenerationJob.STATUS_COMPLETE)

    response = client.get(f"/generate/{job.pk}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"
    assert "preview_url" in data
    assert data["preview_url"] is None


def test_get_job_status_returns_preview_url_from_job_record(client, author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(
        author=author,
        status=GenerationJob.STATUS_COMPLETE,
        preview_url="http://localhost:8080",
    )

    response = client.get(f"/generate/{job.pk}/status")

    assert response.status_code == 200
    assert response.json()["preview_url"] == "http://localhost:8080"


def test_get_job_status_includes_error_message_on_failed(client, author):
    from onboarding.models import GenerationJob
    job = GenerationJob.objects.create(
        author=author,
        status=GenerationJob.STATUS_FAILED,
        error_message="WP-CLI exited with code 1.",
    )

    response = client.get(f"/generate/{job.pk}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "WP-CLI exited with code 1."


def test_get_job_status_returns_404_for_unknown_job_id(client):
    response = client.get(f"/generate/{uuid.uuid4()}/status")

    assert response.status_code == 404
    assert response.json() == {"message": "Job not found."}
