# Стратегия тестирования

## Уровни

- Unit: normalization, state machines, permissions, metric definitions, formula escaping.
- Integration/PostgreSQL: constraints, migrations, transactions, row locks, rollback, timezone.
- API contract: schemas/status/error envelope/auth/scope/idempotency/rate limits.
- Frontend: components, accessibility, query error/offline/loading states, scanner adapter.
- E2E: student registration→entry→exit→re-entry; import preview→confirm; staff auth; map/schedule.
- Mobile: iOS Safari/Android Chrome, camera deny/grant, bright/dark, one hand, slow/offline network.
- Load: lookup, 50 RPS scan peak, 100 polling admins/operators, 50k import/export.
- Security: OWASP cases, CSRF/CORS/CSP, authorization matrix, upload bombs, log leakage.

## Обязательная матрица импорта

Покрыть: корректный; пустой; corrupted; без каждой из 4 колонок; extras warning; пустые `id/name/group/institute`; duplicate id (обе строки); spaces/case; полное/краткое institute; разные IDs при одинаковой персоне; update; deactivate+explicit consent; cancel; apply failure+rollback; duplicate confirm; formula; 20 MiB/50k boundaries; ZIP bomb; две параллельные confirm. Проверять raw и normalized, counters, status и отсутствие частичного update.

## QR/concurrency

Первый ENTRY, EXIT, повторный ENTRY; old/USED/REVOKED/EXPIRED; два конкурентных scan; retry одного HTTP request; wrong purpose; presence mismatch; неизвестный токен. Инвариант: один USED QR — не более одного AttendanceEvent; проигравшая транзакция создаёт контролируемый ScanAttempt.

Definition of Done: migrations up/down на чистой БД, backend ≥80% branch для domain/import/attendance (цель, не замена качеству), frontend critical flows, no high security findings, load targets, restore rehearsal и traceability FR→tests.

