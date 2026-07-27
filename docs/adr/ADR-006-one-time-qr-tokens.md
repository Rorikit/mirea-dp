# ADR-006: Одноразовые QR-токены

- Статус: принято
- Решение: случайный 256-bit bearer token, QR URL без ПДн, HMAC-SHA-256 hash в БД, TTL 15 минут, purpose ENTRY/EXIT, statuses ACTIVE/USED/REVOKED/EXPIRED; один ACTIVE на registration.
- После ENTRY создаётся EXIT автоматически; после EXIT новый ENTRY запрашивает студент. Это сокращает время существования ненужного bearer credential.
- Альтернативы: подписанный QR с данными и переиспользуемый QR отклонены из-за утечки/replay.

