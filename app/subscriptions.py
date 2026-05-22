"""
订阅相关路由
"""

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, Request

from .database import get_db
from .models import SubscriptionCreate, SubscriptionUpdate
from .utils import subscription_to_dict, get_cycle_months
from .auth import get_current_user

logger = logging.getLogger("cost-tracker")

# 订阅表查询语句
SUB_SELECT_ALL = (
    "SELECT id, name, start_date, billing_cycle, cycle_months, price_per_cycle, auto_renew, created_at "
    "FROM subscriptions WHERE username=? ORDER BY created_at DESC"
)
SUB_SELECT_BY_ID = (
    "SELECT id, name, start_date, billing_cycle, cycle_months, price_per_cycle, auto_renew, created_at "
    "FROM subscriptions WHERE id=? AND username=?"
)


def _get_subscriptions(request: Request):
    """获取用户所有订阅"""
    user = get_current_user(request)
    conn = get_db()
    try:
        rows = conn.execute(
            SUB_SELECT_ALL, (user,)
        ).fetchall()
        return [subscription_to_dict(r) for r in rows]
    finally:
        conn.close()


def _create_subscription(request: Request, sub: SubscriptionCreate):
    """创建订阅"""
    user = get_current_user(request)
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO subscriptions "
            "(name, start_date, billing_cycle, cycle_months, price_per_cycle, auto_renew, username) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                sub.name,
                sub.start_date,
                sub.billing_cycle,
                get_cycle_months(sub.billing_cycle),
                sub.price_per_cycle,
                1 if sub.auto_renew else 0,
                user,
            ),
        )
        conn.commit()
        row = conn.execute(SUB_SELECT_BY_ID, (cur.lastrowid, user)).fetchone()
        return subscription_to_dict(row)
    finally:
        conn.close()


def _update_subscription(sub_id: int, sub: SubscriptionUpdate, request: Request):
    """更新订阅"""
    user = get_current_user(request)
    conn = get_db()
    try:
        existing = conn.execute(SUB_SELECT_BY_ID, (sub_id, user)).fetchone()
        if not existing:
            raise HTTPException(404, "Subscription not found")
        sub_dict = dict(existing)
        updates = sub.model_dump(exclude_none=True)
        sub_dict.update(updates)
        sub_dict["cycle_months"] = get_cycle_months(sub_dict["billing_cycle"])
        conn.execute(
            "UPDATE subscriptions SET name=?, start_date=?, billing_cycle=?, cycle_months=?, "
            "price_per_cycle=?, auto_renew=? WHERE id=? AND username=?",
            (
                sub_dict["name"],
                sub_dict["start_date"],
                sub_dict["billing_cycle"],
                sub_dict["cycle_months"],
                sub_dict["price_per_cycle"],
                1 if sub_dict.get("auto_renew") else 0,
                sub_id,
                user,
            ),
        )
        conn.commit()
        row = conn.execute(SUB_SELECT_BY_ID, (sub_id, user)).fetchone()
        return subscription_to_dict(row)
    finally:
        conn.close()


def _renew_subscription(sub_id: int, request: Request):
    """续订订阅"""
    user = get_current_user(request)
    conn = get_db()
    try:
        row = conn.execute(SUB_SELECT_BY_ID, (sub_id, user)).fetchone()
        if not row:
            raise HTTPException(404, "Subscription not found")
        sub_dict = dict(row)
        start = datetime.strptime(sub_dict["start_date"], "%Y-%m-%d").date()
        months = sub_dict["cycle_months"]
        new_start = start + relativedelta(months=months)
        conn.execute(
            "UPDATE subscriptions SET start_date=?, auto_renew=1 WHERE id=? AND username=?",
            (new_start.isoformat(), sub_id, user),
        )
        conn.commit()
        updated = conn.execute(SUB_SELECT_BY_ID, (sub_id, user)).fetchone()
        return subscription_to_dict(updated)
    finally:
        conn.close()


def _delete_subscription(sub_id: int, request: Request):
    """删除订阅"""
    user = get_current_user(request)
    conn = get_db()
    try:
        conn.execute("DELETE FROM subscriptions WHERE id=? AND username=?", (sub_id, user))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def register_subscription_routes(app):
    """注册订阅相关路由"""
    app.get("/api/subscriptions")(_get_subscriptions)
    app.post("/api/subscriptions")(_create_subscription)
    app.put("/api/subscriptions/{sub_id}")(_update_subscription)
    app.post("/api/subscriptions/{sub_id}/renew")(_renew_subscription)
    app.delete("/api/subscriptions/{sub_id}")(_delete_subscription)
