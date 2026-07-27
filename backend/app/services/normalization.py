import re
import unicodedata

SPACE_RE = re.compile(r"\s+")
GROUP_RE = re.compile(r"^[А-ЯЁA-Z]{2,6}-?\d{2}-\d{2}$")


def _normalize_spaces(value: str) -> str:
    return SPACE_RE.sub(" ", unicodedata.normalize("NFKC", value).strip())


def normalize_name(value: str) -> str:
    return _normalize_spaces(value).casefold().replace("ё", "е")


def normalize_group(value: str) -> str:
    return _normalize_spaces(value).upper()


def normalize_institute(value: str) -> str:
    return _normalize_spaces(value).casefold().replace("ё", "е")


def has_control_characters(value: str) -> bool:
    return any(unicodedata.category(character).startswith("C") for character in value)
