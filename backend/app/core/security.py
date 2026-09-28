from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ──────────────────────────────────────────────────────────
# Menggunakan bcrypt dengan deprecated="auto" untuk kompatibilitas upgrade
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Menghasilkan bcrypt hash dari plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi plaintext password terhadap hash yang tersimpan."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token ─────────────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Membuat JWT access token.

    Args:
        data: Payload yang akan di-encode (biasanya mengandung `sub` berupa user ID).
        expires_delta: Durasi kedaluwarsa. Jika None, menggunakan nilai dari settings.

    Returns:
        JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Mendekode dan memvalidasi JWT access token.

    Returns:
        Payload dict.

    Raises:
        JWTError: Jika token tidak valid atau sudah kedaluwarsa.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
