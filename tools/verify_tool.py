"""
IronSentinel - 状态验证工具

让 Agent 具备"检查自己作业"的能力。
在执行操作后，Agent 可以调用此工具验证任务是否真正完成。
"""
import os
import subprocess
from langchain_core.tools import tool

from utils.logger import logger


@tool
def verify_state(check_type: str, target: str) -> str:
    """
    验证任务是否成功完成。在执行完操作后，必须调用此工具进行一次检查确认。

    典型场景：
    - 删除文件后验证文件是否已消失
    - 执行命令后验证输出是否包含预期内容
    - 发送消息后确认状态

    Args:
        check_type: 检查类型，可选值：
            - "file_exists": 检查文件/目录是否存在
            - "file_not_exists": 检查文件/目录是否已删除
            - "command_output": 执行命令并返回结果供评估
            - "process_running": 检查进程是否正在运行
        target: 检查目标（文件路径 / 命令 / 进程名）
    """
    logger.info(f"状态验证: type={check_type}, target={target}")

    try:
        if check_type == "file_exists":
            if os.path.exists(target):
                size = os.path.getsize(target) if os.path.isfile(target) else "目录"
                return f"✅ 验证通过：'{target}' 存在。大小: {size}"
            else:
                return f"❌ 验证失败：'{target}' 不存在。"

        elif check_type == "file_not_exists":
            if not os.path.exists(target):
                return f"✅ 验证通过：'{target}' 已不存在（已删除）。"
            else:
                return f"❌ 验证失败：'{target}' 仍然存在，删除未成功。"

        elif check_type == "command_output":
            result = subprocess.run(
                target, shell=True, capture_output=True, text=True, timeout=15
            )
            output = result.stdout.strip()
            if result.stderr:
                output += f"\n[STDERR] {result.stderr.strip()}"
            return_code = result.returncode
            status = "成功" if return_code == 0 else f"失败(code={return_code})"
            return f"命令执行{status}:\n{output[:500]}"

        elif check_type == "process_running":
            # 使用 tasklist 检查进程是否存在
            result = subprocess.run(
                f'tasklist /FI "IMAGENAME eq {target}" /NH',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if target.lower() in result.stdout.lower():
                return f"✅ 进程 '{target}' 正在运行。"
            else:
                return f"❌ 进程 '{target}' 未在运行。"

        else:
            return f"⚠️ 不支持的检查类型: {check_type}。可用类型: file_exists, file_not_exists, command_output, process_running"

    except subprocess.TimeoutExpired:
        return f"❌ 验证超时：命令执行超过 15 秒。"
    except Exception as e:
        logger.error(f"状态验证异常: {e}")
        return f"❌ 验证过程出错: {e}"
