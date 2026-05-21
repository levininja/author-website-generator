import os
import textwrap
import pytest
from app import create_app


MINIMAL_CONFIG_YAML = textwrap.dedent("""\
    servers:
      - id: shared-standard
        name: Shared Non-Ecommerce Server
        type: shared_standard
        ip: 1.2.3.4
        cloudways_server_id: cw-test-123
""")


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(MINIMAL_CONFIG_YAML)
    return str(cfg)


@pytest.fixture
def client(monkeypatch, config_file):
    monkeypatch.setenv("ADMIN_USERNAME", "testuser")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    app = create_app(config_path=config_file)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def authenticated_client(client):
    """A test client that has already completed the login flow."""
    client.post("/login", data={"username": "testuser", "password": "testpass"})
    return client
