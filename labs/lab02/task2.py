"""Завдання 2 (варіант 9): аудитор безпеки HTTP-заголовків відповідей."""

from __future__ import annotations

import csv
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("header_audit")

# Вага кожного заголовка безпеки у загальному індексі (разом 100).
REQUIRED_HEADERS: dict[str, int] = {
    "Strict-Transport-Security": 25,
    "Content-Security-Policy": 25,
    "X-Frame-Options": 15,
    "X-Content-Type-Options": 15,
}
LEAK_HEADERS = ("Server", "X-Powered-By")
LEAK_PENALTY = 10
STRICT_EXTRA_PENALTY = 5

# Назва ПЗ, слеш/пробіл і номер версії: Apache/2.4.41, PHP/7.4.3
VERSION_RE = re.compile(r"[A-Za-z][\w.-]*[/ ]v?\d+(?:\.\d+)+")

CSV_FIELDS = ["resource", "score", "grade", "status", "missing_headers", "leaks"]


@dataclass
class AuditResult:
    resource: str
    score: int
    grade: str
    status: str
    missing: list[str] = field(default_factory=list)
    leaks: dict[str, str] = field(default_factory=dict)


def load_headers(path: Path) -> dict[str, dict[str, str]]:
    """Читає JSON і повертає {ресурс: {заголовок: значення}}.

    Підтримуються формати: {"url": {...}} та [{"url": "...", "headers": {...}}].
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ValueError(f"Некоректний JSON у {path}: {exc}") from exc

    result: dict[str, dict[str, str]] = {}
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise TypeError("Елемент списку має бути об'єктом")
            url = entry.get("url") or entry.get("resource") or entry.get("target")
            hdrs = entry.get("headers")
            if not url or not isinstance(hdrs, dict):
                raise ValueError(f"Запис без url/headers: {entry!r}")
            items.append((url, hdrs))
    else:
        raise TypeError("Очікується JSON-об'єкт або масив")

    for url, hdrs in items:
        if not isinstance(hdrs, dict):
            raise TypeError(f"Заголовки ресурсу {url!r} мають бути об'єктом")
        result[str(url)] = {str(k): str(v) for k, v in hdrs.items()}
    return result


def grade_for(score: int) -> str:
    for threshold, grade in ((95, "A+"), (85, "A"), (75, "B"), (60, "C"), (45, "D")):
        if score >= threshold:
            return grade
    return "F"


def status_for(score: int) -> str:
    if score >= 80:
        return "PASS"
    if score >= 50:
        return "WARN"
    return "FAIL"


def audit_resource(
    resource: str, headers: dict[str, str], strict: bool = False
) -> AuditResult:
    lowered = {k.lower(): v for k, v in headers.items()}
    score = 100
    missing: list[str] = []
    for name, weight in REQUIRED_HEADERS.items():
        value = lowered.get(name.lower())
        if value is None or not value.strip():
            missing.append(name)
            score -= weight
            logger.warning("%s: відсутній заголовок %s", resource, name)

    leaks: dict[str, str] = {}
    for name in LEAK_HEADERS:
        value = lowered.get(name.lower(), "")
        match = VERSION_RE.search(value)
        if match:
            leaks[name] = value
            score -= LEAK_PENALTY
            logger.warning("%s: витік версії у %s: %s", resource, name, value)

    if strict and (missing or leaks):
        score -= STRICT_EXTRA_PENALTY * (len(missing) + len(leaks))

    score = max(score, 0)
    return AuditResult(
        resource, score, grade_for(score), status_for(score), missing, leaks
    )


def write_csv(results: list[AuditResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "resource": r.resource,
                    "score": r.score,
                    "grade": r.grade,
                    "status": r.status,
                    "missing_headers": "; ".join(r.missing) or "None",
                    "leaks": "; ".join(f"{k}: {v}" for k, v in r.leaks.items())
                    or "None",
                }
            )


def print_report(results: list[AuditResult]) -> None:
    print(f"{'Target Resource':<34}{'Score':<14}{'Status':<8}Missing Security Headers")
    print("-" * 90)
    for r in results:
        score = f"{r.score}/100 ({r.grade})"
        missing = ", ".join(r.missing) or "None"
        print(f"{r.resource:<34}{score:<14}{r.status:<8}{missing}")
    leaking = [r for r in results if r.leaks]
    if leaking:
        print("\n=== Server Software Leak Alerts ===")
        for r in leaking:
            for header, value in r.leaks.items():
                print(f"[LEAK] {r.resource} leaks version in '{header}': {value}")


def run(headers_file: str, output_csv: str, strict: bool, log_level: str) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level), format="[%(levelname)s] %(message)s"
    )
    src = Path(headers_file)
    logger.info("Auditing HTTP response headers from %s...", src)
    try:
        data = load_headers(src)
    except FileNotFoundError:
        logger.error("Файл не знайдено: %s", src)
        return 1
    except (ValueError, TypeError, OSError) as exc:
        logger.error("Не вдалося прочитати вхідні дані: %s", exc)
        return 1

    results = [audit_resource(url, hdrs, strict) for url, hdrs in data.items()]
    print_report(results)
    try:
        write_csv(results, Path(output_csv))
    except OSError as exc:
        logger.error("Не вдалося записати звіт: %s", exc)
        return 1
    logger.info("Header audit report generated at %s", output_csv)
    return 0
