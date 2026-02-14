"""
微信消息监听器
负责监听和处理微信消息，包括文本和语音消息
"""

import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .voice_handler import VoiceMessageHandler

logger = logging.getLogger(__name__)

class WeChatListener:
    """微信消息监听器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.voice_handler = VoiceMessageHandler(data_dir / "voice_messages")
        
    def process_message(self, msg_type: str, msg_content: Any, sender: str) -> Dict[str, Any]:
        """
        处理微信消息
        
        Args:
            msg_type: 消息类型 ('text', 'voice', 'image', etc.)
            msg_content: 消息内容
            sender: 发送者
            
        Returns:
            处理结果
        """
        result = {
            "type": msg_type,
            "sender": sender,
            "processed": False,
            "response": None
        }
        
        try:
            if msg_type == "text":
                result = self._process_text_message(msg_content, sender)
            elif msg_type == "voice":
                result = self._process_voice_message(msg_content, sender)
            elif msg_type == "image":
                result = self._process_image_message(msg_content, sender)
            else:
                logger.warning(f"未处理的消息类型: {msg_type}")
                result["response"] = f"收到 {msg_type} 类型消息，暂不支持处理"
                
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)
            result["error"] = str(e)
            result["response"] = "处理消息时出现错误"
            
        return result
    
    def _process_text_message(self, text: str, sender: str) -> Dict[str, Any]:
        """处理文本消息"""
        logger.info(f"收到文本消息来自 {sender}: {text}")
        
        # 这里可以添加文本消息的处理逻辑
        # 例如：命令解析、问答等
        
        return {
            "type": "text",
            "sender": sender,
            "processed": True,
            "response": f"已收到您的文本消息: {text}"
        }
    
    def _process_voice_message(self, voice_data: bytes, sender: str) -> Dict[str, Any]:
        """处理语音消息"""
        logger.info(f"收到语音消息来自 {sender}")
        
        try:
            # 保存语音文件
            voice_path = self.voice_handler.save_voice_message(voice_data)
            
            # 这里可以添加语音识别逻辑
            # 例如：调用 recognize_speech_from_audio 工具
            
            return {
                "type": "voice",
                "sender": sender,
                "processed": True,
                "voice_path": voice_path,
                "response": f"已收到您的语音消息，保存到: {voice_path}"
            }
            
        except Exception as e:
            logger.error(f"处理语音消息时出错: {e}", exc_info=True)
            return {
                "type": "voice",
                "sender": sender,
                "processed": False,
                "error": str(e),
                "response": "处理语音消息时出现错误"
            }
    
    def _process_image_message(self, image_data: bytes, sender: str) -> Dict[str, Any]:
        """处理图片消息"""
        logger.info(f"收到图片消息来自 {sender}")
        
        # 这里可以添加图片处理逻辑
        # 例如：保存图片、OCR识别等
        
        return {
            "type": "image",
            "sender": sender,
            "processed": True,
            "response": "已收到您的图片消息"
        }
    
    def get_latest_voice_for_recognition(self) -> Optional[str]:
        """
        获取最新的语音文件用于识别
        
        Returns:
            语音文件路径，如果没有则返回 None
        """
        voice_path = self.voice_handler.get_latest_voice_file()
        if voice_path and Path(voice_path).exists():
            return voice_path
        return None