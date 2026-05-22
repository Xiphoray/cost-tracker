"""
工具函数
"""

import uuid
from datetime import datetime, date, timedelta

from .config import BILLING_CYCLE_MONTHS, DAYS_PER_MONTH, MONTHS_OFFSET, SESSION_DURATION_DAYS
from .database import get_db


def calc_days(purchase_date: str) -> int:
    d = datetime.strptime(purchase_date, "%Y-%m-%d").date()
    return max((date.today() - d).days, 1)


def get_cycle_months(billing_cycle: str) -> int:
    return BILLING_CYCLE_MONTHS.get(billing_cycle, 1)


def subscription_cost(sub: dict) -> dict:
    months = sub["cycle_months"]
    price = sub["price_per_cycle"]
    monthly = price / months if months else price
    daily = monthly / DAYS_PER_MONTH
    start = datetime.strptime(sub["start_date"], "%Y-%m-%d").date()
    today = date.today()
    months_elapsed = (today.year - start.year) * 12 + (today.month - start.month) + MONTHS_OFFSET
    total_spent = monthly * max(months_elapsed, 0)
    return {"monthly_cost": round(monthly, 2), "daily_cost": round(daily, 2), "total_spent": round(total_spent, 2)}


def subscription_to_dict(sub) -> dict:
    result = dict(sub)
    result["auto_renew"] = bool(result.get("auto_renew", 0))
    cost = subscription_cost(result)
    result.update(cost)
    return result


def row_to_dict(row) -> dict:
    result = dict(row)
    result["days"] = calc_days(result["purchase_date"])
    result["daily_cost"] = round(result["price"] / result["days"], 2)
    return result


def get_setting(key: str, default: str = "", username: str = None) -> str:
    if username:
        key = f"{username}:{key}"
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def create_session(conn, username: str) -> str:
    """创建会话并返回 token"""
    token = str(uuid.uuid4())
    expires = (datetime.now() + timedelta(days=SESSION_DURATION_DAYS)).isoformat()
    conn.execute("INSERT INTO sessions (token, username, expires_at) VALUES (?,?,?)", (token, username, expires))
    conn.commit()
    return token
