# Проектирование API v1

JSON, UTF-8, UTC ISO-8601. UUID наружу — только public/request IDs. Персональные списки пагинируются cursor. Мутации принимают `Idempotency-Key`; ответы содержат `X-Request-ID`. Ограничения ниже — стартовые per IP или authenticated principal, уточняются нагрузочным тестом.

## Общие схемы

`Error={error:{code,message,details,request_id}}`. `Page={items,next_cursor}`. Ошибки: 400 validation, 401 unauthenticated, 403 forbidden, 404 not found (также для чужого объекта), 409 state/idempotency conflict, 413 size, 415 media, 422 semantic error, 429 rate, 500 generic.

## Endpoints

| Endpoint | Назначение и роль | Request → Response | Коды / идемпотентность / limit / транзакция |
|---|---|---|---|
| `POST /public/registrations/lookup` | Однозначный поиск, public | `{event_slug,full_name,study_group}` → `{match:"FOUND",lookup_token,expires_at}` либо общий `NOT_FOUND_OR_AMBIGUOUS` | 200/404/422/429; no; 5/min/IP+fingerprint; read-only |
| `POST /public/registrations` | Регистрация, public | `{lookup_token}` → `{registration,qr}` + cookie | 200/201/409/429; key required; 3/min; Registration+QR atomic |
| `GET /public/registrations/me` | Свой кабинет, student cookie | — → `{profile,presence_status,active_qr?}` | 200/401/410; safe; 60/min; read |
| `POST /public/registrations/me/qr` | Новый допустимый QR | `{purpose:"ENTRY"}` → `{qr,expires_at}` | 201/409/429; key; 10/h; revoke expired+create atomic |
| `GET /public/schedule` | Published schedule | `event_slug` → `{server_time,timezone,items}` | 200/404; safe/cache 30s; 60/min; read |
| `GET /public/map` | Active map metadata | `event_slug` → `{url,width,height,sha256}` | 200/404; safe/cache; 60/min; read |
| `POST /auth/login` | Staff login | `{username,password}` → `{access_token,expires_in,user}` + refresh cookie | 200/401/429; no; 5/15min; session+audit |
| `POST /auth/refresh` | Rotation | cookie → new token/cookie | 200/401/409; one-time family; 30/h; rotate atomic |
| `POST /auth/logout` | Revoke session | cookie → 204 | idempotent; 30/h; revoke atomic |
| `GET /auth/me` | Current staff | — → `{id,username,role,event_ids}` | 200/401; safe; 120/min; read |
| `POST /operator/scans` | Scan transition, operator/admin | `{token,device_info}` + key → `{result,student,transition,occurred_at}` | 200/400/401/403/409/410/429; key required; 120/min; locks token+registration, event+next QR atomic |
| `GET /operator/scans/recent` | Own attempts | `cursor,limit<=50` → Page | 200/401/403; safe; 60/min; read |
| `POST /admin/imports` | Upload/validate, admin multipart | file,event_id → ImportBatch | 201/413/415/422/429; file hash dedupe advisory; 5/h; staging transaction |
| `GET /admin/imports/{id}` | Batch | — → batch counters/status | 200/404; safe; 60/min; read |
| `GET /admin/imports/{id}/preview` | Preview | cursor/filter → actions/errors + version | 200/409; safe; 60/min; read snapshot |
| `POST /admin/imports/{id}/confirm` | Apply | `{preview_version,accept_warnings,confirm_deactivations,phrase?}` | 200/409/422; key required; 5/h; one serializable/locked transaction |
| `POST /admin/imports/{id}/cancel` | Cancel uncommitted | `{reason}` → batch | 200/409; idempotent; 10/h; lock batch |
| `GET /admin/imports/{id}/errors.xlsx` | Error report | — → attachment | 200/404/409; safe; 10/h; read, formula-safe |
| `GET /admin/students` | Filtered list | query/cursor → Page | 200/422; safe; 120/min; read |
| `GET /admin/students/{id}` | Detail | — → student+registration summary | 200/404; safe; 120/min; read |
| `PATCH /admin/students/{id}` | Active/manual correction | `{is_active?,...}` + `If-Match` → resource | 200/409/422; key; 30/h; update+audit+QR revoke atomic |
| `GET /admin/statistics/summary` | Exact dashboard | filters → counters+as_of | 200/422; safe; 30/min; repeatable read |
| `GET /admin/statistics/traffic` | Time buckets | from,to,bucket → series | 200/422; safe; 30/min; read |
| `GET /admin/statistics/institutes` | Grouping | filters → rows | 200/422; safe; 30/min; read |
| `GET /admin/statistics/groups` | Grouping | filters → rows | 200/422; safe; 30/min; read |
| `GET /admin/exports/attendance.xlsx` | Export | filters → attachment | 200/422/429; safe; 5/h; consistent read snapshot |

Префикс всех строк: `/api/v1`. Для upload ответ может быть 201 только после синхронной validation до лимита 50k; при превышении будущего SLA API переходит на 202 + DB worker без изменения контракта status.

## Дополнения реализации

Для рабочих административных экранов добавлены контракты, отсутствовавшие в первоначальном перечне:

- `GET /public/events/{event_slug}` — публичная метаинформация мероприятия;
- `GET/POST/PATCH/DELETE /admin/schedule` — управление расписанием;
- `POST /admin/map` и `GET /public/map/{asset_id}/file` — публикация и выдача карты;
- `GET/POST/PATCH /admin/users` — управление операторами;
- `POST /admin/events/{event_id}/archive` — защищённое архивирование вместо удаления.

Все административные мутации требуют `ADMIN`, проходят серверную валидацию и пишут `AuditLog`.
