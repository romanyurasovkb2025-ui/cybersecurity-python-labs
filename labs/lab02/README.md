# Лабораторна робота №2

**Варіант 9:** Аудитор безпеки HTTP-заголовків відповідей.

## Залежності

```bash
pip install -r requirements.txt
```

## Структура файлів

```
labs/lab02/
├── __init__.py
├── main.py        # точка входу: команди demo та analyze
├── task1.py       # Завдання 1: User, Admin, Session, AuditLog, UserAccount
├── task2.py       # Завдання 2: аудитор HTTP-заголовків
├── README.md
└── data/
    ├── data_v09/
    │   └── headers.json   # вхідний JSON із заголовками
    └── report.csv         # вихідний CSV-звіт (створюється програмою)
```

## Запуск

Усі команди виконуються з кореня репозиторію.

**Завдання 1** (демонстрація класів):

```bash
python -m labs.lab02.main demo
```

**Завдання 2** (аудит HTTP-заголовків):

```bash
python -m labs.lab02.main analyze \
    --headers-file labs/lab02/data/data_v09/headers.json \
    --output-csv labs/lab02/data/report.csv
```

З додатковими параметрами:

```bash
python -m labs.lab02.main analyze \
    --headers-file labs/lab02/data/data_v09/headers.json \
    --output-csv labs/lab02/data/report.csv \
    --strict --log-level DEBUG
```

## Як працює Завдання 2

1. Програма читає JSON-файл із HTTP-заголовками відповідей різних ресурсів
   (`pathlib` + `json`).
2. Для кожного ресурсу перевіряє наявність чотирьох заголовків безпеки:
   `Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`,
   `X-Content-Type-Options`. Кожен відсутній заголовок знімає бали і
   записується в лог через `logging.warning`.
3. Регулярним виразом (`re`) шукає витік версій ПЗ у заголовках `Server` та
   `X-Powered-By` (наприклад, `Apache/2.4.41`, `PHP/7.4.3`). Кожен витік
   знімає 10 балів.
4. Рахує Score: старт зі 100 балів, мінус штрафи (мінімум 0).
   Штрафи: HSTS −25, CSP −25, X-Frame-Options −15, X-Content-Type-Options −15,
   витік версії −10. З прапорцем `--strict` додатково −5 за кожну проблему.
5. Визначає оцінку (≥95 A+, ≥85 A, ≥75 B, ≥60 C, ≥45 D, інакше F) і статус
   (≥80 PASS, 50–79 WARN, <50 FAIL).
6. Виводить таблицю та список витоків у консоль і зберігає результат у CSV
   (`csv`): resource, score, grade, status, missing_headers, leaks.

## Параметри `analyze`

| Параметр | Обов'язковий | Опис |
|---|---|---|
| `--headers-file` | так | шлях до вхідного JSON (`labs/lab02/data/data_v09/headers.json`) |
| `--output-csv` | так | шлях до вихідного CSV (`labs/lab02/data/report.csv`) |
| `--strict` | ні | прапорець: додатковий штраф −5 за кожну проблему |
| `--log-level` | ні | DEBUG / INFO / WARNING / ERROR / CRITICAL (типово INFO) |

## Поведінка при помилках

Програма не падає з traceback, а пише повідомлення через `logging.error` і
завершується з кодом 1, якщо:

- файл `--headers-file` не знайдено;
- JSON некоректний або має неочікувану структуру;
- не вдалося записати CSV (немає прав, шлях недоступний).

## Перевірка коду

```bash
ruff check .
ruff format --check .
```