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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt limits to 72 bytes. Truncating here as fallback.
    pwd_bytes = plain_password[:72].encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def get_password_hash(password: str) -> str:
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
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "aud": "authenticated"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
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
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_aud": False})
        user_id_str: str = payload.get("sub")
        if user_id_str:
            return db.query(User).filter(User.id == user_id_str).first()
    except Exception:
        return None
    return None

def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker
