"""
IronSentinel - 管理指令解析器

解析并处理以 # 开头的主人专属命令，
用于动态管理权限、查看日志等。
"""
from core.security import security_gate, RoleLevel
from core.audit import audit_logger
from wechat.sender import sender
from utils.logger import logger


def handle_admin_command(content: str, admin_name: str) -> bool:
    """
    处理管理指令

    @param content 原始指令内容 (如 #授权 张三 2)
    @param admin_name 发送指令的主人备注名
    @returns True 表示这是管理指令且已处理，False 表示不是管理指令
    """
    if not content.startswith("#"):
        return False

    parts = content.strip().split()
    cmd = parts[0].lower()

    try:
        if cmd == "#授权" and len(parts) >= 3:
            # 格式: #授权 备注名 等级
            target = parts[1]
            try:
                level = int(parts[2])
                if level not in [0, 1, 2, 3]:
                    raise ValueError
            except ValueError:
                sender.sendMessage(admin_name, "❌ 错误：等级必须是 0-3 之间的整数。")
                return True

            if security_gate.update_permission(target, level, admin_name):
                audit_logger.log_action(admin_name, content, f"SET_PERMISSION_{target}_{level}")
                sender.sendMessage(admin_name, f"✅ 已将 [{target}] 的权限等级设为 {level}。")
            else:
                sender.sendMessage(admin_name, f"❌ 授权失败，请检查数据库。")
            return True

        elif cmd == "#审计" or cmd == "#日志":
            # 格式: #审计 [数量]
            limit = 10
            if len(parts) >= 2:
                try:
                    limit = int(parts[1])
                except ValueError: pass
            
            logs = audit_logger.get_recent_logs(limit)
            if not logs:
                sender.sendMessage(admin_name, "📋 暂无审计记录。")
            else:
                lines = [f"📋 最近 {len(logs)} 条记录:"]
                for log in logs:
                    lines.append(f"[{log['timestamp'][11:16]}] {log['user']} -> {log['action_taken']} ({log['status']})")
                sender.sendMessage(admin_name, "\n".join(lines))
            return True

        elif cmd == "#重启":
            sender.sendMessage(admin_name, "🔄 正在尝试重启助理服务 (Mutation v10.2.1)...")
            from tools.evolution import request_hot_reload
            request_hot_reload(reason="管理员手动请求重启", report_to=admin_name)
            return True

    except Exception as e:
        logger.error(f"处理管理指令异常: {e}")
        sender.sendMessage(admin_name, f"❌ 指令执行异常: {e}")
    
    return True
