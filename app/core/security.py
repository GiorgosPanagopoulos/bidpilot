from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt
from pydantic import BaseModel, ValidationError

from app.core.settings import settings
from app.models.user import Role

ALGORITHM = "HS256"
_BCRYPT_MAX_BYTES = 72


class TokenPayload(BaseModel):
    sub: str
    company_id: str
    role: Role
    exp: int


def hash_password(password: str) -> str:
    raw = password.encode()
    if len(raw) > _BCRYPT_MAX_BYTES:
        raise ValueError("password longer than 72 bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    raw = password.encode()
    if len(raw) > _BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, hashed.encode())
    except ValueError:
        return False


@lru_cache(maxsize=1)
def dummy_hash() -> str:
    # Checked against on unknown emails so login timing doesn't reveal which emails exist.
    return hash_password("timing-equaliser")


def create_access_token(user_id: str, company_id: str, role: Role) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload | None:
    try:
        data = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "company_id", "exp"]},
        )
        return TokenPayload.model_validate(data)
    except (jwt.PyJWTError, ValidationError):
        return None
