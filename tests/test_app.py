"""Тесты служебных маршрутов, раздачи клиента и демо-данных."""
from sqlalchemy import func, select

from src.models import Ticket, User
from src.utils.seed import seed_demo_data


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_index_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_seed_creates_demo_data_once(session_factory):
    with session_factory() as db:
        assert seed_demo_data(db) is True
        assert db.scalar(select(func.count(User.id))) == 2
        assert db.scalar(select(func.count(Ticket.id))) == 4
        assert seed_demo_data(db) is False  # повторный запуск ничего не добавляет
        assert db.scalar(select(func.count(Ticket.id))) == 4
