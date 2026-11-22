"""Демо-данные: создаются при первом запуске, если база пустая."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ROLE_AGENT, ROLE_USER, Comment, Ticket, User
from ..security import hash_password

DEMO_USER = ("demo", "demo123", "Иван Петров")
DEMO_AGENT = ("agent", "agent123", "Мария Соколова")


def seed_demo_data(db: Session) -> bool:
    """Возвращает True, если данные были созданы."""
    if db.scalar(select(func.count(User.id))):
        return False

    user = User(username=DEMO_USER[0], password_hash=hash_password(DEMO_USER[1]),
                full_name=DEMO_USER[2], role=ROLE_USER)
    agent = User(username=DEMO_AGENT[0], password_hash=hash_password(DEMO_AGENT[1]),
                 full_name=DEMO_AGENT[2], role=ROLE_AGENT)
    db.add_all([user, agent])
    db.flush()

    tickets = [
        Ticket(title="Не работает принтер на 3 этаже",
               description="Принтер у кабинета 312 печатает пустые листы. Пробовал перезагрузить, не помогло.",
               status="in_progress", priority="high", author_id=user.id, assignee_id=agent.id),
        Ticket(title="Нужен доступ к общей папке бухгалтерии",
               description="Для подготовки отчёта нужен доступ на чтение к папке \\\\fs01\\accounting.",
               status="new", priority="normal", author_id=user.id),
        Ticket(title="Медленно работает Wi-Fi в переговорной",
               description="Во время созвонов пропадает звук. Проблема только в переговорной на 2 этаже.",
               status="new", priority="low", author_id=user.id),
        Ticket(title="Сброс пароля от почты",
               description="Забыл пароль от корпоративной почты, прошу выдать временный.",
               status="resolved", priority="normal", author_id=user.id, assignee_id=agent.id),
    ]
    db.add_all(tickets)
    db.flush()

    db.add_all([
        Comment(ticket_id=tickets[0].id, author_id=agent.id,
                text="Проверила картридж, он пустой. Заменим сегодня до обеда."),
        Comment(ticket_id=tickets[0].id, author_id=user.id, text="Спасибо, подожду."),
        Comment(ticket_id=tickets[3].id, author_id=agent.id,
                text="Временный пароль отправлен на личную почту. Смените его при входе."),
    ])
    db.commit()
    return True
