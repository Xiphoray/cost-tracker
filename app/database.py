"""
数据库连接和初始化
"""

import sqlite3
import logging
import bcrypt

from .config import DB_PATH, ALLOWED_TABLES, ALLOWED_COLUMNS, DEFAULT_ADMIN_PASSWORD

logger = logging.getLogger("cost-tracker")


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _hash_password(plain_password: str) -> str:
    """生成 bcrypt 密码哈希"""
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def _safe_alter_table(conn, table: str, column: str, default: str):
    """安全地添加列，使用白名单防止 SQL 注入"""
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column name: {column}")
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT DEFAULT ?", (default,))
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise sqlite3.OperationalError(f"Failed to alter table {table}") from e


def _create_items_table(conn):
    """创建物品表"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '其他',
            status TEXT NOT NULL DEFAULT '在用',
            note TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            retirement_date TEXT DEFAULT '',
            warranty_date TEXT DEFAULT '',
            calc_method TEXT NOT NULL DEFAULT '按时间',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    for col, default in [
        ("retirement_date", ""),
        ("warranty_date", ""),
        ("calc_method", "按时间"),
    ]:
        _safe_alter_table(conn, "items", col, default)


def _create_settings_table(conn):
    """创建设置表"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)


def _create_subscriptions_table(conn):
    """创建订阅表"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            billing_cycle TEXT NOT NULL,
            cycle_months INTEGER NOT NULL,
            price_per_cycle REAL NOT NULL,
            auto_renew INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)


def _create_user_tables(conn):
    """创建用户和会话相关表"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    _safe_alter_table(conn, "users", "is_admin", "0")


def _migrate_data(conn):
    """数据迁移：默认用户、字段重命名、数据修复"""
    existing_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if existing_users['cnt'] == 0:
        default_pw_hash = _hash_password(DEFAULT_ADMIN_PASSWORD)
        conn.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
            ('admin', default_pw_hash)
        )

    first_user = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    if first_user:
        conn.execute("UPDATE users SET is_admin=1 WHERE id=?", (first_user['id'],))

        _safe_alter_table(conn, "items", "username", "admin")
        _safe_alter_table(conn, "subscriptions", "username", "admin")
        conn.execute("UPDATE items SET username='admin' WHERE username IS NULL OR username=''")
        conn.execute("UPDATE subscriptions SET username='admin' WHERE username IS NULL OR username=''")

    try:
        conn.execute("ALTER TABLE users RENAME COLUMN password_b64 TO password_hash")
    except sqlite3.OperationalError:
        pass


def _create_indexes(conn):
    """创建数据库索引"""
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_username ON items(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_subs_username ON subscriptions(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        _create_items_table(conn)
        _create_settings_table(conn)
        _create_subscriptions_table(conn)
        _create_user_tables(conn)
        _migrate_data(conn)
        _create_indexes(conn)
        conn.commit()
    finally:
        conn.close()
