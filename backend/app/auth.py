from __future__ import annotations

import secrets
import sqlite3
from typing import Optional

from fastapi import Header, HTTPException, status

from .db import connection_scope, hash_password, utcnow


def create_session(username: str, password: str) -> Optional[dict]:
    with connection_scope() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row or row["password_hash"] != hash_password(password):
            return None

        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, row["id"], utcnow()),
        )
        return {
            "token": token,
            "user": {
                "username": row["username"],
                "role": row["role"],
                "displayName": row["display_name"],
            },
        }


def get_user_by_token(token: str) -> Optional[sqlite3.Row]:
    with connection_scope() as conn:
        return conn.execute(
            """
            SELECT u.username, u.role, u.display_name
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或令牌无效")
    return authorization.split(" ", 1)[1].strip()


def require_user(authorization: str | None = Header(default=None)) -> dict:
    token = extract_bearer_token(authorization)
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效")
    return {"username": user["username"], "role": user["role"], "displayName": user["display_name"]}


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    user = require_user(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
