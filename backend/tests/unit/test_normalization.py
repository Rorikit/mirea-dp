from app.services.normalization import (
    GROUP_RE,
    normalize_group,
    normalize_institute,
    normalize_name,
)


def test_name_normalization_preserves_order_and_normalizes_yo() -> None:
    assert normalize_name("  Сёмин   Пётр Иванович  ") == "семин петр иванович"


def test_group_normalization() -> None:
    assert normalize_group(" икбо-11-26 ") == "ИКБО-11-26"
    assert GROUP_RE.fullmatch("ИКБО-11-26")


def test_institute_normalization_keeps_original_separate() -> None:
    original = "ИТХТ имени М.В. Ломоносова"
    assert normalize_institute(original) == "итхт имени м.в. ломоносова"
    assert original == "ИТХТ имени М.В. Ломоносова"
