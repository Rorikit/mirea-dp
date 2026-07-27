# Пользовательские сценарии

## Регистрация

```mermaid
sequenceDiagram
  actor S as Студент
  participant UI as Web UI
  participant API
  participant DB as PostgreSQL
  S->>UI: ФИО и группа
  UI->>API: lookup
  API->>DB: точный нормализованный поиск active
  DB-->>API: 0 / 1 / несколько
  API-->>UI: opaque lookup_token или общая ошибка
  S->>UI: Подтвердить
  UI->>API: registrations + Idempotency-Key
  API->>DB: создать/вернуть Registration и ENTRY QR
  API-->>UI: student session + профиль + QR
```

`lookup_token` — краткоживущий подписанный непрозрачный результат однозначного поиска; клиент не получает ID до регистрации. При 0/нескольких совпадениях одинаковый по форме ответ и rate limit.

## Импорт и подтверждение

```mermaid
sequenceDiagram
  actor A as Администратор
  participant API
  participant V as Import module
  participant DB
  A->>API: POST файл
  API->>V: безопасное чтение и validation
  V->>DB: сохранить batch/rows/errors
  API-->>A: preview
  A->>API: confirm + version + acknowledgements
  API->>DB: BEGIN, lock batch/event
  DB-->>API: применить CREATE/UPDATE/DEACTIVATE
  API->>DB: status APPLIED, audit, COMMIT
  API-->>A: итог
```

```mermaid
sequenceDiagram
  actor A as Администратор
  participant API
  participant DB
  A->>API: confirm(import_id, preview_version)
  API->>DB: SELECT batch FOR UPDATE
  alt READY и версия актуальна
    API->>DB: применить всё одной транзакцией
    API->>DB: APPLIED + AuditLog
    DB-->>API: COMMIT
  else уже APPLIED
    DB-->>API: тот же итог (идемпотентно)
  else конфликт/ошибка
    DB-->>API: ROLLBACK; FAILED/409
  end
```

## Вход, выход и гонка

```mermaid
sequenceDiagram
  actor O as Оператор
  participant API
  participant DB
  O->>API: scan ENTRY + Idempotency-Key
  API->>DB: BEGIN; token FOR UPDATE; registration FOR UPDATE
  API->>DB: Attendance ENTRY, INSIDE, token USED, новый EXIT
  DB-->>API: COMMIT
  API-->>O: Вход разрешён
```

```mermaid
sequenceDiagram
  actor O as Оператор
  participant API
  participant DB
  O->>API: scan EXIT
  API->>DB: locks + validate INSIDE
  API->>DB: Attendance EXIT, OUTSIDE, token USED
  DB-->>API: COMMIT
  API-->>O: Выход зарегистрирован
  Note over API: Новый ENTRY выдаётся студенту по кнопке
```

```mermaid
sequenceDiagram
  participant O1 as Оператор 1
  participant O2 as Оператор 2
  participant API
  participant DB
  par одновременно
    O1->>API: scan token
    O2->>API: scan token
  end
  API->>DB: Tx1 lock token
  API->>DB: Tx2 ждёт lock
  DB-->>API: Tx1 commit USED
  API->>DB: Tx2 читает USED
  API-->>O1: success
  API-->>O2: QR_ALREADY_USED
```

Другие сценарии: камера запрещена → ручной ввод; сеть пропала до ответа → повтор с тем же `Idempotency-Key`; импорт с ERROR → скачать отчёт; WARNING → явный checkbox; событие архивировано → регистрация и scanning закрыты.

