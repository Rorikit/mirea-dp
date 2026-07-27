import time
from collections import defaultdict, deque

from app.exceptions import AppError

_attempts: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    if limit <= 0:
        return
    now = time.monotonic()
    bucket = _attempts[key]
    while bucket and bucket[0] <= now - window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise AppError("RATE_LIMITED", "Слишком много запросов. Повторите позже", 429)
    bucket.append(now)
