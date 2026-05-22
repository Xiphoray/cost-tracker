"""
统计分析相关路由
"""

import logging
from datetime import datetime, date
from fastapi import Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

from .config import FRONTEND_DIR, DEFAULT_SETTINGS, ITEM_CATEGORY_DEFAULT
from .database import get_db
from .utils import calc_days, subscription_cost, subscription_to_dict, get_cycle_months, get_setting
from .auth import get_current_user

logger = logging.getLogger("cost-tracker")

# 通用查询语句
ITEM_SELECT = "SELECT id, name, price, purchase_date, category, status, note, image_url, retirement_date, warranty_date, calc_method, created_at FROM items WHERE username=?"
SUB_SELECT = "SELECT id, name, start_date, billing_cycle, cycle_months, price_per_cycle, auto_renew, created_at FROM subscriptions WHERE username=?" 


# ── 分析子函数 ──
def _filter_items_by_period(items: list, period: str) -> list:
    """按时间段筛选物品"""
    if period == "all":
        return items
    today = date.today()
    filtered = []
    for item in items:
        purchase_date = datetime.strptime(item["purchase_date"], "%Y-%m-%d").date()
        if period == "year" and purchase_date.year != today.year:
            continue
        elif period == "quarter":
            current_quarter = (today.month - 1) // 3
            item_quarter = (purchase_date.month - 1) // 3
            if purchase_date.year != today.year or item_quarter != current_quarter:
                continue
        elif period == "month" and (purchase_date.year != today.year or purchase_date.month != today.month):
            continue
        filtered.append(item)
    return filtered


def _calculate_category_stats(items: list) -> tuple:
    """计算分类统计"""
    cat_stats = {}
    cat_count = {}
    for item in items:
        category = item["category"]
        cat_stats[category] = cat_stats.get(category, 0) + item["price"]
        cat_count[category] = cat_count.get(category, 0) + 1
    return cat_stats, cat_count


def _calculate_monthly_trend(items: list) -> list:
    """计算月度趋势"""
    monthly = {}
    for item in items:
        purchase_date = datetime.strptime(item["purchase_date"], "%Y-%m-%d")
        key = purchase_date.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + item["price"]
    return sorted(monthly.items())[-12:]


def _calculate_daily_ranking(items: list) -> list:
    """计算日均成本排行"""
    daily_ranking = []
    for item in items:
        days = calc_days(item["purchase_date"])
        daily_ranking.append({"name": item["name"], "daily_cost": round(item["price"] / days, 2)})
    daily_ranking.sort(key=lambda x: x["daily_cost"], reverse=True)
    return daily_ranking[:10]


def _calculate_holding_distribution(items: list) -> list:
    """计算持有时间分布"""
    holding_buckets = [
        {"label": "半年内", "min": 0, "max": 180, "count": 0},
        {"label": "半年到1年", "min": 180, "max": 365, "count": 0},
        {"label": "1-2年", "min": 365, "max": 730, "count": 0},
        {"label": "2年以上", "min": 730, "max": 99999, "count": 0},
    ]
    for item in items:
        days = calc_days(item["purchase_date"])
        for bucket in holding_buckets:
            if bucket["min"] <= days < bucket["max"]:
                bucket["count"] += 1
                break
    total_items = len(items) or 1
    return [
        {"label": bucket["label"], "count": bucket["count"], "percent": round(bucket["count"] / total_items * 100, 1)}
        for bucket in holding_buckets
    ]


def _calculate_price_ranking(items: list) -> list:
    """计算消费榜单"""
    price_ranking = [
        {"name": item["name"], "price": item["price"], "category": item["category"], "purchase_date": item["purchase_date"]}
        for item in items
    ]
    price_ranking.sort(key=lambda x: x["price"], reverse=True)
    return price_ranking[:10]


def _calculate_category_details(cat_stats: dict, cat_count: dict, subs_yearly: float = 0) -> list:
    """计算分类详情（带百分比）"""
    total_price = sum(cat_stats.values()) + subs_yearly
    if subs_yearly > 0:
        cat_stats["订阅服务"] = round(cat_stats.get("订阅服务", 0) + subs_yearly, 2)
        cat_count["订阅服务"] = cat_count.get("订阅服务", 0) + 1

    details = []
    for category, amount in sorted(cat_stats.items(), key=lambda x: x[1], reverse=True):
        details.append({
            "category": category,
            "amount": round(amount, 2),
            "count": cat_count[category],
            "percent": round(amount / total_price * 100, 1) if total_price else 0,
        })
    return details


