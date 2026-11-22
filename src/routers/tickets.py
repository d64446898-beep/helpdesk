"""Маршруты заявок и комментариев."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import (
    CommentCreate,
    CommentOut,
    StatsOut,
    TicketCreate,
    TicketDetail,
    TicketOut,
    TicketUpdate,
)
from ..services import ticket_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tickets = ticket_service.list_tickets(db, user, status, search)
    return [TicketOut.model_validate(t) for t in tickets]


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return StatsOut(**ticket_service.count_by_status(db, user))


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = ticket_service.create_ticket(db, user, data)
    return TicketOut.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = ticket_service.get_ticket(db, user, ticket_id)
    return TicketDetail.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketDetail)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = ticket_service.update_ticket(db, user, ticket_id, data)
    return TicketDetail.model_validate(ticket)


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    ticket_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = ticket_service.add_comment(db, user, ticket_id, data)
    return CommentOut.model_validate(comment)

