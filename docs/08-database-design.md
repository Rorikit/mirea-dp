# Проектирование базы данных

Все PK — UUIDv7 (на уровне приложения до штатной поддержки БД), timestamps — `timestamptz`, enum — PostgreSQL enum либо CHECK с миграцией. Строки ограничены по длине. `source_id varchar(128)` сохраняет ведущие нули и будущие префиксы.

```mermaid
erDiagram
  EVENT ||--o{ SOURCE_STUDENT : contains
  EVENT ||--o{ IMPORT_BATCH : receives
  IMPORT_BATCH ||--o{ IMPORT_ROW : stages
  IMPORT_ROW ||--o{ IMPORT_ROW_ERROR : has
  SOURCE_STUDENT ||--o| REGISTRATION : registers
  REGISTRATION ||--o{ QR_TOKEN : owns
  REGISTRATION ||--o{ ATTENDANCE_EVENT : history
  QR_TOKEN ||--o{ SCAN_ATTEMPT : attempted
  USER ||--o{ USER_SESSION : sessions
  USER ||--o{ ATTENDANCE_EVENT : operates
  USER ||--o{ AUDIT_LOG : acts
  EVENT ||--o{ SCHEDULE_ITEM : schedules
  EVENT ||--o{ MAP_ASSET : maps
  MAP_ASSET ||--o{ MAP_ZONE : zones
  EVENT {
    uuid id PK
    varchar slug UK
    varchar name
    timestamptz starts_at
    timestamptz ends_at
    varchar timezone
    enum status
    boolean registration_enabled
    boolean scanning_enabled
  }
  SOURCE_STUDENT {
    uuid id PK
    uuid event_id FK
    varchar source_id
    varchar full_name
    varchar normalized_full_name
    varchar study_group
    varchar normalized_study_group
    varchar institute
    varchar normalized_institute
    boolean is_active
  }
  REGISTRATION {
    uuid id PK
    uuid source_student_id FK
    uuid public_id UK
    enum presence_status
    timestamptz revoked_at
  }
  QR_TOKEN {
    uuid id PK
    uuid registration_id FK
    char token_hash UK
    enum purpose
    enum status
    timestamptz expires_at
  }
  ATTENDANCE_EVENT {
    uuid id PK
    uuid registration_id FK
    uuid qr_token_id FK
    enum event_type
    enum previous_status
    enum new_status
    uuid request_id UK
  }
  SCAN_ATTEMPT {
    uuid id PK
    uuid event_id FK
    uuid operator_id FK
    uuid qr_token_id FK
    varchar idempotency_key
    varchar result_code
    timestamptz occurred_at
  }
```

## Ограничения и индексы

- `source_students UNIQUE(event_id, source_id)` — ключ синхронизации.
- Индекс `(event_id, normalized_full_name, normalized_study_group) WHERE is_active` — регистрационный поиск; институт исключён намеренно.
- `(event_id, normalized_study_group)`, `(event_id, normalized_institute)` — фильтры/группировки. Отдельный `(event_id,is_active)` не нужен при низкой селективности; частичный `WHERE is_active` добавляется после измерений.
- `registrations UNIQUE(event_id, source_student_id)` и CHECK согласованности статуса.
- Частичный unique `qr_tokens(registration_id) WHERE status='ACTIVE'`; unique `token_hash`.
- `attendance_events UNIQUE(qr_token_id)`, `UNIQUE(event_id, request_id)`; индекс `(event_id, occurred_at)`.
- `scan_attempts UNIQUE(operator_id, idempotency_key)`; индекс recent `(operator_id, occurred_at DESC)`.
- `import_rows UNIQUE(import_batch_id,row_number)`; batch `(event_id,created_at DESC)`.
- Нормализованные институты остаются строками: отдельный справочник преждевременен без утверждённого mapping. `StudyGroup` также не выделяется; это атрибут снимка источника.

Удаление предметных данных запрещено обычным API. SourceStudent деактивируется; Registration отзывается; Event архивируется. Изменение imported полей возможно импортом, ручной PATCH пишет AuditLog и метку override (требует уточнения политики следующего импорта).

## Состояния

```mermaid
stateDiagram-v2
  [*] --> OUTSIDE
  OUTSIDE --> INSIDE: успешный ENTRY
  INSIDE --> OUTSIDE: успешный EXIT
  OUTSIDE --> OUTSIDE: неуспешный scan / QR refresh
  INSIDE --> INSIDE: неуспешный scan
```

