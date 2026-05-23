"""
常量和配置定义
"""

import os
from pathlib import Path

# ── 路径（支持环境变量覆盖） ──
DB_PATH = Path(os.environ.get("COST_TRACKER_DB", str(Path.home() / "cost-tracker" / "data.db")))
FRONTEND_DIR = Path(os.environ.get("COST_TRACKER_FRONTEND", str(Path.home() / "cost-tracker" / "frontend")))

# ── 会话 ──
SESSION_DURATION_DAYS = 30
MAX_SESSION_AGE_SECONDS = SESSION_DURATION_DAYS * 86400

# ── 物品 ──
ITEM_STATUS_ACTIVE = "在用"
ITEM_CATEGORY_DEFAULT = "其他"

# ── 订阅 ──
BILLING_CYCLE_MONTHS = {"月付": 1, "季付": 3, "半年付": 6, "年付": 12}
DAYS_PER_MONTH = 30
MONTHS_OFFSET = 1

# ── 用户设置 ──
DEFAULT_SETTINGS = {
    "precision": "2",
    "currency": "CNY",
    "exclude_retired": "false",
}

# ── 管理员默认密码（支持环境变量覆盖） ──
DEFAULT_ADMIN_PASSWORD = os.environ.get("COST_TRACKER_ADMIN_PASSWORD", "admin123")

# ── SQL 白名单（防注入） ──
ALLOWED_TABLES = {"items", "subscriptions", "users", "sessions", "settings"}
ALLOWED_COLUMNS = {"retirement_date", "calc_method", "usage_count", "username", "is_admin"}
