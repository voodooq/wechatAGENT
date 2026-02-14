"""
消息处理器 - 处理各种类型的消息
"""

import logging
import os
from typing import Dict, Any
from .voice_handler import VoiceHandler

logger = logging.getLogger(__name__)

class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        self.voice_handler = VoiceHandler()
    
    def handle_message(self, msg_type: str, content: Any, **kwargs) -> str:
        """
        处理消息
        Args:
            msg_type: 消息类型 ('text', 'voice', 'image', 'file')
            content: 消息内容
            **kwargs: 其他参数
        Returns:
            处理结果
        """
        try:
            if msg_type == 'text':
                return self._handle_text(content, **kwargs)
            elif msg_type == 'voice':
                return self._handle_voice(content, **kwargs)
            elif msg_type == 'image':
                return self._handle_image(content, **kwargs)
            elif msg_type == 'file':
                return self._handle_file(content, **kwargs)
            else:
                return f"不支持的消息类型: {msg_type}"
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            return f"消息处理失败: {str(e)}"
    
    def _handle_text(self, text: str, **kwargs) -> str:
        """处理文本消息"""
        # 这里可以添加文本消息的处理逻辑
        return f"收到文本消息: {text}"
    
    def _handle_voice(self, voice_file_path: str, **kwargs) -> str:
        """处理语音消息"""
        try:
            # 分析语音消息
            analysis = self.voice_handler.analyze_voice_message(voice_file_path)
            
            if not analysis["exists"]:
                return "语音文件不存在"
            
            # 构建回复
            response = f"🎤 收到语音消息\n"
            response += f"📊 时长: {analysis['duration']:.1f}秒\n"
            response += f"📁 格式: {analysis['format']}\n"
            response += f"📦 大小: {analysis['size'] / 1024:.1f}KB\n\n"
            
            if analysis["text"]:
                response += f"🗣️ 识别内容: {analysis['text']}"
            else:
                response += "⚠️ 语音内容识别失败或语音过短"
            
            return response
            
        except Exception as e:
            logger.error(f"语音消息处理失败: {e}")
            return f"语音消息处理失败: {str(e)}"
    
    def _handle_image(self, image_file_path: str, **kwargs) -> str:
        """处理图片消息"""
        # 这里可以添加图片处理逻辑
        return f"收到图片消息: {image_file_path}"
    
    def _handle_file(self, file_path: str, **kwargs) -> str:
        """处理文件消息"""
        # 这里可以添加文件处理逻辑
        return f"收到文件: {file_path}"
    
    def detect_message_type(self, content: Any) -> str:
        """检测消息类型"""
        if isinstance(content, str):
            # 检查是否是文件路径
            if os.path.exists(content):
                ext = os.path.splitext(content)[1].lower()
                if ext in self.voice_handler.supported_formats:
                    return 'voice'
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    return 'image'
                else:
                    return 'file'
            else:
                return 'text'
        else:
            return 'unknown'