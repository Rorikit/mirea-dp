import io
import zipfile

import pytest
from openpyxl import Workbook

from app.exceptions import AppError
from app.models.enums import ErrorSeverity
from app.services.imports import parse_workbook


def workbook_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def test_valid_file_and_normalization() -> None:
    rows, issues = parse_workbook(
        workbook_bytes(
            ["id", "name", "group", "institute"], [[1, " Иванов  Иван ", " икбо-11-26 ", " ИИИ "]]
        ),
        100,
    )
    assert not issues
    assert rows[0].source_id == "1"
    assert rows[0].normalized_name == "иванов иван"
    assert rows[0].normalized_group == "ИКБО-11-26"


@pytest.mark.parametrize("missing", ["id", "name", "group", "institute"])
def test_required_column_missing(missing: str) -> None:
    headers = [header for header in ["id", "name", "group", "institute"] if header != missing]
    with pytest.raises(AppError, match="обязательные колонки") as caught:
        parse_workbook(workbook_bytes(headers, [["x"] * len(headers)]), 100)
    assert caught.value.code == "IMPORT_REQUIRED_COLUMN_MISSING"


def test_empty_and_corrupted_files() -> None:
    with pytest.raises(AppError) as empty:
        parse_workbook(workbook_bytes(["id", "name", "group", "institute"], []), 100)
    assert empty.value.code == "IMPORT_FILE_EMPTY"
    with pytest.raises(AppError) as corrupted:
        parse_workbook(b"PK\x03\x04broken", 100)
    assert corrupted.value.code == "IMPORT_INVALID_XLSX"


def test_duplicate_id_marks_both_rows_as_errors() -> None:
    rows, _ = parse_workbook(
        workbook_bytes(
            ["id", "name", "group", "institute"],
            [[1, "Иванов Иван", "ИКБО-11-26", "ИИИ"], [1, "Петров Петр", "ИКБО-12-26", "ИИИ"]],
        ),
        100,
    )
    assert all(
        any(
            issue.code == "IMPORT_SOURCE_ID_DUPLICATE" and issue.severity == ErrorSeverity.ERROR
            for issue in row.issues
        )
        for row in rows
    )


def test_formula_is_rejected() -> None:
    rows, _ = parse_workbook(
        workbook_bytes(
            ["id", "name", "group", "institute"], [[1, '=CONCAT("Иван","ов")', "ИКБО-11-26", "ИИИ"]]
        ),
        100,
    )
    assert any(issue.code == "IMPORT_FORMULA_NOT_ALLOWED" for issue in rows[0].issues)


def test_extra_columns_are_warning() -> None:
    _, issues = parse_workbook(
        workbook_bytes(
            ["id", "name", "group", "institute", "extra"],
            [[1, "Иванов Иван", "ИКБО-11-26", "ИИИ", "x"]],
        ),
        100,
    )
    assert issues[0].severity == ErrorSeverity.WARNING


def test_zip_bomb_is_rejected() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "x" * 1_000_000)
        archive.writestr("xl/worksheets/sheet1.xml", "x" * 1_000_000)
    with pytest.raises(AppError) as caught:
        parse_workbook(stream.getvalue(), 100)
    assert caught.value.code == "IMPORT_ZIP_BOMB"
