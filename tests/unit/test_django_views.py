"""Django view tests for the migrated onboarding app."""

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
    assert b"<form" in response.content


@pytest.mark.django_db
def test_onboard_has_generate_site_button(client):
    response = client.get("/onboard")
    assert b"Generate Site" in response.content


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
def test_generate_returns_ok_json(client):
    response = client.post("/generate")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}
