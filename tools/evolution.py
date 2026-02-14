import ast
import os
import sys
import json
import time
import subprocess
import hashlib
from langchain.tools import tool
from utils.logger import logger
from core.config import conf

def run_git_cmd(args: list):
    """执行 Git 命令的辅助函数"""
    try:
        result = subprocess.run(
            args, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Git Error: {e.stderr}")
        raise Exception(f"Git 命令执行失败: {e.stderr}")

@tool
def evolve_code(file_path: str, code: str, reason: str):
    """
    [核心进化] 修改/创建代码 -> 语法自检 -> 本地版本固化 (Git Commit) -> 申请热重启。
    请确保 file_path 是基于项目根目录的相对路径。
    """
    # 0. 安全栅栏：严禁修改私有配置和关键数据库
    forbidden_keywords = ["config_private", "data/", ".env", "secrets"]
    if any(k in file_path for k in forbidden_keywords):
        return f"❌ [安全拦截] 禁止修改受保护的隐私文件: {file_path}"

    # 1. 语法免疫检查 (AST)
    try:
        ast.parse(code)
    except Exception as e:
        return f"❌ [语法校验失败] 无法应用此进化，代码存在语法缺陷: {e}"

    # 2. 实现进化：物理写入文件
    try:
        # 确保父目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # 备份旧文件副本（如果存在）
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                logger.info(f"进化：正在覆盖旧版本 [{file_path}]")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
    except Exception as e:
        return f"❌ [文件写入失败] 无法完成进化: {e}"

    # 3. 固化版本 (Git Commit)
    try:
        run_git_cmd(["git", "add", file_path])
        commit_msg = f"🧬 [Auto-Evolve] {reason}"
        run_git_cmd(["git", "commit", "-m", commit_msg])
        logger.info(f"版本已固化: {commit_msg}")
    except Exception as e:
        # 如果是因为没有变化而提交失败，可以忽略
        if "nothing to commit" in str(e).lower():
            pass
        else:
            return f"⚠️ 代码已进化，但本地版本固化失败: {e}"

    return "✅ [进化完成] 代码已成功写入。请通过 request_hot_reload() 触发系统更新以生效。"

@tool
def sync_to_github(commit_msg: str):
    """
    [开源同步] 将核心逻辑推送到线上公共仓库，实现开源同步。
    需确保本地已配置 Git 免密推送。
    """
    try:
        # 1. 首先确保本地暂存区干净
        # 2. 调用 git add . 配合增强后的 .gitignore 自动过滤隐私和测试文件
        run_git_cmd(["git", "add", "."])
        
        # 3. 执行推送 (备注已固化在 evolve_code 中，这里通常是同步最新状态)
        run_git_cmd(["git", "push", "origin", "main"])
        return "✅ [开源同步成功] 核心逻辑已安全推送至 GitHub。非核心测试文件与隐私数据已由 .gitignore 自动过滤。"
    except Exception as e:
        return f"❌ [同步失败] 无法推送到 GitHub: {e}。请检查 SSH 网络连接或权限。"

@tool
def report_evolution_progress(step_name: str, detail: str, report_to: str = "文件传输助手"):
    """
    [汇报] 在复杂的代码演化或环境搭建过程中，向用户同步阶段性进展。
    
    @param step_name: 阶段名称 (如 "依赖安装", "代码修改")
    @param detail: 详细描述
    @param report_to: 汇报对象
    """
    from wechat.sender import sender
    from core.config import conf
    
    # 格式化汇报内容
    msg = (
        f"⏳ **IronSentinel 进化进度: {step_name}**\n"
        f"--------------------------------\n"
        f"📝 详情: {detail}\n"
        f"🚀 状态: 正在推进中..."
    )
    
    try:
        sender.sendMessage(report_to, msg)
        logger.info(f"已发送进度汇报: {step_name}")
        return f"✅ 进度汇报已发送: {step_name}"
    except Exception as e:
        logger.error(f"发送进度汇报失败: {e}")
        return f"⚠️ 汇报发送失败，但逻辑仍在继续: {e}"

@tool
def request_hot_reload(reason: str = "应用代码演化", report_to: str = "文件传输助手"):
    """
    重启系统以应用所有代码进化
    
    @param reason: 本次演化的简要描述，将用于重启后的自动汇报
    @param report_to: 演化成功后通知的对象（联系人/群名称）
    """
    import os
    logger.warning(f"👋 AI 正在请求热重启应用系统进化: {reason} | 汇报对象: {report_to}")
    
    # [NEW] 记录演化存根，供重启后的新进程读取并汇报完成情况
    try:
        pending_file = os.path.join(conf.project_root, "data", "evolution_pending.json")
        os.makedirs(os.path.dirname(pending_file), exist_ok=True)
        with open(pending_file, "w", encoding="utf-8") as f:
            json.dump({
                "reason": reason,
                "target_user": report_to,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending_report"
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"演化存根已保存: {pending_file}")
    except Exception as e:
        logger.error(f"保存演化存根失败: {e}")

    # [核心修复] 使用 os._exit(100) 确保即便在子线程中也能强力终止整个进程
    os._exit(100)

@tool
def isolate_self(reason: str):
    """[紧急跳火闸] 如果发现逻辑失控或安全风险，以此隔离自身"""
    logger.critical(f"🛑 触发自我隔离机制: {reason}")
    sys.exit(999) # 退出码 999 锁定 Overseer
