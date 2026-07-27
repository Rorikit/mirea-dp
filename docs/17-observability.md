# Наблюдаемость

Структурированные JSON-логи: timestamp UTC, level, service/version, request_id, route template, status, duration, actor_id (pseudonymous), role, event_id, error_code. Не логируются body регистрации/login, QR/token/cookie/password, полные ФИО и XLSX rows.

Метрики: request rate/error/latency; DB pool/locks/deadlocks; scan success/error и transaction latency; imports by status/duration/rows; active sessions; backup age; disk. Alerts: scan 5xx >2%/5m, p95 >2s, DB unavailable, import stuck >10m, clock drift >2s, backup >24h, disk >80%.

Health: `/health` — process liveness без деталей; `/ready` — DB/migrations readiness только во внутренней сети. AuditLog — предметный неизменяемый журнал, не заменяет технический лог. Retention и доступ разделяются; request_id связывает UI, API, ScanAttempt, AttendanceEvent и AuditLog.

