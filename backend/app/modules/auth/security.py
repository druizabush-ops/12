"""Утилиты безопасности для аутентификации.
Файл существует, чтобы изолировать хэширование пароля и выпуск токенов.
Минимальность: только bcrypt и простые JWT без дополнительных функций.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

import bcrypt


def hash_password(password: str) -> str:
    """Создаёт bcrypt-хэш пароля.
    Нужен исключительно для безопасного хранения в базе.
    """

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет пароль по bcrypt-хэшу.
    Используется только при логине.
    """

    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _get_secret_key() -> bytes:
    """Читает секрет для подписи токенов.
    Минимально: только из окружения без дефолта.
    """

    secret = os.getenv("AUTH_SECRET_KEY")
    if not secret:
        raise RuntimeError("AUTH_SECRET_KEY is required")
    return secret.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    """Кодирует данные в base64url.
    Нужна для сборки JWT без внешних библиотек.
    """

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Декодирует base64url.
    Используется при проверке токена.
    """

    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(subject: str) -> str:
    """Создаёт JWT access token.
    Токен содержит только технический subject и срок жизни.
    """

    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    expires_minutes = int(os.getenv("AUTH_TOKEN_EXPIRES_MINUTES", "30"))
    payload = {"sub": subject, "iat": now, "exp": now + expires_minutes * 60}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(_get_secret_key(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Проверяет JWT и возвращает payload.
    Минимально валидирует подпись и срок действия.
    """

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        _get_secret_key(), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(_b64url_decode(signature_b64), expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp") is not None and int(payload["exp"]) < int(time.time()):
        raise ValueError("Token expired")

    return payload
