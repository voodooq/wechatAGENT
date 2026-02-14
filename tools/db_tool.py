"""
数据库查询工具

允许 AI Agent 查询本地 SQLite 数据库，
仅支持 SELECT 操作以确保数据安全。
"""
import sqlite3
from langchain_core.tools import tool

from core.config import conf
from utils.logger import logger


def _getDbPath() -> str:
    """获取数据库文件绝对路径"""
    return str(conf.db_full_path)


def _initDemoDb() -> None:
    """
    初始化演示数据库

    创建示例表并插入测试数据，
    仅在数据库不存在时执行。
    """
    db_path = _getDbPath()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT '已完成',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建库存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL UNIQUE,
            stock INTEGER NOT NULL DEFAULT 0,
            unit_price REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建权限表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remark_name TEXT NOT NULL UNIQUE,
            role_level INTEGER NOT NULL, -- 3:Root, 2:Admin, 1:Guest
            added_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建群白名单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL UNIQUE,
            allow_guest_chat BOOLEAN DEFAULT 1
        )
    """)

    # 创建审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            command TEXT NOT NULL,
            action_taken TEXT,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 插入默认权限（主人）
    cursor.execute("SELECT COUNT(*) FROM user_permissions")
    if cursor.fetchone()[0] == 0:
        master_name = conf.whitelist[0] if conf.whitelist else "文件传输助手"
        cursor.execute(
            "INSERT INTO user_permissions (remark_name, role_level, added_by) VALUES (?, ?, ?)",
            (master_name, 3, "SYSTEM")
        )
        logger.info(f"已初始化主人权限: {master_name} (Level 3)")

    # 插入示例数据（如果表为空）
    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        demo_orders = [
            ("张三", "笔记本电脑", 2, 6999.00, "已完成"),
            ("李四", "机械键盘", 5, 599.00, "已完成"),
            ("王五", "显示器", 1, 2499.00, "待发货"),
            ("赵六", "鼠标", 10, 199.00, "已完成"),
            ("钱七", "耳机", 3, 899.00, "待发货"),
        ]
        cursor.executemany(
            "INSERT INTO orders (customer_name, product, quantity, price, status) VALUES (?, ?, ?, ?, ?)",
            demo_orders,
        )
        logger.info("已插入订单示例数据")

    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        demo_inventory = [
            ("笔记本电脑", 50, 6999.00),
            ("机械键盘", 200, 599.00),
            ("显示器", 30, 2499.00),
            ("鼠标", 500, 199.00),
            ("耳机", 100, 899.00),
        ]
        cursor.executemany(
            "INSERT INTO inventory (product, stock, unit_price) VALUES (?, ?, ?)",
            demo_inventory,
        )
        logger.info("已插入库存示例数据")

    conn.commit()
    conn.close()


@tool
def queryDatabase(query: str) -> str:
    """
    查询本地 SQLite 数据库。当用户询问订单、库存、销售等业务数据时使用此工具。

    输入应为合法的 SQL SELECT 语句。
    可用的表：
    - orders: 订单表 (id, customer_name, product, quantity, price, status, created_at)
    - inventory: 库存表 (id, product, stock, unit_price, updated_at)

    Args:
        query: SQL SELECT 查询语句
    """
    # 安全检查：仅允许 SELECT 语句
    normalized = query.strip().upper()
    if not normalized.startswith("SELECT"):
        return "错误：出于安全考虑，仅允许执行 SELECT 查询语句。"

    # NOTE: 拦截危险关键字，防止 SQL 注入式的破坏操作
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if keyword in normalized:
            return f"错误：检测到危险关键字 '{keyword}'，查询已被拒绝。"

    try:
        conn = sqlite3.connect(_getDbPath())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "查询结果为空，没有找到匹配的数据。"

        # 格式化输出
        columns = rows[0].keys()
        result_lines = [" | ".join(columns)]
        result_lines.append("-" * len(result_lines[0]))
        for row in rows:
            result_lines.append(" | ".join(str(row[col]) for col in columns))

        return "\n".join(result_lines)

    except sqlite3.Error as e:
        logger.error(f"数据库查询失败: {e}")
        return f"数据库查询失败: {e}"


# 模块加载时自动初始化演示数据库
_initDemoDb()
