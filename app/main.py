"""
白驹过隙 - FastAPI 应用初始化和路由挂载
"""

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from .config import FRONTEND_DIR
from .database import init_db
from .auth import AuthMiddleware, register_auth_routes
from .items import register_item_routes
from .subscriptions import register_subscription_routes
from .admin import register_admin_routes
from .analytics import register_analytics_routes, register_data_routes, register_settings_routes, register_page_routes

# ── 日志配置 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── 初始化数据库 ──
init_db()

# ── 创建 FastAPI 应用 ──
app = FastAPI(title="物品日均成本追踪器")

# ── 注册中间件 ──
app.add_middleware(AuthMiddleware)

# ── 注册路由 ──
register_auth_routes(app)
register_item_routes(app)
register_subscription_routes(app)
register_admin_routes(app)
register_analytics_routes(app)
register_data_routes(app)
register_settings_routes(app)
register_page_routes(app)

# ── 静态文件 ──
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
app.mount("/vendor", StaticFiles(directory=str(FRONTEND_DIR / "vendor")), name="vendor")
app.mount("/icons", StaticFiles(directory=str(FRONTEND_DIR / "icons")), name="icons")


@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(str(FRONTEND_DIR / "manifest.json"), media_type="application/manifest+json")


@app.get("/sw.js")
def serve_sw():
    return FileResponse(str(FRONTEND_DIR / "sw.js"), media_type="application/javascript")


@app.get("/{path:path}", response_class=HTMLResponse)
def serve_index(path: str):
    return FileResponse(str(FRONTEND_DIR / "index.html"))
