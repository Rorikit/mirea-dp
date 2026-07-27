# Развёртывание

Production: Nginx (единственная публичная точка) → статический frontend и FastAPI; PostgreSQL/volume находятся в закрытой Docker network. Compose подходит одному серверу MVP. TLS от утверждённого CA, HSTS после проверки. Secrets не в image/репозитории; `.env.example` содержит только имена.

Pipeline: lint/type/test → build pinned images → vulnerability scan/SBOM → backup → Alembic migrate (backward-compatible) → deploy → readiness/smoke → ручное разрешение трафика. Rollback приложения не откатывает destructive migration; schema changes expand/contract.

Перед мероприятием: capacity test, импорт финальной копии, restore drill, NTP, TLS expiry, операторские устройства, запасной интернет/зарядки, runbook и ответственные. Бэкапы: ежедневный full + WAL/PITR 15 мин, encrypted off-host, проверка восстановления. RPO 15 мин/RTO 60 мин.

Dev compose — skeleton only; настоящий production config, certificates, backup jobs и hardening будут отдельной задачей после ответов на open questions.

