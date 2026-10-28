"""Маршрути записів."""

import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response, status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]
NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Дублікат code"}}


def _db_error(exc: sqlite3.Error) -> HTTPException:
    logger.exception("Помилка бази даних", exc_info=exc)
    return HTTPException(500, "Помилка роботи з базою даних")


@router.get("", response_model=list[RecordRead], summary="Список записів")
def list_records(
    category_id: Annotated[int | None, Query(gt=0, description="Категорія")] = None,
    status_filter: Annotated[
        Status | None, Query(alias="status", description="Статус")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(ge=0, allow_inf_nan=False, description="Мінімум value (хв)"),
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=120, description="Підрядок у title"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Макс. записів")] = 20,
    offset: Annotated[int, Query(ge=0, description="Пропустити записів")] = 0,
) -> list[dict]:
    """Повернути записи з фільтрами, відсортовані за id."""
    try:
        return repository.list_records(
            category_id=category_id,
            status=status_filter,
            min_value=min_value,
            q=q,
            limit=limit,
            offset=offset,
        )
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне створення записів",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    payload: Annotated[list[RecordCreate], Body(min_length=1, max_length=100)],
) -> list[dict]:
    """Атомарно створити від 1 до 100 записів."""
    try:
        return repository.create_records_bulk([item.model_dump() for item in payload])
    except repository.NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except repository.ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict:
    """Повернути один запис."""
    try:
        return repository.get_record(record_id)
    except repository.NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(payload: RecordCreate) -> dict:
    """Створити запис."""
    try:
        return repository.create_record(payload.model_dump())
    except repository.NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except repository.ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Замінити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict:
    """Повністю замінити змінювані поля запису."""
    try:
        return repository.replace_record(record_id, payload.model_dump())
    except repository.NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except repository.ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> Response:
    """Видалити запис."""
    try:
        repository.delete_record(record_id)
    except repository.NotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except sqlite3.Error as exc:
        raise _db_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
