"""Tests for login/auth logic. Does not test HTML rendering."""


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_login_success_redirects_to_onboard(client):
    response = client.post("/login", data={"username": "testuser", "password": "testpass"})
    assert response.status_code == 302
    assert "/onboard" in response.headers["Location"]


def test_login_success_sets_session(client):
    with client.session_transaction() as sess:
        assert not sess.get("authenticated")
    client.post("/login", data={"username": "testuser", "password": "testpass"})
    with client.session_transaction() as sess:
        assert sess.get("authenticated") is True


def test_login_wrong_password(client):
    response = client.post("/login", data={"username": "testuser", "password": "wrong"})
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_wrong_username(client):
    response = client.post("/login", data={"username": "nobody", "password": "testpass"})
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_empty_credentials(client):
    response = client.post("/login", data={"username": "", "password": ""})
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_onboard_requires_auth(client):
    response = client.get("/onboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_onboard_accessible_when_authenticated(authenticated_client):
    response = authenticated_client.get("/onboard")
    assert response.status_code == 200


def test_root_redirects_to_onboard(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/onboard" in response.headers["Location"]


def test_logout_clears_session(authenticated_client):
    response = authenticated_client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with authenticated_client.session_transaction() as sess:
        assert not sess.get("authenticated")


def test_login_redirects_when_already_authenticated(authenticated_client):
    response = authenticated_client.get("/login")
    assert response.status_code == 302
    assert "/onboard" in response.headers["Location"]


def test_generate_requires_auth_returns_401(client):
    response = client.post("/generate")
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"


def test_generate_stub_returns_ok(authenticated_client):
    response = authenticated_client.post("/generate")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}
