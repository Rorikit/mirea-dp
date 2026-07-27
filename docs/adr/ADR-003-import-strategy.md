# ADR-003: Стратегия импорта

- Статус: принято
- Решение: staged full sync (вариант C): upload→validate→preview→explicit confirm→single transaction. CREATE/UPDATE/UNCHANGED/DEACTIVATE; physical delete запрещён.
- Deactivate требует отдельного согласия и контрольной фразы при аномальном количестве; ERROR блокирует, WARNING требует acknowledgement.
- Альтернативы A/B безопаснее неполного файла, но оставляют устаревшие записи активными. Риск C компенсируется preview/version/lock.
- Последствие: хранение ImportBatch/Row/Error и preview snapshot; повтор confirm идемпотентен.