def _calculate_stats(items, subs, user):
    """计算统计数据"""
    subs_cost = [subscription_cost(dict(s)) for s in subs]
    sub_monthly = sum(cost["monthly_cost"] for cost in subs_cost)
    sub_daily = sum(cost["daily_cost"] for cost in subs_cost)

    if not items:
        return {"total_count": 0, "total_value": 0, "avg_daily_cost": 0, "today_cost": round(sub_daily, 2), "month_spending": round(sub_monthly, 2), "subscription_count": len(subs_cost), "subscription_monthly": round(sub_monthly, 2)}

    exclude = get_setting("exclude_retired", "false", user) == "true"
    if exclude:
        today_str = date.today().isoformat()
        items = [item for item in items if not item["retirement_date"] or item["retirement_date"] > today_str]

    today = date.today()
    total_value = sum(item["price"] for item in items)
    daily_costs = []
    month_spending = 0
    for item in items:
        days = calc_days(item["purchase_date"])
        daily_costs.append(item["price"] / days)
        purchase_date = datetime.strptime(item["purchase_date"], "%Y-%m-%d").date()
        if purchase_date.month == today.month and purchase_date.year == today.year:
            month_spending += item["price"]

    month_spending += sub_monthly
    avg_daily_cost = (sum(daily_costs) + sub_daily) / len(daily_costs) if daily_costs else sub_daily
    today_cost = round(sum(daily_costs) + sub_daily, 2)

    return {
        "total_count": len(items),
        "total_value": round(total_value, 2),
        "avg_daily_cost": round(avg_daily_cost, 2),
        "today_cost": today_cost,
        "month_spending": round(month_spending, 2),
        "subscription_count": len(subs_cost),
        "subscription_monthly": round(sub_monthly, 2),
    }


def _merge_subscription_analytics(items, subs, period):
    """合并订阅和物品的分析数据"""
    filtered = _filter_items_by_period(items, period)
    cat_stats, cat_count = _calculate_category_stats(filtered)
    monthly_trend = _calculate_monthly_trend(filtered)
    daily_ranking = _calculate_daily_ranking(filtered)
    holding_distribution = _calculate_holding_distribution(filtered)
    price_ranking = _calculate_price_ranking(filtered)

    subs_list = [subscription_to_dict(s) for s in subs]
    sub_monthly = sum(s["monthly_cost"] for s in subs_list)
    sub_yearly = sub_monthly * 12

    sub_daily_ranking = [{"name": s["name"], "daily_cost": s["daily_cost"], "is_subscription": True} for s in subs_list]
    all_daily_ranking = (daily_ranking + sub_daily_ranking)[:10]

    sub_spending = [{"name": s["name"], "price": round(s["monthly_cost"] * 12, 2), "category": "订阅服务", "purchase_date": s["start_date"], "is_subscription": True} for s in subs_list]
    all_spending = (price_ranking + sub_spending)[:10]

    category_details = _calculate_category_details(cat_stats, cat_count, sub_yearly)

    return {
        "category_stats": cat_stats,
        "category_count": cat_count,
        "category_details": category_details,
        "monthly_trend": monthly_trend,
        "daily_cost_ranking": all_daily_ranking,
        "monthly_count": sorted(_calculate_monthly_trend(items), reverse=True)[:12],
        "holding_distribution": holding_distribution,
        "spending_ranking": all_spending,
        "total_price": round(sum(cat_stats.values()) + sub_yearly, 2),
        "period": period,
        "subscription_monthly": round(sub_monthly, 2),
        "subscription_yearly": round(sub_yearly, 2),
        "subscriptions": subs_list,
    }


# ── 路由处理器 ──
def _get_stats(request: Request):
    """获取统计数据"""
    user = get_current_user(request)
    conn = get_db()
    try:
        items = conn.execute(ITEM_SELECT, (user,)).fetchall()
        subs = conn.execute(SUB_SELECT, (user,)).fetchall()
    finally:
        conn.close()
    return _calculate_stats(items, subs, user)


def _get_analytics(request: Request, period: str = "all"):
    """获取分析数据"""
    user = get_current_user(request)
    conn = get_db()
    try:
        items = conn.execute(ITEM_SELECT, (user,)).fetchall()
        subs = conn.execute(SUB_SELECT, (user,)).fetchall()
    finally:
        conn.close()
    return _merge_subscription_analytics(items, subs, period)


