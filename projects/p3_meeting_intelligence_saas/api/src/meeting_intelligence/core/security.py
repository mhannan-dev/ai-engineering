"""Security utilities: password hashing and signed authentication tokens."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def hash_password(password: str, salt: str | None = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:16]
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored salt$hash format."""
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(actual.hex(), expected_hash)
    except Exception:
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 1440,
    claims: dict[str, Any] | None = None,
) -> str:
    """Create a tamper-evident signed JWT-format token."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }
    if claims:
        payload.update(claims)

    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode()

    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_b64 = _b64encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any] | None:
    """Verify and decode a signed token. Returns payload dict or None if invalid/expired."""
    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()

    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    expected_sig_b64 = _b64encode(expected_sig)

    if not hmac.compare_digest(signature_b64, expected_sig_b64):
        return None

    try:
        payload = json.loads(_b64decode(payload_b64).decode("utf-8"))
        if payload.get("exp") and int(payload["exp"]) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
