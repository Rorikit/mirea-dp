# Обработка ошибок

```json
{
  "error": {
    "code": "IMPORT_SOURCE_ID_DUPLICATE",
    "message": "В файле обнаружены повторяющиеся идентификаторы студентов",
    "details": {"source_id": "105", "rows": [12, 48]},
    "request_id": "018f..."
  }
}
```

`code` стабилен, `message` безопасен и локализуем, `details` имеет allowlist. Stack trace, SQL, секрет, hash QR и внутреннее исключение наружу не выходят. Validation errors приводятся к этому же envelope.

Ключевые коды: `VALIDATION_ERROR`, `AUTH_REQUIRED`, `FORBIDDEN`, `RATE_LIMITED`, `RESOURCE_NOT_FOUND`, `STATE_CONFLICT`, `IDEMPOTENCY_CONFLICT`, `REGISTRATION_NOT_FOUND_OR_AMBIGUOUS`, `QR_INVALID`, `QR_EXPIRED`, `QR_ALREADY_USED`, `QR_REVOKED`, `PRESENCE_STATE_MISMATCH`, `IMPORT_*`, `IMPORT_PREVIEW_STALE`, `IMPORT_HAS_ERRORS`, `EVENT_REGISTRATION_DISABLED`, `EVENT_SCANNING_DISABLED`.

4xx логируется INFO/WARN без ПДн; 5xx ERROR с internal exception и request_id в защищённом sink. Клиент показывает retry только для network/408/429/5xx; повтор мутаций сохраняет Idempotency-Key. `Retry-After` обязателен для 429/503.

