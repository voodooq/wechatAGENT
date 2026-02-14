from utils.logger import logger

def format_error_payload(tool_name: str, error_msg: str, suggestion: str) -> str:
    """
    生成结构化的系统反馈，强制引导 Agent 进行自我修正。
    同时记录影子日志 (Shadow Logs) 以供后台开发者观测。
    """
    # 记录影子日志 [SELF_HEALING_TRIGGER]
    logger.warning(
        f"[SELF_HEALING_TRIGGER] 工具 '{tool_name}' 触发自愈链路。\n"
        f"- 原始错误: {error_msg}\n"
        f"- 建议对策: {suggestion}"
    )

    return (
        f"【系统反馈】❌ 调用失败\n"
        f"- 工具: {tool_name}\n"
        f"- 原因: {str(error_msg)}\n"
        f"- 强制指令: 不要放弃。请忽略此错误，立即尝试使用 [{suggestion}] 工具作为替代方案。"
    )
