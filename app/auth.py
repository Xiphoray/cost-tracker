"""
认证中间件和路由
"""

import logging
import base64
import binascii
import bcrypt
from datetime import datetime
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import FRONTEND_DIR, MAX_SESSION_AGE_SECONDS
from .database import get_db
from .utils import create_session
from .models import LoginRequest, ChangePasswordRequest, ChangeUsernameRequest

logger = logging.getLogger("cost-tracker")

# ── 公开路径 ──
PUBLIC_PATHS = {'/login', '/api/login', '/api/register'}
PUBLIC_PREFIXES = ('/css/', '/js/', '/vendor/', '/favicon')


def get_current_user(request: Request) -> str:
    user = getattr(request.state, 'username', None)
    if not user:
        raise HTTPException(401, "未登录")
    return user


def is_admin(request: Request) -> bool:
    return getattr(request.state, 'is_admin', False)


def _verify_password(stored_password: str, plain_password: str) -> bool:
    """验证密码，支持 bcrypt 和旧的 base64 格式"""
    if stored_password.startswith('$2b$'):
        return bcrypt.checkpw(plain_password.encode(), stored_password.encode())
    else:
        try:
            decoded_pw = base64.b64decode(stored_password).decode()
            return decoded_pw == plain_password
        except (binascii.Error, UnicodeDecodeError):
            return False


def _hash_password(plain_password: str) -> str:
    """生成 bcrypt 密码哈希"""
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def _migrate_password_if_needed(conn, username: str, stored_password: str, plain_password: str):
    """如果密码是旧的 base64 格式，自动迁移到 bcrypt"""
    if not stored_password.startswith('$2b$'):
        new_hash = _hash_password(plain_password)
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
        conn.commit()


# ── 中间件 ──
class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件，拦截未登录请求并重定向到登录页面。

    白名单路径（PUBLIC_PATHS）和静态资源前缀（PUBLIC_PREFIXES）直接放行，
    其余路径校验 session cookie，未通过则返回 302 重定向到 /login。
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        token = request.cookies.get('session_token')
        if token:
            conn = get_db()
            try:
                row = conn.execute("SELECT username, expires_at FROM sessions WHERE token=?", (token,)).fetchone()
                if row and row['expires_at'] > datetime.now().isoformat():
                    request.state.username = row['username']
                    user_row = conn.execute("SELECT is_admin FROM users WHERE username=?", (row['username'],)).fetchone()
                    request.state.is_admin = bool(user_row['is_admin']) if user_row else False
                    return await call_next(request)
            finally:
                conn.close()

        if path.startswith('/api/'):
            return JSONResponse({'error': 'unauthorized'}, status_code=401)
        return RedirectResponse('/login', status_code=302)


# ── 认证路由处理器 ──
def _api_register(body: LoginRequest):
    """用户注册"""
    if not body.username or len(body.username) < 2:
        raise HTTPException(400, "用户名至少2个字符")
    if not body.password or len(body.password) < 6:
        raise HTTPException(400, "密码至少6个字符")
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username=?", (body.username,)).fetchone()
        if existing:
            raise HTTPException(400, "用户名已存在")
        password_hash = _hash_password(body.password)
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (body.username, password_hash))
        conn.commit()
        token = create_session(conn, body.username)
        resp = JSONResponse({"ok": True, "username": body.username})
        resp.set_cookie("session_token", token, max_age=MAX_SESSION_AGE_SECONDS, httponly=True, samesite="lax")
        logger.info("用户注册: %s", body.username)
        return resp
    finally:
        conn.close()


def _api_login(body: LoginRequest):
    """用户登录"""
    conn = get_db()
    try:
        user = conn.execute("SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username=?", (body.username,)).fetchone()
        if not user:
            logger.warning("登录失败(用户不存在): %s", body.username)
            raise HTTPException(401, "用户名或密码错误")

        stored_password = user['password_hash']
        if not _verify_password(stored_password, body.password):
            logger.warning("登录失败(密码错误): %s", body.username)
            raise HTTPException(401, "用户名或密码错误")

        _migrate_password_if_needed(conn, body.username, stored_password, body.password)
        token = create_session(conn, body.username)
        resp = JSONResponse({"ok": True, "username": body.username})
        resp.set_cookie("session_token", token, max_age=MAX_SESSION_AGE_SECONDS, httponly=True, samesite="lax")
        logger.info("用户登录: %s", body.username)
        return resp
    finally:
        conn.close()


def _api_logout(request: Request):
    """用户登出"""
    token = request.cookies.get('session_token')
    if token:
        conn = get_db()
        try:
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
        finally:
            conn.close()
    logger.info("用户登出")
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("session_token")
    return resp


def _api_auth_check(request: Request):
    """检查认证状态"""
    return {"authenticated": hasattr(request.state, 'username'), "username": getattr(request.state, 'username', None), "is_admin": getattr(request.state, 'is_admin', False)}


def _api_change_password(request: Request, body: ChangePasswordRequest):
    """修改密码"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(401, "未登录")
    conn = get_db()
    try:
        user = conn.execute("SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username=?", (username,)).fetchone()
        stored_password = user['password_hash']
        if not _verify_password(stored_password, body.old_password):
            raise HTTPException(400, "原密码错误")
        new_hash = _hash_password(body.new_password)
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
        conn.commit()
        logger.warning("密码修改: %s", username)
        return {"ok": True}
    finally:
        conn.close()


def _api_change_username(request: Request, body: ChangeUsernameRequest):
    """修改用户名"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(401, "未登录")
    if not body.new_username or len(body.new_username) < 2:
        raise HTTPException(400, "用户名至少2个字符")
    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username=?", (body.new_username,)).fetchone()
        if existing:
            raise HTTPException(400, "用户名已存在")
        conn.execute("UPDATE users SET username=? WHERE username=?", (body.new_username, username))
        conn.execute("UPDATE sessions SET username=? WHERE username=?", (body.new_username, username))
        conn.execute("UPDATE settings SET key = REPLACE(key, ?, ?) WHERE key LIKE ?", (username + ":", body.new_username + ":", username + ":%"))
        conn.commit()
        logger.warning("用户名修改: %s -> %s", username, body.new_username)
        return {"ok": True, "username": body.new_username}
    finally:
        conn.close()


def _login_page():
    """登录页面"""
    return FileResponse(str(FRONTEND_DIR / "login.html"))


def register_auth_routes(app):
    """注册认证相关路由"""
    app.post("/api/register")(_api_register)
    app.post("/api/login")(_api_login)
    app.post("/api/logout")(_api_logout)
    app.get("/api/auth/check")(_api_auth_check)
    app.post("/api/change-password")(_api_change_password)
    app.post("/api/change-username")(_api_change_username)
    app.get("/login", response_class=HTMLResponse)(_login_page)
