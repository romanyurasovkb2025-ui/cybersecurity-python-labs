"""Завдання 3: Безпечне хешування, CSV-база та JSON-логування з винятками."""

import csv
import functools
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import VARIANT_NUMBER

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_PATH = os.path.join(DATA_DIR, "log.json")

MIN_PASSWORD_LENGTH = 13
PERSONAL_SALT = f"{VARIANT_NUMBER:05d}"


class ValidationError(Exception):
    """Виняток при невідповідності пароля мінімальним вимогам."""


def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує хеш sha224 від пароля з сіллю з перевіркою параметрів."""
    try:
        if not password or not salt:
            raise ValueError("Пароль та сіль не можуть бути порожніми.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(
                f"Пароль закороткий (< {MIN_PASSWORD_LENGTH} символів)."
            )

        return hashlib.sha224((password + salt).encode("utf-8")).hexdigest()
    except (ValueError, ValidationError):
        raise
    except (TypeError, UnicodeError) as exc:
        raise RuntimeError(f"Непередбачена помилка хешування: {exc}") from exc


def log_event(func):
    """Декоратор для безпечного логування спроб автентифікації у JSON-файл."""

    @functools.wraps(func)
    def wrapper(username: str, password: str, *args, **kwargs):
        success = False
        try:
            result = func(username, password, *args, **kwargs)
            success = bool(result)
            return result
        except (ValueError, TypeError, ValidationError) as exc:
            print(f"[Помилка виклику автентифікації] {username}: {exc}")
            return False
        finally:
            log_record = {
                "event": "login",
                "user": username,
                "result": "success" if success else "failure",
                "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                "args": [username],
                "kwargs": {},
            }
            logs = []
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                if os.path.exists(LOG_PATH):
                    try:
                        with open(LOG_PATH, "r", encoding="utf-8") as lf:
                            logs = json.load(lf)
                    except (OSError, json.JSONDecodeError):
                        logs = []

                logs.append(log_record)
                with open(LOG_PATH, "w", encoding="utf-8") as lf:
                    json.dump(logs, lf, ensure_ascii=False, indent=4)
            except OSError as io_err:
                print(f"[Помилка запису логів у JSON]: {io_err}", file=sys.stderr)

    return wrapper


def create_user(username: str, password: str) -> tuple:
    """Створює запис користувача з хешем пароля."""
    pwd_hash = generate_hash(password, PERSONAL_SALT)
    return username, pwd_hash


def create_users(users_list: list) -> None:
    """Записує список користувачів у CSV-базу даних з ізоляцією помилок."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for u, p in users_list:
                try:
                    rec = create_user(u, p)
                    writer.writerow(rec)
                except (ValueError, ValidationError) as e:
                    print(f"[Помилка реєстрації] {u}: {e}")
                except (TypeError, csv.Error) as e:
                    print(f"[Невідома помилка реєстрації] {u}: {e}")
    except OSError as e:
        print(f"[Помилка доступу до файлу CSV]: {e}", file=sys.stderr)


def read_users_db() -> list:
    """Зчитує користувачів з CSV-файлу з перехопленням винятків."""
    db = []
    try:
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"Файл бази даних не знайдено: {CSV_PATH}")

        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    db.append((row[0], row[1]))
    except (FileNotFoundError, OSError, csv.Error) as err:
        print(f"[Збій читання бази користувачів]: {err}", file=sys.stderr)
    return db


@log_event
def login(username: str, password: str, users_db: list) -> bool:
    """Автентифікує користувача, гарантуючи повернення False при збоях."""
    try:
        if not username or not password:
            raise ValueError("Логін або пароль не можуть бути порожніми.")

        current_hash = generate_hash(password, PERSONAL_SALT)

        for db_user, db_hash in users_db:
            if db_user == username and db_hash == current_hash:
                return True
    except (ValidationError, ValueError, TypeError):
        return False

    return False


def run_task3() -> None:
    """Головна функція виконання Завдання 3 із чистим виведенням."""
    print("\n" + "=" * 60)
    print("ЗАВДАННЯ 3: ХЕШУВАННЯ ТА ЛОГУВАННЯ")
    print("=" * 60)

    users_to_register = (
        ("admin_root", "UltraSecretKey2026!"),
        ("dev_alex", "SuperLongDevPass123"),
        ("sec_officer", "CorporateCyberSec#9"),
        ("analyst_olha", "DataSecurityPassWord_"),
        ("qa_mark", "MarkPasswordTest#12"),
        ("ops_stepan", "DevOpsPipelinePass#"),
        ("guest_user", "Short_123"),
        ("lead_taras", "SecureClusterAccess99!"),
        ("intern_dmytro", "JuniorDevCyberPass_1"),
        ("audit_clara", "AuditLogSecurityPass2026"),
    )

    try:
        create_users(users_to_register)
        db = read_users_db()

        print("\nБаза користувачів з users.csv:")
        print(f"{'Username':<15} | {'SHA-224 Hash'}")
        print("-" * 75)
        for u, h in db:
            print(f"{u:<15} | {h}")

        print("\nТестування входу (з логуванням у log.json):")
        test_attempts = [
            ("admin_root", "UltraSecretKey2026!"),
            ("dev_alex", "WrongPassword12345"),
            ("unknown_user", "AnyValidPassword123!"),
            ("", "EmptyUsernameTest123"),
        ]

        for u, p in test_attempts:
            status = login(u, p, db)
            print(
                f"Спроба входу: user={u:<13} -> {'УСПІШНО' if status else 'ВІДХИЛЕНО'}"
            )

    except (OSError, RuntimeError) as fatal_err:
        print(f"[Критична помилка в Завданні 3]: {fatal_err}", file=sys.stderr)


if __name__ == "__main__":
    run_task3()