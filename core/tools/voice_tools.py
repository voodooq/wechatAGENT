"""
语音消息处理工具
"""

import os
import logging
from pathlib import Path
from ..voice_handler import VoiceMessageHandler
from ..config import VOICE_MESSAGES_DIR

logger = logging.getLogger(__name__)

def process_voice_message(voice_file_path=None, user_name="文件传输助手"):
    """
    处理语音消息的主函数
    
    Args:
        voice_file_path: 语音文件路径（可选，如果为None则尝试自动查找）
        user_name: 发送者名称
        
    Returns:
        tuple: (识别结果文本, 是否成功)
    """
    try:
        # 初始化语音处理器
        voice_handler = VoiceMessageHandler()
        
        # 如果提供了文件路径，保存它
        if voice_file_path and os.path.exists(voice_file_path):
            saved_path = voice_handler.save_voice_message(voice_file_path, user_name)
            logger.info(f"已保存语音消息: {saved_path}")
        else:
            # 尝试获取最新的语音消息
            saved_path = voice_handler.get_latest_voice_message(user_name)
            if not saved_path:
                logger.warning(f"未找到{user_name}的语音消息")
                return "未找到语音消息文件，请确保已发送语音消息。", False
        
        # 识别语音内容 (使用绝对导入或从 tools.default 导入)
        from tools.default import recognize_speech_from_audio
        recognition_result = recognize_speech_from_audio(audio_file_path=saved_path)
        
        if recognition_result.get("status") == "success":
            text = recognition_result.get("text", "")
            logger.info(f"语音识别成功: {text}")
            
            # 移动已处理的文件
            voice_handler.move_to_processed(saved_path)
            
            return text, True
        else:
            error_msg = recognition_result.get("message", "语音识别失败")
            logger.error(f"语音识别失败: {error_msg}")
            return f"语音识别失败: {error_msg}", False
            
    except Exception as e:
        logger.error(f"处理语音消息时发生错误: {e}")
        return f"处理语音消息时发生错误: {str(e)}", False

def auto_detect_voice_messages():
    """
    自动检测并处理语音消息
    
    Returns:
        list: 处理结果列表
    """
    results = []
    
    try:
        voice_handler = VoiceMessageHandler()
        
        # 获取所有用户的语音消息
        received_dir = VOICE_MESSAGES_DIR / "received"
        if not received_dir.exists():
            return results
        
        # 查找所有语音文件
        voice_files = []
        for ext in ['.silk', '.amr', '.mp3', '.m4a', '.wav']:
            voice_files.extend(received_dir.glob(f"*{ext}"))
        
        for voice_file in voice_files:
            # 从文件名提取用户信息
            file_name = voice_file.name
            if "voice_" in file_name:
                parts = file_name.split("_")
                if len(parts) >= 2:
                    user = parts[1]
                else:
                    user = "unknown"
            else:
                user = "unknown"
            
            # 处理语音消息
            text, success = process_voice_message(str(voice_file), user)
            
            results.append({
                "file": str(voice_file),
                "user": user,
                "text": text,
                "success": success
            })
            
            if success:
                logger.info(f"自动处理语音消息成功: {user} - {text[:50]}...")
            else:
                logger.warning(f"自动处理语音消息失败: {user}")
    
    except Exception as e:
        logger.error(f"自动检测语音消息时发生错误: {e}")
    
    return results