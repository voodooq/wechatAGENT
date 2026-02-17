"""
AI 智能助理 — 程序入口

启动所有模块线程并保持主循环运行，
支持 Ctrl+C 优雅退出。
"""
import sys
import time
import signal
import nest_asyncio
nest_asyncio.apply()

from core.config import conf

# [v11.6 Evolution] 环境自愈催化剂：强制探测并注入全局 FFmpeg 路径
try:
    from core.env_init import setup_ffmpeg_environment
    setup_ffmpeg_environment()
except Exception as e:
    print(f"环境初始化异常: {e}")

from utils.logger import logger

from utils.stability import setupGlobalExceptionHandler
from utils.self_test import get_self_test_report
from wechat.listener import WechatListener
from wechat.sender import sender
from worker.processor import MessageProcessor
from scheduler.daily_summary import DailySummaryScheduler


def main():
    # Setup exception handler
    setupGlobalExceptionHandler()
    pass

if __name__ == "__main__":
    main()











# 全局组件实例
listener = WechatListener()
processor = MessageProcessor()
scheduler = DailySummaryScheduler()


def _printBanner():
    """打印启动横幅 (v13.0 Evolution)"""
    banner = """
╔══════════════════════════════════════════════╗
║           🤖 IronSentinel v13.0              ║
║                                              ║
║   开源进化 | 自我维护 | 物理隔离 | 守护运行  ║
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
import time
from datetime import datetime, timedelta

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
            # 即使失败也清理文件，防止无限重试
            if os.path.exists(pending_file):
                os.remove(pending_file)

def _should_send_self_test_report() -> bool:
    """
    判断是否应该发送自检报告
    
    规则：
    1. 如果从未发送过自检报告，返回 True
    2. 如果上次发送时间超过 24 小时，返回 True  
    3. 否则返回 False（避免重复发送）
    
    使用 audit_logs 表中的记录来判断
    """
    try:
        from core.audit import audit_logger
        from datetime import datetime, timedelta
        
        # 查询最近的自检报告记录
        with audit_logger._get_db_conn() as conn:
            cursor = conn.cursor()
            # 查找包含自检报告关键词的记录
            cursor.execute(
                "SELECT timestamp FROM audit_logs WHERE command LIKE '%自检报告%' AND status = 'SUCCESS' ORDER BY timestamp DESC LIMIT 1"
            )
            result = cursor.fetchone()
            
            if result is None:
                # 从未发送过自检报告
                return True
                
            # 解析时间戳
            last_timestamp_str = result[0]
            # SQLite 时间戳格式: YYYY-MM-DD HH:MM:SS
            last_timestamp = datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # 计算时间差
            now = datetime.now()
            time_diff = now - last_timestamp
            
            # 如果超过 24 小时，重新发送
            return time_diff > timedelta(hours=24)
            
    except Exception as e:
        logger.warning(f"检查自检报告发送状态时出错: {e}")
        # 出错时保守地允许发送
        return True

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

    # [Fix v10.2.5] 配置验证
    if not conf.validate():
        logger.error("❌ 配置验证失败，请修正配置后重启程序")
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
        
        # 1. 发送常规自检报告（仅在需要时）
        try:
            # 检查是否需要发送自检报告
            if _should_send_self_test_report():
                time.sleep(3) # 给微信窗口一点初始化时间
                report = get_self_test_report()
                sender.sendMessage(conf.master_remark, report)
                logger.info(f"🚀 已向主人 [{conf.master_remark}] 发送启动自检报告")
            else:
                logger.info("📋 跳过自检报告发送（最近已发送过）")
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