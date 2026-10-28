"""Початкове заповнення бази з JSON."""

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from pydantic import ValidationError

from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


def seed_database() -> str:
    """Заповнити порожню базу; повернути повідомлення про результат."""
    try:
        payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        categories = payload["categories"]
        records = payload["records"]
        for category in categories:
            CategoryCreate(name=category["name"])
            if int(category["id"]) <= 0:
                raise ValueError("id категорії має бути додатним")
        for record in records:
            RecordCreate(**record)
    except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
        return f"Помилка початкових даних: {exc}"

    initialize_database()
    with closing(get_connection()) as connection:
        count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        count += connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if count:
            return "База вже містить дані; заповнення пропущено."
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(c["id"], c["name"]) for c in categories],
                )
                connection.executemany(
                    "INSERT INTO records (code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            r["code"],
                            r["title"],
                            r["category_id"],
                            r["value"],
                            r["status"],
                        )
                        for r in records
                    ],
                )
        except sqlite3.Error as exc:
            return f"Помилка заповнення, зміни скасовано: {exc}"
    return f"Додано {len(categories)} категорії та {len(records)} записів."


if __name__ == "__main__":
    message = seed_database()
    print(message)
    if message.startswith("Помилка"):
        sys.exit(1)
