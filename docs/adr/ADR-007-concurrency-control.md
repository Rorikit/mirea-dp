# ADR-007: Конкурентность и идемпотентность

- Статус: принято
- Решение: PostgreSQL transaction; QR row `FOR UPDATE`, затем Registration row в постоянном порядке; unique qr attendance; staff idempotency key с fingerprint и сохранённым response.
- Второй параллельный scan после ожидания видит USED и получает `QR_ALREADY_USED`; второго события нет. Confirm import сериализуется lock batch + event-level import lock/version.
- Альтернативы optimistic-only и distributed lock отклонены: pessimistic row lock проще и надёжнее для короткой критической секции.