def _export_data(request: Request):
    """导出数据"""
    user = get_current_user(request)
    conn = get_db()
    try:
        items = conn.execute("SELECT name,price,purchase_date,category,note,image_url,retirement_date,warranty_date,calc_method FROM items WHERE username=? ORDER BY created_at", (user,)).fetchall()
        subs = conn.execute("SELECT name,start_date,billing_cycle,price_per_cycle,auto_renew FROM subscriptions WHERE username=? ORDER BY created_at", (user,)).fetchall()
        settings_rows = conn.execute("SELECT key, value FROM settings WHERE key LIKE ?", (user + ":%",)).fetchall()
        settings = {row["key"].split(":", 1)[1]: row["value"] for row in settings_rows}
        logger.info("数据导出: %s (物品%d, 订阅%d)", user, len(items), len(subs))
        return {
            "items": [dict(r) for r in items],
            "subscriptions": [dict(r) for r in subs],
            "settings": settings,
            "exported_at": datetime.now().isoformat(),
            "username": user,
        }
    finally:
        conn.close()


def _import_items_batch(conn, items, user):
    """批量导入物品"""
    count = 0
    for item in items:
        conn.execute(
            "INSERT INTO items (name,price,purchase_date,category,note,image_url,retirement_date,warranty_date,calc_method,username) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (item.get("name", ""), item.get("price", 0), item.get("purchase_date", ""), item.get("category", ITEM_CATEGORY_DEFAULT),
             item.get("note", ""), item.get("image_url", ""), item.get("retirement_date", ""),
             item.get("warranty_date", ""), item.get("calc_method", "按时间"), user),
        )
        count += 1
    return count


def _import_subs_batch(conn, subs, user):
    """批量导入订阅"""
    count = 0
    for sub in subs:
        cycle = sub.get("billing_cycle", "月付")
        conn.execute(
            "INSERT INTO subscriptions (name,start_date,billing_cycle,cycle_months,price_per_cycle,auto_renew,username) VALUES (?,?,?,?,?,?,?)",
            (sub.get("name", ""), sub.get("start_date", ""), cycle, get_cycle_months(cycle),
             sub.get("price_per_cycle", 0), 1 if sub.get("auto_renew") else 0, user),
        )
        count += 1
    return count


def _import_settings_batch(conn, settings, user):
    """批量导入设置"""
    count = 0
    for key, value in settings.items():
        if key in DEFAULT_SETTINGS:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (user + ":" + key, str(value)))
            count += 1
    return count


def _import_full_data(request: Request, body: dict, mode: str = "append"):
    """完整数据导入"""
    user = get_current_user(request)
    conn = get_db()
    try:
        if mode == "overwrite":
            conn.execute("DELETE FROM items WHERE username=?", (user,))
            conn.execute("DELETE FROM subscriptions WHERE username=?", (user,))
            conn.execute("DELETE FROM settings WHERE key LIKE ?", (user + ":%",))
        imported_items = _import_items_batch(conn, body.get("items", []), user)
        imported_subs = _import_subs_batch(conn, body.get("subscriptions", []), user)
        imported_settings = _import_settings_batch(conn, body.get("settings", {}), user)
        conn.commit()
        logger.info("数据导入: %s mode=%s (物品%d, 订阅%d, 设置%d)", user, mode, imported_items, imported_subs, imported_settings)
        return {"ok": True, "imported_items": imported_items, "imported_subs": imported_subs, "imported_settings": imported_settings}
    finally:
        conn.close()


def _get_settings(request: Request):
    """获取设置"""
    user = get_current_user(request)
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM settings WHERE key LIKE ?", (user + ":%",)).fetchall()
        result = dict(DEFAULT_SETTINGS)
        for row in rows:
            result[row["key"].split(":", 1)[1]] = row["value"]
        return result
    finally:
        conn.close()


def _update_settings(request: Request, body: dict):
    """更新设置"""
    user = get_current_user(request)
    conn = get_db()
    try:
        for key, value in body.items():
            if key in DEFAULT_SETTINGS:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (user + ":" + key, str(value)))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def _settings_page():
    """设置页面"""
    return FileResponse(str(FRONTEND_DIR / "settings.html"))


def _analytics_page():
    """分析页面"""
    return FileResponse(str(FRONTEND_DIR / "analytics.html"))


def _import_page():
    """导入页面重定向"""
    return RedirectResponse(url="/settings", status_code=301)


# ── 路由注册 ──
def register_analytics_routes(app):
    """注册统计分析路由"""
    app.get("/api/stats")(_get_stats)
    app.get("/api/analytics")(_get_analytics)


def register_data_routes(app):
    """注册数据导出/导入路由"""
    app.get("/api/export")(_export_data)
    app.post("/api/import-full")(_import_full_data)


def register_settings_routes(app):
    """注册设置路由"""
    app.get("/api/settings")(_get_settings)
    app.put("/api/settings")(_update_settings)


def register_page_routes(app):
    """注册页面路由"""
    app.get("/settings", response_class=HTMLResponse)(_settings_page)
    app.get("/analytics", response_class=HTMLResponse)(_analytics_page)
    app.get("/import", response_class=HTMLResponse)(_import_page)
