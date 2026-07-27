# ADR-008: Аутентификация

- Статус: принято с открытым вопросом MFA
- Решение staff: Argon2id password, short access token в памяти, rotating refresh session в HttpOnly Secure SameSite=Strict cookie, CSRF/Origin protection, revoke family. Student: отдельная opaque HttpOnly cookie, scoped к registration.
- RBAC и event/object scope проверяет backend. Административные опасные действия требуют re-auth; MFA рекомендуется до production.
- Альтернативы localStorage JWT отклонены из-за XSS; полностью server-side cookie session допустима и может заменить hybrid после инфраструктурного выбора.

