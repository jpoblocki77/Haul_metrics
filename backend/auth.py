import os
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request

from db import get_conn, one

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    if not 6 <= len(password) or len(password.encode()) > 72:
        raise HTTPException(422, "Password must be at least 6 characters and at most 72 UTF-8 bytes")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return len(plain.encode()) <= 72 and bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user_id: int, username: str, session_version: str) -> str:
    payload = {"sub": str(user_id), "username": username, "type": "access",
               "jti": uuid.uuid4().hex,
               "version": session_version, "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


def get_token(request: Request):
    token = request.cookies.get("access_token")
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token = header[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    return token


def get_current_user(request: Request) -> dict:
    token = get_token(request)
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    if payload.get("type") != "access" or not str(payload.get("sub", "")).isdigit():
        raise HTTPException(401, "Invalid token")
    with get_conn() as conn:
        if one(conn, "SELECT token_hash FROM session_revocations WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),)):
            raise HTTPException(401, "Session signed out")
        user = one(conn, "SELECT id, username, role, session_version FROM users WHERE id = ?", (int(payload["sub"]),))
    if not user:
        raise HTTPException(401, "User not found")
    if payload.get("version", "0") != user.pop("session_version"):
        raise HTTPException(401, "Session revoked. Sign in again.")
    return user


def revoke_token(request: Request):
    token = get_token(request)
    payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO session_revocations (token_hash,expires_at) VALUES (?,?)",
                     (hashlib.sha256(token.encode()).hexdigest(), payload["exp"]))


def seed_owner():
    username = os.environ["OWNER_USERNAME"].lower()
    password = os.environ["OWNER_PASSWORD"]
    with get_conn() as conn:
        existing = one(conn, "SELECT id FROM users LIMIT 1")
        if not existing:
            conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'owner')", (username, hash_password(password)))


def require_owner(request: Request) -> dict:
    user = get_current_user(request)
    if user["role"] != "owner":
        raise HTTPException(403, "Only an owner can do this")
    return user
