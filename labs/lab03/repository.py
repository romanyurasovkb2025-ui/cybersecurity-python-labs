"""Параметризовані SQL-запити до бази даних."""

import sqlite3
from collections.abc import Sequence
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


class NotFoundError(Exception):
    """Запис або категорію не знайдено."""


class ConflictError(Exception):
    """Порушення унікальності або зв’язку між таблицями."""


_RECORD_SELECT = """
SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
       r.value, r.status
FROM records AS r
JOIN categories AS c ON c.id = r.category_id
"""


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict[str, Any]:
    row = connection.execute(
        _RECORD_SELECT + " WHERE r.id = ?", (record_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено")
    return dict(row)


def _insert_record(connection: sqlite3.Connection, data: dict[str, Any]) -> int:
    cursor = connection.execute(
        "INSERT INTO records (code, title, category_id, value, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            data["code"],
            data["title"],
            data["category_id"],
            data["value"],
            data["status"],
        ),
    )
    row_id = cursor.lastrowid
    if row_id is None:
        raise sqlite3.DatabaseError("Не вдалося отримати id запису")
    return row_id


# ---------- Категорії ----------


def create_category(name: str) -> dict[str, Any]:
    """Створити категорію."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Категорія з такою назвою вже існує") from exc
        return {"id": cursor.lastrowid, "name": name}


def list_categories() -> list[dict[str, Any]]:
    """Отримати категорії за зростанням id."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    with closing(get_connection()) as connection:
        try:
            with connection:
                if not _category_exists(connection, category_id):
                    raise NotFoundError("Категорію не знайдено")
                connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Категорія містить записи") from exc


# ---------- Записи ----------


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Додати запис."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                record_id = _insert_record(connection, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Запис з таким code вже існує") from exc
        return _fetch_record(connection, record_id)


def get_record(record_id: int) -> dict[str, Any]:
    """Отримати запис за id."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        return _fetch_record(connection, record_id)


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Отримати записи з фільтрами та поділом на сторінки."""
    conditions: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)
    sql = _RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def replace_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повністю замінити змінювані поля запису."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                exists = connection.execute(
                    "SELECT 1 FROM records WHERE id = ?", (record_id,)
                ).fetchone()
                if exists is None:
                    raise NotFoundError("Запис не знайдено")
                if not _category_exists(connection, data["category_id"]):
                    raise NotFoundError("Категорію не знайдено")
                connection.execute(
                    "UPDATE records SET code = ?, title = ?, category_id = ?, "
                    "value = ?, status = ? WHERE id = ?",
                    (
                        data["code"],
                        data["title"],
                        data["category_id"],
                        data["value"],
                        data["status"],
                        record_id,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Запис з таким code вже існує") from exc
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise NotFoundError("Запис не знайдено")


def create_records_bulk(items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Атомарно додати пакет записів в одній транзакції."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                for item in items:
                    if not _category_exists(connection, item["category_id"]):
                        raise NotFoundError("Категорію не знайдено")
                ids = [_insert_record(connection, item) for item in items]
        except sqlite3.IntegrityError as exc:
            raise ConflictError("Дублікат code у пакеті або в базі") from exc
        return [_fetch_record(connection, record_id) for record_id in ids]
