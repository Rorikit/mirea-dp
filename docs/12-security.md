# Безопасность и модель угроз

| Угроза | Вероятность / ущерб | Защита | MVP |
|---|---|---|:---:|
| Перебор ФИО/групп, чужой кабинет | средняя / высокий | общий ответ 404, rate limit, краткий lookup token, student HttpOnly session, отсутствие списков совпадений | ✓ |
| Передача/скриншот QR | высокая / средний | 15 мин, одноразовый, purpose/status, визуальная сверка оператором, revoke | ✓ |
| Подделка/повтор QR/HTTP | средняя / высокий | 256-bit token, HMAC hash, TLS, row locks, unique, idempotency | ✓ |
| Конкурентное сканирование | средняя / высокий | транзакция и `FOR UPDATE`, unique qr attendance | ✓ |
| Обход staff routes | средняя / высокий | backend RBAC + event scope; deny by default | ✓ |
| Подбор пароля | средняя / высокий | Argon2id, ≥12 символов, rate/lockout, admin MFA желательно | частично; MFA open |
| Кража сессии | средняя / высокий | short access, rotating HttpOnly refresh, Secure/SameSite, revoke family, CSP | ✓ |
| CSRF | средняя / высокий | SameSite Strict + CSRF token для cookie-auth mutating запросов; Origin check | ✓ |
| XSS | средняя / высокий | React escaping, без raw HTML, CSP nonce, safe filenames/content | ✓ |
| SQL injection | низкая / высокий | SQLAlchemy parameters, allowlist sort/filter | ✓ |
| CORS ошибка | средняя / высокий | точный allowlist origin, no wildcard credentials | ✓ |
| Вредоносный/повреждённый XLSX, ZIP bomb | средняя / высокий | size/entry/ratio limits, signatures, no macros/links, read-only, timeout | ✓ |
| Excel formula injection | средняя / высокий | reject import formulas; exported cells escaped/type string | ✓ |
| Вредоносная карта | средняя / высокий | только decoded/re-encoded PNG/WebP, лимиты dimensions/bytes, отдельный origin/no SVG | ✓ |
| Утечка ПДн/токенов в логах | средняя / высокий | field allowlist/redaction, token never logged, RBAC/export audit/encryption backups | ✓ |
| Опасная admin операция | средняя / критический | re-auth, phrase, preview, audit; archive not delete | ✓ |
| Нет HTTPS | средняя / критический | redirect/HSTS, TLS 1.2+, secure cookies; backend не публикуется | ✓ |
| Потеря БД | низкая / критический | encrypted backup, PITR, restore drill, off-host copy | ✓ |
| Неверное время | средняя / высокий | NTP, UTC DB, drift alert, server time authoritative | ✓ |

Дополнительно: секреты только environment/secret store, отдельный DB user без superuser, миграции отдельной ролью, security headers (`CSP`, `HSTS`, `X-Content-Type-Options`, `Referrer-Policy: no-referrer`, frame deny), dependency pinning/scanning. ПДн не помещаются в URL. Аудит append-only для входов, импортов, ручных изменений, экспорта и архивирования.

