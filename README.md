# День первокурсника РТУ МИРЭА 2026

Рабочее mobile-first веб-приложение мероприятия 1 сентября 2026 года: импорт списка студентов, безопасная регистрация, одноразовые QR, контроль входов/выходов, операторский сканер, расписание, карта, статистика, экспорт и аудит.

## Архитектура

Модульный монолит: React SPA → Nginx → async FastAPI → PostgreSQL. `source_id` из Excel отделён от внутреннего UUID. QR не содержит ПДн, в БД хранится HMAC-хеш. Сканирование использует PostgreSQL row lock — блокировку строки — и идемпотентность. Решения описаны в [docs](docs/README.md) и [ADR](docs/adr/).

## Требования

- Docker Desktop/Engine с Compose;
- для локальной разработки без Docker: Python 3.12+, Node.js 24+, PostgreSQL 17;
- HTTPS и камера требуют secure context — защищённого контекста — кроме `localhost`.

## Быстрый запуск через Docker

1. Скопировать `.env.example` в `.env` и заменить `POSTGRES_PASSWORD`, `APP_SECRET_KEY`, `APP_QR_PEPPER`.
2. Выполнить `make up` или `docker compose up --build -d`.
3. Применить миграции: `make migrate`.
4. Создать мероприятие: `docker compose run --rm backend python -m app.scripts.create_event`.
5. Создать администратора: `docker compose run --rm backend python -m app.scripts.create_admin`.
   Если Windows Terminal повреждает интерактивный ввод Docker, передайте
   `ADMIN_USERNAME` и `ADMIN_PASSWORD` через переменные окружения с флагами `-e`.
6. Открыть `http://localhost:8080`; staff login расположен по `/login`.

Пароль администратора вводится интерактивно. Для автоматизации допустимы временные `ADMIN_USERNAME` и `ADMIN_PASSWORD`; секрет не выводится в лог.

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `POSTGRES_*` | База, пользователь и пароль PostgreSQL |
| `APP_DATABASE_URL` | Async SQLAlchemy URL |
| `APP_SECRET_KEY` | Подпись access/lookup и HMAC сессий |
| `APP_QR_PEPPER` | Независимый HMAC-secret QR |
| `APP_CORS_ORIGINS` | Точный список допустимых origins |
| `APP_SECURE_COOKIES` | `true` только при HTTPS |
| `APP_UPLOAD_DIR` | Persistent-каталог карты/import assets |
| `VITE_API_BASE` | API base frontend, по умолчанию `/api/v1` |
| `VITE_EVENT_SLUG` | `freshman-day-2026` по умолчанию |

Production-секреты должны приходить из secret manager или защищённого environment-файла, не из репозитория.

## Локальная разработка

Backend: `pip install -e ".[dev]"`, задать `APP_DATABASE_URL`, затем `uvicorn app.main:app --reload` из `backend/`. Frontend: `npm ci && npm run dev` из `frontend/`.

Команды Makefile: `dev/up/down`, `test`, `lint`, `format`, `migrate`, `revision m="описание"`, `frontend-test`.

В локальном Compose ограничение попыток входа отключено через
`APP_LOGIN_RATE_LIMIT=0`. Положительное значение включает лимит обратно;
production должен использовать значение не меньше `5`.

## Миграции

- Применение: `docker compose run --rm backend alembic upgrade head`.
- Новая: `make revision m="add field"`.
- Проверка: `alembic check` и цикл upgrade/downgrade на тестовой БД.

Схема production не изменяется автоматически при старте контейнера.

## Импорт XLSX

Войти как ADMIN → «Импорт студентов» → выбрать `.xlsx` с `id,name,group,institute` → проверить preview → явно принять warnings/deactivations → подтвердить. Файл ограничен 20 МиБ и 50 000 строками; формулы, повреждённый ZIP/XLSX и ZIP bomb отклоняются. Изменения применяются одной транзакцией.

## Тестирование и качество

- Backend: `docker build --target test -t freshman-day-backend-test backend` и `docker run --rm freshman-day-backend-test pytest -q`.
- Backend lint/type: Ruff + Mypy.
- Frontend: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`.
- Mobile E2E: `npx playwright install chromium webkit`, затем `npm run test:e2e`.
- Docker: `docker compose build backend frontend`.

CI выполняет lint, format check, type check, tests, migration check, frontend build и Docker build без production-секретов.

## Резервное копирование и восстановление

Backup: `docker compose exec -T db pg_dump -U freshman -Fc freshman > freshman.dump`. Карты копируются отдельно из volume `uploads`. Restore выполняется в остановленный новый контур: создать пустую БД, затем `pg_restore --clean --if-exists -U freshman -d freshman freshman.dump`. Команды восстановления сначала проверяются на rehearsal-контуре; RPO/RTO утверждаются владельцем системы.

## Production

Подготовить TLS-файлы `fullchain.pem` и `privkey.pem`, задать `TLS_DIR`, production secrets и HTTPS origin. Запуск: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`. Конфигурация использует статический frontend, непривилегированных пользователей контейнеров, healthchecks, persistent PostgreSQL/uploads volumes и TLS 1.2/1.3.

## Известные ограничения MVP

- Rate limit хранится в памяти процесса и рассчитан на один backend worker; для нескольких workers нужен PostgreSQL-backed limiter либо обоснованный Redis. Production Docker временно должен использовать один worker до этого изменения.
- Нет офлайн-синхронизации сканов, MFA, интерактивной GIS-карты, SSO и интеграций университета.
- Карту необходимо проверить на реальных мобильных устройствах; torch на iOS не гарантирован.
- Для preview больших файлов validation выполняется в request worker; после нагрузочных тестов допускается DB-backed worker без брокера.
- Юридические сроки хранения ПДн и оригиналов импортов должны быть утверждены до production.
