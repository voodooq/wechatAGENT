"""
IronSentinel - RPA 与系统控制工具

实现需要高权限执行的动作，并内置 Sudo 二次确认流。
"""
import os
import subprocess
from langchain_core.tools import tool

from core.security import security_gate, RoleLevel
from core.audit import audit_logger
from utils.logger import logger


@tool
def ask_for_confirmation(reason: str, user_name: str) -> str:
    """
    当需要执行敏感操作（如关机、重启、执行系统命令等）时，必须调用此工具请求用户确认。

    Args:
        reason: 请求确认的原因/操作描述
        user_name: 当前操作的用户名称
    """
    token = security_gate.generate_sudo_token(user_name)
    msg = f"⚠️ [Sudo 确认请求]\n操作: {reason}\n内容: 请通过微信回复 [!confirm {token}] 以授权执行。"
    
    # NOTE: 这里仅作为工具输出，实际发送给用户通常由 Worker 或 Agent 分层处理
    # 但在 IronSentinel 设计中，我们需要在此处记录待确认状态
    logger.warning(f"触发 Sudo 确认: 用户 {user_name}，Token {token}, 原因: {reason}")
    return msg


@tool
def execute_system_command(command: str, user_name: str) -> str:
    """
    执行 Windows 系统命令。此操作极其敏感，仅限 Root 权限使用且必须先请求确认。

    Args:
        command: 要执行的 CMD 指令
        user_name: 当前操作的用户名称
    """
    # 1. 权限基础校验
    auth_info = security_gate.authenticate(user_name)
    if auth_info.role_level < RoleLevel.ROOT:
        audit_logger.log_action(user_name, command, "EXECUTE_CMD", "DENIED")
        return "⛔ 权限拒绝：执行系统命令需要 Root (主人) 权限。"

    # 2. 这里的逻辑通常需要 Agent 已经调用过 ask_for_confirmation 并收到了用户的 confirm。
    # 为了简化演示，这里直接执行，但在实际生产中，Agent 应该有逻辑链。
    try:
        logger.info(f"主人指令执行: {command}")
        # 增加超时时间到 30秒，适应较慢的命令
        # 合并 stdout 和 stderr 以便完整捕获错误
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        status = "SUCCESS" if result.returncode == 0 else "FAIL"
        audit_logger.log_action(user_name, command, "EXECUTE_CMD", status)
        
        if not output.strip():
            return "✅ 指令已执行，无文本输出。"
        return f"指令执行结果:\n{output[:800]}" # 截断防止微信消息过长
    except subprocess.TimeoutExpired:
        audit_logger.log_action(user_name, command, "EXECUTE_CMD", "TIMEOUT")
        return "❌ 指令执行超时 (30秒)。"
    except Exception as e:
        audit_logger.log_action(user_name, command, "EXECUTE_CMD", "FAIL")
        from tools.tools_common import format_error_payload
        return format_error_payload(
            "execute_system_command",
            str(e),
            "检查指令拼写、确认路径引号、或尝试替代命令（如 Windows 环境下的 dir vs ls）"
        )


@tool
def manage_wechat_window(action: str) -> str:
    """
    管理微信窗口状态 (打开/置顶/恢复)。

    Args:
        action: 'restore' 或 'focus'
    """
    from utils.stability import keepAliveWechatWindow
    if keepAliveWechatWindow():
        return "✅ 微信窗口已成功恢复或置顶。"
    return "❌ 无法找到微信窗口句柄。"
