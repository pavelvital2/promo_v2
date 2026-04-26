"""Redaction helpers for WB API safe contours."""

from __future__ import annotations

import re


SECRET_KEY_MARKERS = (
    "authorization",
    "bearer",
    "token",
    "api_key",
    "apikey",
    "secret",
    "password",
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bAuthorization\s*[:=]\s*[A-Za-z0-9._~+/=-]{6,}", re.IGNORECASE),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\b(api[_-]?key|token|secret|password)\s*[:=]\s*[A-Za-z0-9._~+/=-]{6,}", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"),
)


def is_secret_like_key(key) -> bool:
    normalized = "".join(character for character in str(key).lower() if character.isalnum())
    lowered = str(key).lower()
    return any(marker in lowered or marker in normalized for marker in SECRET_KEY_MARKERS)


def contains_secret_like_value(value) -> bool:
    if value is None or isinstance(value, bool | int | float):
        return False
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    text = str(value)
    return any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)


def assert_no_secret_like_values(value, *, field_name: str = "safe value") -> None:
    if contains_secret_like(value):
        raise ValueError(f"{field_name} contains secret-like values.")


def contains_secret_like(value) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_secret_like_key(key) or contains_secret_like(child):
                return True
        return False
    if isinstance(value, list | tuple | set):
        return any(contains_secret_like(child) for child in value)
    return contains_secret_like_value(value)


def redact(value):
    if isinstance(value, dict):
        sanitized = {}
        redacted_index = 1
        for key, child in value.items():
            if is_secret_like_key(key) or contains_secret_like(child):
                sanitized[f"redacted_field_{redacted_index}"] = "[redacted]"
                redacted_index += 1
            else:
                sanitized[key] = redact(child)
        return sanitized
    if isinstance(value, list):
        return [redact(child) for child in value]
    if contains_secret_like_value(value):
        return "[redacted]"
    return value
