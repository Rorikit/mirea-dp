from app.security.crypto import hash_password, token_hash, verify_password


def test_password_hash_is_not_plaintext() -> None:
    password = "Сложный пароль 2026!"
    hashed = hash_password(password)
    assert password not in hashed
    assert verify_password(hashed, password)
    assert not verify_password(hashed, "неверный пароль")


def test_token_hash_is_deterministic_and_does_not_contain_token() -> None:
    raw = "секретный-токен"
    hashed = token_hash(raw, "pepper")
    assert hashed == token_hash(raw, "pepper")
    assert raw not in hashed
