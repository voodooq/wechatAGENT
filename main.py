"""
AI 智能助理 — 程序入口

启动所有模块线程并保持主循环运行，
支持 Ctrl+C 优雅退出。
"""
import sys
import time
import signal
import nest_asyncio

# [v7.2 Patch] 允许在异步事件循环中进行嵌套调用
nest_asyncio.apply()

# [v11.6 Evolution] 环境自愈催化剂：强制探测并注入全局 FFmpeg 路径
try:
    from core.env_init import setup_ffmpeg_environment
    setup_ffmpeg_environment()
except Exception as e:
    print(f"环境初始化异常: {e}")

from core.config import conf
from utils.logger import logger
from utils.stability import setupGlobalExceptionHandler
from utils.self_test import get_self_test_report
from wechat.listener import WechatListener
from wechat.sender import sender
from worker.processor import MessageProcessor
from scheduler.daily_summary import DailySummaryScheduler


# 全局组件实例
listener = WechatListener()
processor = MessageProcessor()
scheduler = DailySummaryScheduler()


def _printBanner():
    """打印启动横幅 (v10.0 Evolution)"""
    banner = """
╔══════════════════════════════════════════════╗
║           🤖 IronSentinel v10.0              ║
║                                              ║
║   开源进化 | 自我维护 | 物理隔离 | 守护运行   ║
╚══════════════════════════════════════════════╝
    """
    print(banner)


def _printConfig():
    """打印当前配置 (v10.3)"""
    provider = getattr(conf, 'llm_provider', 'google').capitalize()
    logger.info(f"AI驱动: {provider} ({conf.model_name})")
    logger.info(f"微信白名单: {conf.whitelist}")
    logger.info(f"数据库路径: {conf.db_full_path}")


def _gracefulShutdown(signum, frame):
    """优雅退出处理"""
    logger.info("收到退出信号，正在优雅关闭...")
    listener.stop()
    processor.stop()
    scheduler.stop()
    logger.info("所有模块已停止，程序退出")
    sys.exit(0)


import json
import os

def _checkEvolutionReports():
    """检查并发送演化完成报告"""
    pending_file = os.path.join(conf.project_root, "data", "evolution_pending.json")
    if os.path.exists(pending_file):
        try:
            with open(pending_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            reason = data.get("reason", "未知修复")
            timestamp = data.get("timestamp", "刚刚")
            target_user = data.get("target_user", conf.master_remark)
            
            report = (
                f"🧬 **IronSentinel 演化成功通知**\n"
                f"--------------------------------\n"
                f"ℹ️ 演化内容: {reason}\n"
                f"⏰ 完成时间: {timestamp}\n"
                f"🚀 状态: 系统已成功热重载并恢复运行。\n"
                f"--------------------------------\n"
                f"您的 AI 助手已变得更加强大。"
            )
            
            sender.sendMessage(target_user, report)
            logger.info(f"✅ 演化汇报已发送给主人: {reason}")
            
            # 及时清理，防止重复发送
            os.remove(pending_file)
        except Exception as e:
            logger.error(f"处理演化汇报失败: {e}")

def main():
    """程序主入口"""
    # [v10.9] 权限守卫：确保具备跨目录访问权限 (如访问 Lenove 用户文档)
    try:
        from kernel.privilege_guard import request_admin
        request_admin()
    except Exception as e:
        logger.warning(f"权限提权跳过或失败: {e}")
        
    _printBanner()

    # 安装全局异常处理
    setupGlobalExceptionHandler()

    # 注册退出信号
    signal.signal(signal.SIGINT, _gracefulShutdown)
    signal.signal(signal.SIGTERM, _gracefulShutdown)

    # 打印配置信息
    _printConfig()

    # [Fix v10.2.5] 检查必要配置 (动态按驱动校验)
    provider = getattr(conf, 'llm_provider', 'google').lower()
    key_mapping = {
        "google": ("GOOGLE_API_KEY", conf.GOOGLE_API_KEY),
        "openai": ("OPENAI_API_KEY", conf.OPENAI_API_KEY),
        "anthropic": ("ANTHROPIC_API_KEY", conf.ANTHROPIC_API_KEY),
        "deepseek": ("DEEPSEEK_API_KEY", conf.DEEPSEEK_API_KEY),
        "openai-compatible": ("OPENAI_API_KEY", conf.OPENAI_API_KEY)
    }
    
    env_name, key_val = key_mapping.get(provider, ("API_KEY", None))
    if not key_val:
        logger.error(f"⚠️ 供应商 [{provider}] 的核心配置项 {env_name} 未配置，请在 .env 文件中设置后重启")
        sys.exit(1)

    # 按依赖顺序启动模块
    try:
        logger.info("=" * 50)
        logger.info("启动微信监听器...")
        listener.start()

        logger.info("启动消息处理器...")
        processor.start()

        logger.info("启动每日摘要调度器...")
        scheduler.start()

        logger.info("=" * 50)
        logger.info("✅ 所有模块启动完成，等待消息...")
        
        # 1. 发送常规自检报告
        try:
            time.sleep(3) # 给微信窗口一点初始化时间
            report = get_self_test_report()
            sender.sendMessage(conf.master_remark, report)
            logger.info(f"🚀 已向主人 [{conf.master_remark}] 发送启动自检报告")
        except Exception as e:
            logger.error(f"发送自检报告失败: {e}")

        # 2. [NEW] 检查并发送演化回报 (如果是因为进化而重启的)
        _checkEvolutionReports()

        logger.info("按 Ctrl+C 退出")

        # 主线程保活
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        _gracefulShutdown(None, None)


if __name__ == "__main__":
    main()
