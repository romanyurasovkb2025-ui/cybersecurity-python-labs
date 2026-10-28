"""FastAPI-застосунок ЛР №3 (варіант 9)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared import student


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску."""
    initialize_database()
    yield


app = FastAPI(
    title="Облік часу опрацювання повідомлень про події безпеки",
    description=(
        f"{config.DOMAIN}. Значення `value` — тривалість перевірки "
        f"у хвилинах ({config.UNIT}); навчальний поріг: {config.THRESHOLD}."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["service"], summary="Перевірка доступності")
def ping() -> dict[str, str]:
    """Повернути стан API."""
    return {"status": "ok"}


@app.get("/student", tags=["service"], summary="Дані студента")
def get_student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": student.STUDENT_NAME,
        "group_name": student.GROUP_NAME,
        "variant_number": student.VARIANT_NUMBER,
    }
