# ЛР №3 — варіант 9: облік часу опрацювання повідомлень про події безпеки

Web API на FastAPI з базою SQLite (без ORM).

- `categories` — джерело повідомлення: `siem`, `helpdesk`, `monitoring`.
- `records.value` — тривалість перевірки в **хвилинах** (`minutes`), число >= 0, скінченне.
- `records.status` — `new`, `in_progress`, `done`.
- Навчальний поріг: **15.0** хв.

## Встановлення і запуск (з кореня репозиторію)

```bash
pip install -r requirements.txt
python -m labs.lab03.seed
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i -X POST "http://127.0.0.1:8000/records" -H "Content-Type: application/json" \
  -d '{"code":"V09-TEST","title":"Навчальне вимірювання","category_id":1,"value":7.5,"status":"new"}'
curl -i -X POST "http://127.0.0.1:8000/records/bulk" -H "Content-Type: application/json" \
  -d '[{"code":"V09-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V09-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
```

Останній запит повертає `409`, `V09-ROLLBACK` не зберігається.

## Перевірка стилю

```bash
ruff check . && ruff format --check .
```