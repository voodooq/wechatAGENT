import os
import time
from typing import Dict
from langchain_core.tools import tool
from utils.logger import logger

@tool
def one_click_voice_process() -> str:
    """
    一键处理最新语音消息
    自动识别当前微信账号→定位语音目录→处理最新语音→返回TTS回应
    """
    try:
        logger.info("🚀 启动一键语音处理...")
        
        # 调用自动语音处理工具
        from core.tools.auto_voice_processor import auto_process_latest_voice
        result = auto_process_latest_voice.invoke({"scout_seconds": 60})
        
        logger.info("✅ 一键语音处理完成")
        return result
        
    except Exception as e:
        logger.error(f"一键语音处理失败: {e}")
        return f"❌ 处理失败: {str(e)}"

@tool
def quick_voice_check() -> str:
    """
    快速检查语音系统状态和最新语音
    """
    try:
        result = "🔍 语音系统快速检查\n" + "=" * 25 + "\n"
        
        # 检查系统状态
        from core.tools.auto_voice_processor import get_voice_system_status
        status = get_voice_system_status.invoke({})
        result += status + "\n\n"
        
        # 检查当前账号和语音目录
        from core.tools.enhanced_wechat_locator import get_current_wechat_context
        context = get_current_wechat_context.invoke({})
        result += context + "\n\n"
        
        # 尝试查找最新语音（不进行完整处理）
        from core.tools.auto_voice_processor import _auto_voice_processor
        account_info = _auto_voice_processor._auto_identify_current_account()
        
        if account_info.get('success'):
            voice_dir = _auto_voice_processor._locate_voice_directory(account_info['account_path'])
            if voice_dir:
                latest_voice = _auto_voice_processor._find_latest_voice_file(voice_dir, 300)  # 5分钟内
                if latest_voice:
                    time_diff = int(time.time() - latest_voice.stat().st_mtime)
                    result += f"🔊 最新语音: {os.path.basename(latest_voice)} ({time_diff}秒前)\n"
                else:
                    result += "🔇 最近5分钟内无新语音\n"
            else:
                result += "❌ 未找到语音目录\n"
        else:
            result += "❌ 无法识别当前账号\n"
            
        return result
        
    except Exception as e:
        logger.error(f"快速检查失败: {e}")
        return f"❌ 检查失败: {str(e)}"