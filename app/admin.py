"""
管理员相关路由
"""

import logging
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from .config import FRONTEND_DIR, DEFAULT_ADMIN_PASSWORD
from .database import get_db
from .auth import get_current_user, is_admin, _hash_password

logger = logging.getLogger("cost-tracker")


def _admin_list_users(request: Request):
    """获取用户列表"""
    if not is_admin(request):
        raise HTTPException(403, "无权限")
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT u.id, u.username, u.is_admin, u.created_at,
              (SELECT COUNT(*) FROM items WHERE username=u.username) as item_count,
              (SELECT COUNT(*) FROM subscriptions WHERE username=u.username) as sub_count,
              (SELECT COUNT(*) FROM sessions WHERE username=u.username) as total_sessions,
              (SELECT COUNT(*) FROM sessions WHERE username=u.username AND expires_at > datetime('now','localtime')) as active_sessions
            FROM users u ORDER BY u.id
        """).fetchall()
        return [
            {
                "id": row['id'], "username": row['username'], "is_admin": bool(row['is_admin']),
                "created_at": row['created_at'], "item_count": row['item_count'],
                "sub_count": row['sub_count'], "active_sessions": row['active_sessions'], "total_sessions": row['total_sessions'],
            }
            for row in rows
        ]
    finally:
        conn.close()


def _admin_delete_user(request: Request, username: str):
    """删除用户"""
    if not is_admin(request):
        raise HTTPException(403, "无权限")
    current_user = get_current_user(request)
    if username == current_user:
        raise HTTPException(400, "不能删除自己")
    conn = get_db()
    try:
        user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if not user:
            raise HTTPException(404, "用户不存在")
        conn.execute("DELETE FROM items WHERE username=?", (username,))
        conn.execute("DELETE FROM subscriptions WHERE username=?", (username,))
        conn.execute("DELETE FROM sessions WHERE username=?", (username,))
        conn.execute("DELETE FROM settings WHERE key LIKE ?", (username + ":%",))
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        logger.warning("管理员删除用户: %s (操作人: %s)", username, current_user)
        return {"ok": True, "deleted": username}
    finally:
        conn.close()


def _admin_promote_user(request: Request, username: str):
    """提升用户为管理员"""
    if not is_admin(request):
        raise HTTPException(403, "无权限")
    conn = get_db()
    try:
        conn.execute("UPDATE users SET is_admin=1 WHERE username=?", (username,))
        conn.commit()
        logger.warning("管理员提升: %s -> 管理员 (操作人: %s)", username, get_current_user(request))
        return {"ok": True}
    finally:
        conn.close()


def _admin_demote_user(request: Request, username: str):
    """撤销管理员权限"""
    if not is_admin(request):
        raise HTTPException(403, "无权限")
    current_user = get_current_user(request)
    if username == current_user:
        raise HTTPException(400, "不能撤销自己的管理员")
    conn = get_db()
    try:
        conn.execute("UPDATE users SET is_admin=0 WHERE username=?", (username,))
        conn.commit()
        logger.warning("管理员降权: %s -> 普通用户 (操作人: %s)", username, current_user)
        return {"ok": True}
    finally:
        conn.close()


def _admin_reset_password(request: Request, username: str):
    """重置用户密码"""
    if not is_admin(request):
        raise HTTPException(403, "无权限")
    conn = get_db()
    try:
        user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if not user:
            raise HTTPException(404, "用户不存在")
        new_hash = _hash_password(DEFAULT_ADMIN_PASSWORD)
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (new_hash, username))
        conn.execute("DELETE FROM sessions WHERE username=?", (username,))
        conn.commit()
        logger.warning("管理员重置密码: %s (操作人: %s)", username, get_current_user(request))
        return {"ok": True, "username": username}
    finally:
        conn.close()


def _admin_page():
    """管理页面"""
    return FileResponse(str(FRONTEND_DIR / "admin.html"))


def register_admin_routes(app):
    """注册管理员相关路由"""
    app.get("/api/admin/users")(_admin_list_users)
    app.delete("/api/admin/users/{username}")(_admin_delete_user)
    app.post("/api/admin/users/{username}/promote")(_admin_promote_user)
    app.post("/api/admin/users/{username}/demote")(_admin_demote_user)
    app.post("/api/admin/users/{username}/reset-password")(_admin_reset_password)
    app.get("/admin", response_class=HTMLResponse)(_admin_page)
