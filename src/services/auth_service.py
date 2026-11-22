"""Логика регистрации и входа."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ROLE_USER, User
from ..schemas import LoginIn, RegisterIn
from ..security import create_access_token, hash_password, verify_password
from ..utils.errors import AppError


def register_user(db: Session, data: RegisterIn) -> User:
    exists = db.scalar(select(User).where(User.username == data.username))
    if exists:
        raise AppError(409, "Такой логин уже занят")
    user = User(
        username=data.username,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=ROLE_USER,
    )
    db.add(user)
    db.commit()
    return user


def login_user(db: Session, data: LoginIn) -> str:
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise AppError(401, "Неверный логин или пароль")
    return create_access_token(user.id)
