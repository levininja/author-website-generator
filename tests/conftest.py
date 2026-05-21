import pytest
import app as app_module
from app import app


@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.setattr(app_module, "APP_USERNAME", "testuser")
    monkeypatch.setattr(app_module, "APP_PASSWORD", "testpass")
    with app.test_client() as c:
        yield c


@pytest.fixture
def authenticated_client(client):
    """A test client that has already completed the login flow."""
    client.post("/login", data={"username": "testuser", "password": "testpass"})
    return client
