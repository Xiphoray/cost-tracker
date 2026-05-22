<div align="center">

# 🐎 白驹过隙

**个人物品日均成本追踪器**

*时光如白驹过隙，每一笔消费都值得被记录*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## ✨ 功能特性

### 📦 物品管理
- 添加、编辑、删除物品，支持批量导入/导出
- 自动计算日均持有成本，直观展示"这东西每天花了我多少钱"
- 支持按时间、按次数两种成本计算方式
- 物品退役、保修期管理

### 🔄 订阅服务
- 管理月付/季付/半年付/年付订阅
- 自动续订提醒，一键续订
- 订阅成本纳入总览和分析统计

### 📊 数据洞察
- **分类统计**：各品类消费占比，一目了然
- **月度趋势**：近 12 个月消费走势
- **日均排行**：最"烧钱"物品 TOP 10
- **持有分布**：半年内/半年到1年/1-2年/2年以上
- **消费榜单**：历史消费 TOP 10

### ⚙️ 系统功能
- 多用户支持，数据完全隔离
- 管理员后台：用户管理、密码重置、权限控制
- 完整数据导出/导入（JSON 格式）
- 响应式设计，支持亮色/暗色模式
- 日期选择器，中文界面

## 🚀 快速开始

### 环境要求

- Python 3.12+
- pip

### 安装

```bash
# 克隆项目
git clone https://github.com/xiphoray/cost-tracker.git
cd cost-tracker

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
./start.sh
```

服务启动后访问 http://localhost:9271

### 默认账户

| 用户名 | 密码 | 权限 |
|--------|------|------|
| `admin` | `admin` | 超级管理员 |

> ⚠️ 首次使用请立即修改默认密码

## 📁 项目结构

```
cost-tracker/
├── app/                        # 后端应用
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置常量
│   ├── database.py             # 数据库初始化
│   ├── models.py               # Pydantic 数据模型
│   ├── utils.py                # 工具函数
│   ├── auth.py                 # 认证中间件 & 路由
│   ├── items.py                # 物品 API
│   ├── subscriptions.py        # 订阅 API
│   ├── admin.py                # 管理后台 API
│   └── analytics.py            # 统计分析 & 设置 & 导入导出
├── frontend/                   # 前端页面
│   ├── index.html              # 首页
│   ├── login.html              # 登录页
│   ├── settings.html           # 设置页
│   ├── analytics.html          # 数据分析页
│   ├── admin.html              # 管理后台
│   ├── css/style.css           # 样式
│   ├── js/                     # JavaScript
│   └── vendor/                 # 第三方库 (Chart.js, Flatpickr)
├── requirements.txt            # Python 依赖
└── start.sh                    # 启动脚本
```

## 🔌 API 接口

<details>
<summary>点击展开 API 列表</summary>

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/register` | 用户注册 |
| `POST` | `/api/login` | 用户登录 |
| `POST` | `/api/logout` | 用户登出 |
| `GET` | `/api/auth/check` | 检查认证状态 |
| `POST` | `/api/change-password` | 修改密码 |
| `POST` | `/api/change-username` | 修改用户名 |
| `GET` | `/api/items` | 获取物品列表 |
| `POST` | `/api/items` | 创建物品 |
| `PUT` | `/api/items/{id}` | 更新物品 |
| `DELETE` | `/api/items/{id}` | 删除物品 |
| `POST` | `/api/items/import` | 批量导入物品 |
| `GET` | `/api/subscriptions` | 获取订阅列表 |
| `POST` | `/api/subscriptions` | 创建订阅 |
| `PUT` | `/api/subscriptions/{id}` | 更新订阅 |
| `POST` | `/api/subscriptions/{id}/renew` | 续订 |
| `DELETE` | `/api/subscriptions/{id}` | 删除订阅 |
| `GET` | `/api/stats` | 获取统计数据 |
| `GET` | `/api/analytics` | 获取分析数据 |
| `GET` | `/api/settings` | 获取设置 |
| `PUT` | `/api/settings` | 更新设置 |
| `GET` | `/api/export` | 导出数据 |
| `POST` | `/api/import-full` | 导入完整数据 |
| `GET` | `/api/admin/users` | 管理员：用户列表 |
| `DELETE` | `/api/admin/users/{name}` | 管理员：删除用户 |
| `POST` | `/api/admin/users/{name}/promote` | 管理员：提升权限 |
| `POST` | `/api/admin/users/{name}/demote` | 管理员：撤销权限 |
| `POST` | `/api/admin/users/{name}/reset-password` | 管理员：重置密码 |

</details>

## 🔧 配置

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `COST_TRACKER_DB` | 数据库文件路径 | `~/cost-tracker/data.db` |
| `COST_TRACKER_FRONTEND` | 前端目录路径 | `~/cost-tracker/frontend` |
| `COST_TRACKER_ADMIN_PASSWORD` | 默认管理员密码 | `admin` |

### Systemd 服务

```bash
# 创建服务文件
cat > ~/.config/systemd/user/cost-tracker.service << 'EOF'
[Unit]
Description=Cost Tracker Web Application
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/cost-tracker
ExecStart=/path/to/cost-tracker/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9271
Restart=always

[Install]
WantedBy=default.target
EOF

# 启用并启动
systemctl --user daemon-reload
systemctl --user enable --now cost-tracker
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI + Uvicorn |
| **数据库** | SQLite (WAL 模式) |
| **密码加密** | bcrypt |
| **数据验证** | Pydantic v2 |
| **图表** | Chart.js |
| **日期选择** | Flatpickr |
| **前端** | 原生 HTML/CSS/JS |

## 📋 开发规范

本项目遵循：

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [阿里巴巴 Java 开发手册](https://github.com/alibaba/p3c)（适用于通用编码规范）

代码质量：
- ✅ 零 `SELECT *`，全部明确字段
- ✅ 零 f-string SQL，全部参数化查询
- ✅ 所有函数 ≤ 40 行
- ✅ 全部 `try/finally` 管理数据库连接
- ✅ bcrypt 密码哈希 + 环境变量外部化

## 📄 License

[MIT](LICENSE) © 2026
