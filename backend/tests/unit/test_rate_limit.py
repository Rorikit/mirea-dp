from app.services.rate_limit import enforce_rate_limit


def test_zero_limit_disables_rate_limiting() -> None:
    for _ in range(100):
        enforce_rate_limit("test:disabled", 0, 60)
