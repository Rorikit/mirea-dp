# План реализации MVP

1. **Утверждение архитектуры (текущий gate).** Ответить на открытые вопросы, threat/privacy review, согласовать API/schema/UX и acceptance criteria.
2. **Platform foundation.** CI, environments/secrets, DB/Alembic, observability, Event/Auth/RBAC, frontend design system. Выход: защищённый login и health.
3. **Импорт и студенты.** Safe XLSX parser, staging/preview/report/atomic confirm, admin UI, тестовая матрица. Выход: проверенный финальный список без ручного SQL.
4. **Регистрация и QR.** Student session, exact matching, token lifecycle, scanner, concurrency/idempotency. Выход: end-to-end ENTRY/EXIT и нагрузочные тесты.
5. **Контент и отчёты.** Map/schedule, statistics polling, safe export, audit UI.
6. **Hardening.** Security/accessibility/mobile/load/backup restore, runbooks, operator training, dry run.
7. **Launch and archive.** Change freeze, final import, monitoring, incident response, post-event archive/export/retention.

Не переходить к полной бизнес-разработке до formal sign-off шага 1. Созданный рядом каркас демонстрирует только структуру и `/health`.

