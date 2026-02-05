from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

# In-memory token blacklist (in production, use Redis)
token_blacklist: set[str] = set()
refresh_tokens: dict[str, dict] = {}  # refresh_token -> {user_id, expires_at}


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.jwt_exp_minutes)
    to_encode = {"exp": expire, "sub": subject, "type": "access"}
    return jwt.encode(to_encode, settings.jwt_secret, settings.jwt_algorithm)


def create_refresh_token(subject: str, expires_days: int = 30) -> str:
    """Create a refresh token that lasts longer than access token"""
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    token_id = str(uuid4())
    to_encode = {"exp": expire, "sub": subject, "type": "refresh", "jti": token_id}
    token = jwt.encode(to_encode, settings.jwt_secret, settings.jwt_algorithm)
    refresh_tokens[token_id] = {
        "user_id": subject,
        "expires_at": expire,
        "created_at": datetime.now(timezone.utc),
    }
    return token


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != token_type:
            return None
        if token in token_blacklist:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def revoke_token(token: str) -> None:
    """Add token to blacklist"""
    token_blacklist.add(token)


def revoke_refresh_token(token_id: str) -> None:
    """Remove refresh token from storage"""
    refresh_tokens.pop(token_id, None)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password_reset_token() -> str:
    """Generate a random token for password reset"""
    return str(uuid4())

