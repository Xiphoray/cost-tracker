"""
物品相关路由
"""

import logging
from fastapi import HTTPException, Request

from .config import ITEM_STATUS_ACTIVE
from .database import get_db
from .models import ItemCreate, ItemUpdate
from .utils import row_to_dict
from .auth import get_current_user

logger = logging.getLogger("cost-tracker")

# 物品表查询语句
ITEM_SELECT_ALL = (
    "SELECT id, name, price, purchase_date, category, status, note, image_url, "
    "retirement_date, warranty_date, calc_method, usage_count, created_at "
    "FROM items WHERE username=? ORDER BY created_at DESC"
)
ITEM_SELECT_BY_ID = (
    "SELECT id, name, price, purchase_date, category, status, note, image_url, "
    "retirement_date, warranty_date, calc_method, usage_count, created_at "
    "FROM items WHERE id=? AND username=?"
)


def _get_items(request: Request):
    """获取用户所有物品"""
    user = get_current_user(request)
    conn = get_db()
    try:
        rows = conn.execute(
            ITEM_SELECT_ALL, (user,)
        ).fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def _create_item(request: Request, item: ItemCreate):
    """创建物品"""
    user = get_current_user(request)
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO items ("
            "name, price, purchase_date, category, status, note, image_url, "
            "retirement_date, warranty_date, calc_method, usage_count, username"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                item.name,
                item.price,
                item.purchase_date,
                item.category,
                ITEM_STATUS_ACTIVE,
                item.note,
                item.image_url,
                item.retirement_date,
                "",
                item.calc_method,
                item.usage_count,
                user,
            ),
        )
        conn.commit()
        row = conn.execute(ITEM_SELECT_BY_ID, (cur.lastrowid, user)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def _update_item(item_id: int, item: ItemUpdate, request: Request):
    """更新物品"""
    user = get_current_user(request)
    conn = get_db()
    try:
        existing = conn.execute(ITEM_SELECT_BY_ID, (item_id, user)).fetchone()
        if not existing:
            raise HTTPException(404, "Item not found")
        item_dict = dict(existing)
        for key, value in item.model_dump(exclude_none=True).items():
            item_dict[key] = value
        conn.execute(
            "UPDATE items SET name=?, price=?, purchase_date=?, category=?, note=?, image_url=?, "
            "retirement_date=?, warranty_date=?, calc_method=?, usage_count=? WHERE id=? AND username=?",
            (
                item_dict["name"],
                item_dict["price"],
                item_dict["purchase_date"],
                item_dict["category"],
                item_dict["note"],
                item_dict["image_url"],
                item_dict.get("retirement_date", ""),
                "",
                item_dict.get("calc_method", "按时间"),
                item_dict.get("usage_count", 0),
                item_id,
                user,
            ),
        )
        conn.commit()
        row = conn.execute(ITEM_SELECT_BY_ID, (item_id, user)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def _delete_item(item_id: int, request: Request):
    """删除物品"""
    user = get_current_user(request)
    conn = get_db()
    try:
        conn.execute("DELETE FROM items WHERE id=? AND username=?", (item_id, user))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def _import_items(request: Request, items: list[ItemCreate], mode: str = "append"):
    """批量导入物品"""
    user = get_current_user(request)
    conn = get_db()
    try:
        if mode == "overwrite":
            conn.execute("DELETE FROM items WHERE username=?", (user,))
        count = 0
        for item in items:
            conn.execute(
                "INSERT INTO items ("
                "name, price, purchase_date, category, status, note, image_url, "
                "retirement_date, warranty_date, calc_method, usage_count, username"
               ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
               (
                   item.name,
                   item.price,
                   item.purchase_date,
                   item.category,
                   ITEM_STATUS_ACTIVE,
                   item.note,
                   item.image_url,
                   item.retirement_date,
                   "",
                   item.calc_method,
                    item.usage_count,
                   user,
                ),
            )
            count += 1
        conn.commit()
        logger.info("物品批量导入: %s mode=%s (%d件)", user, mode, count)
        return {"imported": count}
    finally:
        conn.close()


def register_item_routes(app):
    """注册物品相关路由"""
    app.get("/api/items")(_get_items)
    app.post("/api/items")(_create_item)
    app.put("/api/items/{item_id}")(_update_item)
    app.delete("/api/items/{item_id}")(_delete_item)
    app.post("/api/items/import")(_import_items)
