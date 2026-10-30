"""Password hashing and signed bearer tokens (HS256 JWT), ported from P3 without extra dependencies."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt. Stored as `salt$hash`."""
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"{salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a password against a `salt$hash` value in constant time."""
    try:
        salt, expected = hashed_password.split("$", 1)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(actual.hex(), expected)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(signing_input: bytes, secret_key: str) -> str:
    return _b64encode(hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest())


def create_access_token(subject: str, secret_key: str, expires_minutes: int = 1440) -> str:
    """Create a signed JWT whose `sub` claim is the user id."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "iat": now, "exp": now + expires_minutes * 60}
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode()
    return f"{header_b64}.{payload_b64}.{_sign(signing_input, secret_key)}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any] | None:
    """Return the token's claims, or None if it is malformed, tampered with or expired."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, signature_b64 = parts
    expected = _sign(f"{header_b64}.{payload_b64}".encode(), secret_key)
    if not hmac.compare_digest(signature_b64, expected):
        return None
    try:
        header = json.loads(_b64decode(header_b64))
        payload = json.loads(_b64decode(payload_b64))
    except (ValueError, UnicodeDecodeError):
        return None
    # Reject tokens that claim another algorithm, e.g. "none".
    if not isinstance(header, dict) or header.get("alg") != "HS256" or not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload
