"""Точка входа: приложение FastAPI, обработка ошибок и раздача веб-клиента."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (регистрирует таблицы)
from .database import Base, SessionLocal, engine
from .routers import auth, tickets
from .utils.errors import AppError
from .utils.seed import seed_demo_data

STATIC_DIR = Path(__file__).parent / "static"

FIELD_NAMES = {
    "username": "логин",
    "password": "пароль",
    "full_name": "имя",
    "title": "тема",
    "description": "описание",
    "text": "текст комментария",
    "priority": "приоритет",
    "status": "статус",
    "assignee_id": "исполнитель",
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("SEED_DEMO", "1") == "1":
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(title="Helpdesk: заявки техподдержки", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(tickets.router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    fields = []
    for error in exc.errors():
        name = str(error["loc"][-1]) if error.get("loc") else ""
        label = FIELD_NAMES.get(name, name)
        if label and label not in fields:
            fields.append(label)
    detail = "Проверьте поля: " + ", ".join(fields) if fields else "Проверьте введённые данные"
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/api/health", tags=["service"])
def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
