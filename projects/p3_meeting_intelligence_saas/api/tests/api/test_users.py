"""Integration tests for user registration, authentication, and profiles."""


def test_register_user_success(client):
    """Verify successful user registration."""
    res = client.post(
        "/api/v1/users/",
        json={"email": "bob@example.com", "password": "Password123!", "first_name": "Bob", "last_name": "Builder"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "bob@example.com"
    assert data["first_name"] == "Bob"
    assert data["last_name"] == "Builder"
    assert data["avatar"] is None
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    """Verify duplicate user registration returns 409 Conflict."""
    payload = {"email": "duplicate@example.com", "password": "Password123!", "first_name": "Dup"}
    res1 = client.post("/api/v1/users/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/users/", json=payload)
    assert res2.status_code == 409
    assert res2.json()["message"]


def test_register_short_password_rejected(client):
    """Verify validation rejects passwords shorter than 8 characters."""
    res = client.post(
        "/api/v1/users/", json={"email": "short@example.com", "password": "short", "first_name": "S"}
    )
    assert res.status_code == 422
    body = res.json()  # same error shape as every other error
    assert body["error"] == "ValidationError"
    assert body["message"].startswith("password:")
    assert body["details"]["errors"][0]["field"] == "password"


def test_login_wrong_password_fails(client, auth_headers):
    """Verify login with a wrong password returns 401."""
    res = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "WrongPass123!"})
    assert res.status_code == 401


def test_login_and_get_me(client, auth_headers):
    """Verify authenticated user can fetch their own profile."""
    res = client.get("/api/v1/users/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "alice@example.com"
    assert data["first_name"] == "Alice"


def test_update_me(client, auth_headers):
    """Verify the caller can update their own name."""
    res = client.patch(
        "/api/v1/users/me", headers=auth_headers, json={"first_name": "Alicia", "last_name": "Dev"}
    )
    assert res.status_code == 200
    assert (res.json()["first_name"], res.json()["last_name"]) == ("Alicia", "Dev")


def test_unauthorized_access_fails(client):
    """Verify protected endpoints reject requests without token."""
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401


def test_invalid_token_rejected(client):
    """Verify a forged/garbage token is rejected."""
    res = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_user_listing_not_exposed(client, auth_headers):
    """Verify there is no endpoint listing every user's email address."""
    res = client.get("/api/v1/users/", headers=auth_headers)
    assert res.status_code == 405
