"""Общие настройки тестов: отдельная БД в памяти, быстрые пароли."""
import os

# Должно быть выставлено до импорта приложения.
os.environ.setdefault("PBKDF2_ITERATIONS", "1000")
os.environ.setdefault("SEED_DEMO", "0")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src import models  # noqa: F401
from src.database import Base, get_db
from src.main import app
from src.models import ROLE_AGENT, User
from src.security import hash_password


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_agent(session_factory):
    def _make(username="agent", password="agent123"):
        with session_factory() as db:
            user = User(username=username, full_name="Агент", role=ROLE_AGENT,
                        password_hash=hash_password(password))
            db.add(user)
            db.commit()
            return user.id
    return _make


def register_and_login(client, username, password="secret123"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def user_headers(client):
    return register_and_login(client, "ivan")


@pytest.fixture()
def other_headers(client):
    return register_and_login(client, "olga")


@pytest.fixture()
def agent_headers(client, make_agent):
    make_agent()
    res = client.post("/api/auth/login", json={"username": "agent", "password": "agent123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
