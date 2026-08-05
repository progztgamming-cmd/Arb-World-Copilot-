from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""


_WORD_RE = re.compile(r"[A-Za-z0-9\u0600-\u06FF]+")


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def has_meaningful_text(text: str | None, min_length: int = 2, max_length: int = 5000) -> bool:
    value = normalize_text(text)
    if len(value) < min_length:
        return False
    if len(value) > max_length:
        return False
    return True


def looks_like_repeated_noise(text: str | None) -> bool:
    value = normalize_text(text)
    if not value:
        return True
    if value.isdigit():
        return True
    if re.fullmatch(r"(.)\1{4,}", value):
        return True
    if len(_WORD_RE.findall(value)) == 0:
        return True
    return False


def validate_name(text: str | None) -> ValidationResult:
    value = normalize_text(text)
    if not value:
        return ValidationResult(False, "missing_name")
    if len(value) < 2:
        return ValidationResult(False, "name_too_short")
    if len(value) > 80:
        return ValidationResult(False, "name_too_long")
    if looks_like_repeated_noise(value):
        return ValidationResult(False, "name_invalid")
    return ValidationResult(True)


def validate_generic_text(text: str | None, *, min_length: int = 2, max_length: int = 2000) -> ValidationResult:
    value = normalize_text(text)
    if not value:
        return ValidationResult(False, "missing_text")
    if len(value) < min_length:
        return ValidationResult(False, "text_too_short")
    if len(value) > max_length:
        return ValidationResult(False, "text_too_long")
    if looks_like_repeated_noise(value):
        return ValidationResult(False, "text_invalid")
    return ValidationResult(True)


def validate_age(text: str | None) -> ValidationResult:
    value = normalize_text(text)
    if not value:
        return ValidationResult(False, "missing_age")
    if not value.isdigit():
        return ValidationResult(False, "age_not_numeric")
    age = int(value)
    if age < 5 or age > 120:
        return ValidationResult(False, "age_out_of_range")
    return ValidationResult(True)


def validate_time_text(text: str | None) -> ValidationResult:
    value = normalize_text(text)
    if not value:
        return ValidationResult(False, "missing_time")
    if len(value) < 2:
        return ValidationResult(False, "time_too_short")
    return ValidationResult(True)


def validate_location(text: str | None) -> ValidationResult:
    value = normalize_text(text)
    if not value:
        return ValidationResult(False, "missing_location")
    if len(value) < 2:
        return ValidationResult(False, "location_too_short")
    if len(value) > 200:
        return ValidationResult(False, "location_too_long")
    return ValidationResult(True)


def validate_screenshot(value: str | None, attachment_urls: list[str] | None = None) -> ValidationResult:
    if attachment_urls:
        return ValidationResult(True)
    normalized = normalize_text(value)
    if not normalized:
        return ValidationResult(False, "missing_screenshot")
    if normalized.lower() in {"skip", "no", "none", "n/a", "تخطي", "لا"}:
        return ValidationResult(True)
    if len(normalized) > 200:
        return ValidationResult(False, "screenshot_text_too_long")
    return ValidationResult(True)


def contains_bad_word(text: str | None, bad_words: set[str]) -> bool:
    value = (text or "").lower()
    return any(word.lower() in value for word in bad_words)


def attachment_urls_from_objects(attachments: list[Any] | None) -> list[str]:
    if not attachments:
        return []
    urls: list[str] = []
    for attachment in attachments:
        url = getattr(attachment, "url", None)
        if url:
            urls.append(str(url))
    return urls


def validate_intake_field(kind: str, field_name: str, value: str | None, attachment_urls: list[str] | None = None) -> ValidationResult:
    if field_name == "name" or field_name == "target_name":
        return validate_name(value)

    if field_name == "age":
        return validate_age(value)

    if field_name == "time_occurred":
        return validate_time_text(value)

    if field_name == "location":
        return validate_location(value)

    if field_name in {"content", "reproduction_steps"}:
        return validate_generic_text(value, min_length=4, max_length=3000)

    if field_name == "screenshot":
        return validate_screenshot(value, attachment_urls)

    return validate_generic_text(value, min_length=2, max_length=2000)


def validate_intake_payload(kind: str, payload: dict[str, str]) -> ValidationResult:
    required_fields_by_kind = {
        "complaint": ("target_name", "time_occurred", "location", "content"),
        "suggestion": ("name", "age", "content"),
        "bug": ("name", "location", "reproduction_steps", "screenshot"),
    }

    required_fields = required_fields_by_kind.get(kind, ())
    for field_name in required_fields:
        if not normalize_text(payload.get(field_name)):
            return ValidationResult(False, f"missing_{field_name}")

    return ValidationResult(True)
