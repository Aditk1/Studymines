"""
Authentication helpers for password hashing, JWT creation, role detection, and FastAPI user dependencies.
"""

import base64
import json
import hmac
import hashlib
import jwt
from datetime import datetime, timedelta
import os
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

import bcrypt

SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("SUPABASE_JWT_SECRET environment variable is not set!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

def _b64url_encode(raw: bytes) -> str:
    """Encode bytes with unpadded JWT base64url encoding."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    """Decode unpadded JWT base64url text."""
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _fallback_jwt_encode(payload: dict) -> str:
    """Create an HS256 JWT when PyJWT is shadowed by another jwt package."""
    serializable = dict(payload)
    if isinstance(serializable.get("exp"), datetime):
        serializable["exp"] = int(serializable["exp"].timestamp())
    header = {"alg": ALGORITHM, "typ": "JWT"}
    signing_input = ".".join([
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64url_encode(json.dumps(serializable, separators=(",", ":"), default=str).encode("utf-8")),
    ])
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def _fallback_jwt_decode(token: str) -> dict:
    """Verify and decode an HS256 JWT when PyJWT is unavailable."""
    try:
        header_raw, payload_raw, signature_raw = token.split(".")
    except ValueError as exc:
        raise ValueError("Malformed JWT") from exc

    signing_input = f"{header_raw}.{payload_raw}"
    expected = hmac.new(SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    actual = _b64url_decode(signature_raw)
    if not hmac.compare_digest(expected, actual):
        raise ValueError("Invalid JWT signature")

    payload = json.loads(_b64url_decode(payload_raw))
    exp = payload.get("exp")
    if exp is not None and datetime.utcnow().timestamp() > float(exp):
        raise ValueError("JWT has expired")
    return payload


def _jwt_encode(payload: dict) -> str:
    """Encode a JWT using PyJWT when present, otherwise the local HS256 fallback."""
    if hasattr(jwt, "encode"):
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return _fallback_jwt_encode(payload)


def _jwt_decode(token: str) -> dict:
    """Decode a JWT using PyJWT when present, otherwise the local HS256 fallback."""
    if hasattr(jwt, "decode"):
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
    return _fallback_jwt_decode(token)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Handle the verify password operation."""
    # bcrypt limits to 72 bytes. Truncating here as fallback.
    pwd_bytes = plain_password[:72].encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def get_password_hash(password: str) -> str:
    """Handle the get password hash operation."""
    pwd_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

def detect_role_from_email(email: str) -> str:
    """Auto-detect student or teacher based on domain or keywords."""
    email_lower = email.lower()
    if "teacher" in email_lower or "admin" in email_lower or "prof" in email_lower:
        return "teacher"
    return "student"

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Handle the create access token operation."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "aud": "authenticated"})
    encoded_jwt = _jwt_encode(to_encode)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """Handle the get current user operation."""
    token = credentials.credentials
    try:
        payload = _jwt_decode(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user_id = user_id_str
    except Exception as e:
        print("JWT Decode error:", e)
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security), db: Session = Depends(get_db)):
    """Handle the get current user optional operation."""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = _jwt_decode(token)
        user_id_str: str = payload.get("sub")
        if user_id_str:
            return db.query(User).filter(User.id == user_id_str).first()
    except Exception:
        return None
    return None

def require_role(allowed_roles: list[str]):
    """Handle the require role operation."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker
