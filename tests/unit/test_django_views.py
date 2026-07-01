"""Django view tests for the onboarding app."""

import json
import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_onboard_returns_200(client):
    response = client.get("/onboard")
    assert response.status_code == 200


@pytest.mark.django_db
def test_onboard_template_renders(client):
    response = client.get("/onboard")
    assert response.status_code == 200
    templates = [t.name for t in response.templates]
    assert "onboarding/onboard.html" in templates


@pytest.mark.django_db
def test_onboard_has_form(client):
    response = client.get("/onboard")
    assert b'id="onboarding-root"' in response.content


@pytest.mark.django_db
def test_onboard_loads_frontend_bundle(client):
    response = client.get("/onboard")
    assert b'/static/onboarding/onboard.js' in response.content


@pytest.mark.django_db
def test_divi_templates_in_context(client):
    response = client.get("/onboard")
    assert "divi_templates" in response.context
    assert len(response.context["divi_templates"]) == 6


@pytest.mark.django_db
def test_root_redirects_to_onboard(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"] == "/onboard"


@pytest.mark.django_db
def test_generate_accepts_valid_onboarding_json(client):
    response = client.post(
        "/generate",
        data=json.dumps(
            {
                "author_name": "Jane Doe",
                "author_email": "jane@example.com",
                "website_name": "Jane Doe Books",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_rejects_non_post_requests(client):
    response = client.get("/generate")

    assert response.status_code == 405


def test_generate_rejects_non_json_requests(client):
    response = client.post("/generate", data={"author_name": "Jane Doe"})

    assert response.status_code == 400
    assert response.json()["message"] == "Request body must be valid JSON."


def test_generate_rejects_malformed_json(client):
    response = client.post(
        "/generate", data="{invalid", content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Request body must be valid JSON."


@pytest.mark.parametrize("field", ["author_name", "author_email", "website_name"])
def test_generate_reports_missing_required_fields(client, field):
    data = {
        "author_name": "Jane Doe",
        "author_email": "jane@example.com",
        "website_name": "Jane Doe Books",
    }
    del data[field]

    response = client.post(
        "/generate", data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Please correct the highlighted fields."
    assert field in response.json()["errors"]


def test_generate_reports_invalid_color(client):
    response = client.post(
        "/generate",
        data=json.dumps(
            {
                "author_name": "Jane Doe",
                "author_email": "jane@example.com",
                "website_name": "Jane Doe Books",
                "primary_color": "blue",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "primary_color" in response.json()["errors"]


def test_generate_reports_invalid_social_url(client):
    response = client.post(
        "/generate",
        data=json.dumps(
            {
                "author_name": "Jane Doe",
                "author_email": "jane@example.com",
                "website_name": "Jane Doe Books",
                "social_links": {"instagram": "instagram.com/janedoe"},
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "social_links.instagram" in response.json()["errors"]
