# ADR-010: Обновление статистики

- Статус: принято
- Решение: polling 10 секунд, точные SQL queries с `as_of`; индексы прежде preaggregation.
- WebSocket отклонён: нет требования sub-second, усложняет proxy/reconnect/authorization. Materialized aggregates вводятся после профилирования.

