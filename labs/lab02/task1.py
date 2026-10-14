"""Завдання 1: модель користувача, сеансів та журналу аудиту."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import ClassVar

PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 16
SESSION_TIMEOUT_SEC = 900

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User:
    """Користувач із безпечним зберіганням пароля."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "user",
        active: bool = True,
        password: str | None = None,
    ) -> None:
        self.username = username
        self.email = email  # проходить через setter із валідацією
        self.role = role
        self.active = active
        self.__password_hash: bytes = b""
        self.__password_salt: bytes = b""
        if password is not None:
            self.set_password(password)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
            raise ValueError(f"Некоректний email: {value!r}")
        self._email = value

    @staticmethod
    def _derive(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )

    def set_password(self, password: str) -> None:
        if not password:
            raise ValueError("Пароль не може бути порожнім")
        self.__password_salt = os.urandom(SALT_SIZE)
        self.__password_hash = self._derive(password, self.__password_salt)

    def check_password(self, password: str) -> bool:
        if not self.__password_hash:
            return False
        candidate = self._derive(password, self.__password_salt)
        return hmac.compare_digest(candidate, self.__password_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        state = "active" if self.active else "inactive"
        return f"User(username={self.username}, email={self.email}, role={self.role}, {state})"


class Admin(User):
    """Адміністратор: користувач із набором дозволів."""

    def __init__(
        self,
        username: str,
        email: str,
        active: bool = True,
        password: str | None = None,
        permissions: set[str] | None = None,
    ) -> None:
        super().__init__(
            username, email, role="admin", active=active, password=password
        )
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        perms = ", ".join(sorted(self.permissions)) or "none"
        return f"{super().__str__()} permissions=[{perms}]"


class Session:
    """Сеанс користувача (час у UTC)."""

    def __init__(self, ip: str, login_time: datetime | None = None) -> None:
        now = _utcnow()
        self.ip = ip
        self.login_time = login_time or now
        self.last_activity = self.login_time

    def touch(self) -> None:
        self.last_activity = _utcnow()

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути додатним")
        return _utcnow() - self.last_activity <= timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    username: str
    action: str
    timestamp: datetime = field(default_factory=_utcnow)


class AuditLog:
    """Журнал аудиту (паролі в журнал не потрапляють)."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        self.records.append(AuditRecord(username, action))

    def show_all(self) -> None:
        for r in self.records:
            print(
                f"{r.timestamp.isoformat(timespec='seconds')} | {r.username} | {r.action}"
            )


class UserAccount:
    """Композиція User + Session + AuditLog."""

    _ALLOWED_KEYS: ClassVar[dict[str, type | tuple[type, ...]]] = {
        "user": User,
        "session": (Session, type(None)),
        "audit": AuditLog,
    }

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit: AuditLog | None = None,
    ) -> None:
        self._data: dict[str, object] = {
            "user": user,
            "session": session,
            "audit": audit if audit is not None else AuditLog(),
        }

    def login(self, username: str, password: str, ip: str) -> bool:
        user: User = self._data["user"]  # type: ignore[assignment]
        audit: AuditLog = self._data["audit"]  # type: ignore[assignment]
        ok = user.active and username == user.username and user.check_password(password)
        if not ok:
            audit.add_log(username, "login_failure")
            return False
        session = Session(ip)
        session.touch()
        self._data["session"] = session
        audit.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        session = self._data["session"]
        if session is None:
            return False
        return session.is_active(SESSION_TIMEOUT_SEC)  # type: ignore[union-attr]

    def logout(self) -> None:
        session = self._data["session"]
        if session is None:
            return
        user: User = self._data["user"]  # type: ignore[assignment]
        audit: AuditLog = self._data["audit"]  # type: ignore[assignment]
        self._data["session"] = None
        audit.add_log(user.username, "logout")

    def __getitem__(self, key: str) -> object:
        if key not in self._ALLOWED_KEYS:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value: object) -> None:
        if key not in self._ALLOWED_KEYS:
            raise KeyError(key)
        if not isinstance(value, self._ALLOWED_KEYS[key]):
            raise TypeError(f"Неправильний тип для {key!r}: {type(value).__name__}")
        self._data[key] = value


def run_demo() -> None:
    """Демонстрація роботи класів Завдання 1."""
    admin = Admin("alice_admin", "alice_admin@example.com", password="S3cret!pass")
    account = UserAccount(admin)

    print("== Вхід ==")
    print("Невдалий вхід:", account.login("alice_admin", "wrong", "10.0.0.5"))
    print("Успішний вхід:", account.login("alice_admin", "S3cret!pass", "10.0.0.5"))
    print("Автентифікований:", account.is_authenticated())

    print("\n== Зміна email ==")
    admin.email = "alice_new@example.org"
    print("Новий email:", admin.email)
    try:
        admin.email = "1bad@x"
    except ValueError as exc:
        print("Помилка валідації:", exc)

    print("\n== Права адміністратора ==")
    admin.grant_permission("read_logs")
    admin.grant_permission("manage_users")
    admin.revoke_permission("read_logs")
    print(admin)
    print("has manage_users:", admin.has_permission("manage_users"))

    print("\n== Доступ через ключі ==")
    print(account["user"])
    for key, value in (("password", 1), ("user", "not-a-user")):
        try:
            account[key] = value
        except (KeyError, TypeError) as exc:
            print(f"{type(exc).__name__}: {exc}")

    print("\n== Таймаут сеансу ==")
    session: Session = account["session"]  # type: ignore[assignment]
    session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 60)
    print("Автентифікований після простою:", account.is_authenticated())

    print("\n== Вихід ==")
    account.login("alice_admin", "S3cret!pass", "10.0.0.5")
    account.logout()
    print("Автентифікований:", account.is_authenticated())

    print("\n== Журнал аудиту ==")
    audit: AuditLog = account["audit"]  # type: ignore[assignment]
    audit.show_all()
