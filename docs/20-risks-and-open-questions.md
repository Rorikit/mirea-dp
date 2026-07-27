# Риски и открытые вопросы

| Риск | P/I | Мера / владелец |
|---|---|---|
| Неполный Excel деактивирует студентов | M/H | anomaly threshold, explicit preview/phrase; владелец данных |
| Дубли ФИО+группы блокируют регистрацию | M/M | админ-resolution workflow до события; организатор |
| QR передан другому человеку | H/M | short TTL и визуальная сверка; безопасность |
| Плохая связь/камера | H/H | manual code, retry same key, rehearsal; эксплуатация |
| Пиковая нагрузка выше допущения | M/H | подтвердить профиль, load test, capacity buffer; архитектор |
| Неопределённое основание/retention ПДн | M/H | legal decision до production; заказчик/DPO |
| Browser BarcodeDetector несовместим | M/M | adapter с ZXing fallback; frontend |
| Ошибка времени | L/H | NTP/alert/server authoritative; DevOps |
| Один сервер — SPOF | M/H | backup/restore/spare host; решение после SLA |
| Admin account compromise | M/H | MFA/re-auth/least privilege; security |

## Решения, требующие ответа до реализации

Юридическая модель ПДн/retention; SLA/RPO/RTO и capacity; глобальность source ID; утверждение `ё→е` и group regex; режим нескольких КПП/offline; политика ручных overrides; admin MFA; официальный брендбук/карта; срок хранения original Excel/ScanAttempt; допустимый объём operator-visible ПДн.

До ответа применяются явно помеченные допущения из [обзора](01-project-overview.md), но production launch заблокирован для юридических, SLA и security-вопросов.

