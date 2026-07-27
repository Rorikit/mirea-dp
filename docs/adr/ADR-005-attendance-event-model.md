# ADR-005: Модель посещаемости

- Статус: принято
- Решение: Registration хранит materialized current state OUTSIDE/INSIDE; неизменяемый AttendanceEvent хранит только успешные ENTRY/EXIT; ScanAttempt хранит все попытки.
- Инвариант: переход, event, token USED и новый QR совершаются одной транзакцией. История — источник аудита, текущий status — быстрый read model.
- Альтернатива вычислять status только из истории отклонена из-за lock/concurrency и стоимости чтения. ScanAttempt внутри AttendanceEvent невозможен для неуспешных переходов.

