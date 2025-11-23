"""Security helpers for Prophet Labs platform."""
from __future__ import annotations

import hashlib
import hmac
from typing import Optional


def sign_payload(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


def redact(value: Optional[str]) -> str:
    if value is None:
        return "<empty>"
    if len(value) <= 4:
        return "****"
    return f"***{value[-4:]}"


__all__ = ["sign_payload", "verify_signature", "redact"]
