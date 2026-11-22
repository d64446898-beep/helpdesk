"""Логика работы с заявками и комментариями."""
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import STATUSES, Comment, Ticket, User, utcnow
from ..schemas import CommentCreate, TicketCreate, TicketUpdate
from ..utils.errors import AppError


def _visible_query(user: User):
    """Агент видит все заявки, обычный пользователь только свои."""
    query = select(Ticket)
    if not user.is_agent:
        query = query.where(Ticket.author_id == user.id)
    return query


def list_tickets(
    db: Session,
    user: User,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Ticket]:
    query = _visible_query(user)
    if status:
        if status not in STATUSES:
            raise AppError(422, "Неизвестный статус заявки")
        query = query.where(Ticket.status == status)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Ticket.title.ilike(pattern), Ticket.description.ilike(pattern)))
    return list(db.scalars(query.order_by(Ticket.updated_at.desc(), Ticket.id.desc())))


def get_ticket(db: Session, user: User, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise AppError(404, "Заявка не найдена")
    if not user.is_agent and ticket.author_id != user.id:
        raise AppError(403, "Это чужая заявка")
    return ticket


def create_ticket(db: Session, user: User, data: TicketCreate) -> Ticket:
    ticket = Ticket(
        title=data.title,
        description=data.description,
        priority=data.priority,
        author_id=user.id,
    )
    db.add(ticket)
    db.commit()
    return ticket


def update_ticket(db: Session, user: User, ticket_id: int, data: TicketUpdate) -> Ticket:
    ticket = get_ticket(db, user, ticket_id)
    changes = data.model_dump(exclude_unset=True)

    if user.is_agent:
        if "assignee_id" in changes:
            assignee_id = changes["assignee_id"]
            if assignee_id is not None:
                assignee = db.get(User, assignee_id)
                if assignee is None or not assignee.is_agent:
                    raise AppError(422, "Назначить можно только сотрудника поддержки")
            ticket.assignee_id = assignee_id
        if changes.get("status"):
            ticket.status = changes["status"]
        if changes.get("priority"):
            ticket.priority = changes["priority"]
    else:
        # Автор может только закрыть свою заявку или вернуть её в работу.
        if set(changes) - {"status"}:
            raise AppError(403, "Менять приоритет и исполнителя может только поддержка")
        new_status = changes.get("status")
        if new_status == "closed" and ticket.status != "closed":
            ticket.status = "closed"
        elif new_status == "new" and ticket.status in ("resolved", "closed"):
            ticket.status = "new"
        elif new_status and new_status != ticket.status:
            raise AppError(403, "Вы можете только закрыть заявку или открыть её заново")

    ticket.updated_at = utcnow()
    db.commit()
    return ticket


def add_comment(db: Session, user: User, ticket_id: int, data: CommentCreate) -> Comment:
    ticket = get_ticket(db, user, ticket_id)
    if ticket.status == "closed":
        raise AppError(409, "Заявка закрыта. Откройте её заново, чтобы написать комментарий")
    comment = Comment(ticket_id=ticket.id, author_id=user.id, text=data.text)
    ticket.updated_at = utcnow()
    db.add(comment)
    db.commit()
    return comment


def count_by_status(db: Session, user: User) -> dict[str, int]:
    tickets = db.scalars(_visible_query(user)).all()
    result = {status: 0 for status in STATUSES}
    for ticket in tickets:
        result[ticket.status] += 1
    result["total"] = len(tickets)
    return result
