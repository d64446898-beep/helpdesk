"""Тесты регистрации, входа и защиты маршрутов."""


def test_register_creates_user_with_role_user(client):
    res = client.post("/api/auth/register",
                      json={"username": "Ivan", "password": "secret123", "full_name": "Иван"})
    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "ivan"  # логин приводится к нижнему регистру
    assert body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_username(client):
    data = {"username": "ivan", "password": "secret123"}
    assert client.post("/api/auth/register", json=data).status_code == 201
    res = client.post("/api/auth/register", json=data)
    assert res.status_code == 409
    assert "занят" in res.json()["detail"]


def test_register_validation_error_is_in_russian(client):
    res = client.post("/api/auth/register", json={"username": "iv", "password": "123"})
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert "логин" in detail and "пароль" in detail


def test_login_success_returns_token(client):
    client.post("/api/auth/register", json={"username": "ivan", "password": "secret123"})
    res = client.post("/api/auth/login", json={"username": "ivan", "password": "secret123"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "ivan", "password": "secret123"})
    res = client.post("/api/auth/login", json={"username": "ivan", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert res.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_garbage_token(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert res.status_code == 401


def test_me_returns_profile(client, user_headers):
    res = client.get("/api/auth/me", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "ivan"


def test_tickets_require_auth(client):
    assert client.get("/api/tickets").status_code == 401
    assert client.post("/api/tickets", json={"title": "abc", "description": "x"}).status_code == 401
