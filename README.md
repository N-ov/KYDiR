# KYDiR — общий семейный бюджет

Самостоятельно хостящийся трекер семейных финансов: траты и доходы вносят все члены семьи в один общий бюджет, аналитика — по категориям, по людям и по месяцам.

## Стек

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite (вся база — один файл, бэкап = копия файла)
- **Frontend:** статика в `frontend/` (SPA без сборки), раздаётся этим же приложением
- **Авторизация:** cookie-сессии; открытой регистрации нет, членов семьи добавляем сами

## Быстрый старт

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; на Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py init-db
python manage.py seed-categories
python manage.py add-user --username papa --name "Папа" --color "#4f8ef7"

uvicorn app.main:app --reload
```

- Приложение: http://localhost:8000/
- API: http://localhost:8000/api
- Документация API (Swagger): http://localhost:8000/api/docs

## Структура

```
app/
  main.py          # приложение FastAPI, CORS, раздача статики
  config.py        # настройки (переопределяются env-переменными KYDIR_*)
  database.py      # engine SQLite, сессии
  models.py        # User, Category, Transaction, AuthSession
  schemas.py       # Pydantic-схемы
  routers/         # auth, users, categories, transactions, analytics
manage.py          # CLI: init-db, add-user, seed-categories
frontend/          # статический фронтенд (SPA)
FRONTEND_PROMPT.md # промпт для генерации фронтенда
```

## Настройки (env)

| Переменная | По умолчанию | Что делает |
|---|---|---|
| `KYDIR_DB` | `./data/kydir.db` | путь к файлу базы |
| `KYDIR_SESSION_TTL_DAYS` | `30` | срок жизни сессии |
| `KYDIR_COOKIE_SECURE` | `0` | `1` на VPS за HTTPS |

## Деталь реализации

Суммы хранятся в копейках (integer), наружу API отдаёт рубли — без ошибок округления float.
