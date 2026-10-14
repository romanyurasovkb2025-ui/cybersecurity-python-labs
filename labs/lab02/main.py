"""Точка входу ЛР №2: команди demo та analyze."""

from __future__ import annotations

import argparse
import sys

from labs.lab02 import task1, task2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="labs.lab02.main", description="ЛР №2")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Демонстрація класів Завдання 1")

    analyze = sub.add_parser("analyze", help="Аудитор HTTP-заголовків (варіант 9)")
    analyze.add_argument("--headers-file", required=True, help="JSON із заголовками")
    analyze.add_argument("--output-csv", required=True, help="Шлях до CSV-звіту")
    analyze.add_argument(
        "--strict", action="store_true", help="Суворий режим оцінювання"
    )
    analyze.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        task1.run_demo()
        return 0
    return task2.run(args.headers_file, args.output_csv, args.strict, args.log_level)


if __name__ == "__main__":
    sys.exit(main())
