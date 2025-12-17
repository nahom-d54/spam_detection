"""Security utilities for password encryption, JWT tokens, and password hashing."""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context
# Use Argon2 by default (secure modern algorithm) while keeping bcrypt
# in the list so existing bcrypt hashes still verify.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"], default="argon2", deprecated="auto"
)

# Fernet cipher for encrypting IMAP passwords
cipher_suite = Fernet(settings.FERNET_KEY.encode())


def hash_password(password: str) -> str:
    """Hash a password using the configured scheme (Argon2 by default).

    This avoids the 72-byte bcrypt input limitation by using Argon2 for new
    hashes while still supporting verification of older bcrypt hashes.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_password(password: str) -> str:
    """Encrypt a password using Fernet symmetric encryption."""
    encrypted = cipher_suite.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password using Fernet symmetric encryption."""
    decrypted = cipher_suite.decrypt(encrypted_password.encode())
    return decrypted.decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None
