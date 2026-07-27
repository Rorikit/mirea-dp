# Архитектура системы

## Контекст

```mermaid
flowchart LR
  S[Студент] -->|HTTPS| SYS[Freshman Day Web System]
  O[Оператор] -->|HTTPS, камера| SYS
  A[Администратор] -->|HTTPS, XLSX| SYS
  SYS -->|SQL/TLS во внутренней сети| DB[(PostgreSQL)]
  SYS -->|резервные копии| B[(Backup storage)]
```

## Контейнеры

```mermaid
flowchart TB
  N[Nginx: TLS, headers, static, proxy]
  F[React + TypeScript SPA]
  B[FastAPI modular monolith]
  D[(PostgreSQL)]
  V[(Persistent uploads/maps)]
  U[Student/Operator/Admin] --> N
  N --> F
  N -->|/api| B
  B --> D
  B --> V
```

В production frontend собирается в статические файлы. Backend stateless кроме БД/файлов; горизонтальное масштабирование возможно позднее. Загруженные оригиналы Excel по умолчанию удаляются после установленного срока, staging-данные остаются согласно политике.

## Модули backend

```mermaid
flowchart LR
  API[HTTP adapters] --> AUTH[Auth/RBAC]
  API --> REG[Registration]
  API --> IMP[Import]
  API --> ATT[QR & Attendance]
  API --> CONTENT[Schedule & Map]
  API --> REPORT[Statistics & Export]
  AUTH --> AUDIT[Audit]
  REG --> CORE[Event & Students]
  IMP --> CORE
  ATT --> REG
  REPORT --> ATT
  CONTENT --> CORE
  CORE --> DB[(SQLAlchemy Unit of Work)]
  AUDIT --> DB
```

Модуль владеет моделями и сервисами; связи идут через application interfaces — прикладные интерфейсы. API → application → domain → infrastructure. Транзакция задаётся use case — прикладным сценарием, не репозиторием.

## Технологические решения

FastAPI/SQLAlchemy 2/Alembic/PostgreSQL и React/Vite/TanStack Query соответствуют команде и нагрузке. Добавляются только `openpyxl` в read-only режиме с защитой ZIP, библиотека QR-кодирования, `argon2id` для паролей и структурированные логи. Redis/Kafka/Kubernetes/WebSocket не нужны: фоновые задачи импорта допустимы в процессе при одном экземпляре MVP; перед масштабированием нужен DB-backed worker.

