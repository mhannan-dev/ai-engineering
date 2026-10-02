"""Integration tests for user registration, authentication, and profiles."""


def test_register_user_success(client):
    """Verify successful user registration."""
    res = client.post(
        "/api/v1/users/",
        json={"email": "bob@example.com", "password": "Password123!", "full_name": "Bob Builder"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "bob@example.com"
    assert data["full_name"] == "Bob Builder"
    assert "id" in data


def test_register_duplicate_email_fails(client):
    """Verify duplicate user registration returns 409 Conflict."""
    payload = {"email": "duplicate@example.com", "password": "Password123!"}
    res1 = client.post("/api/v1/users/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/users/", json=payload)
    assert res2.status_code == 409


def test_login_and_get_me(client, auth_headers):
    """Verify authenticated user can fetch their own profile."""
    res = client.get("/api/v1/users/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Developer"


def test_unauthorized_access_fails(client):
    """Verify protected endpoints reject requests without token."""
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401
