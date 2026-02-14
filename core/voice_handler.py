"""
语音处理模块 - 处理微信语音消息
"""

import os
import tempfile
import json
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class VoiceHandler:
    """处理语音消息的类"""
    
    def __init__(self):
        self.supported_formats = ['.silk', '.amr', '.mp3', '.m4a', '.wav']
        
    def process_wechat_voice(self, voice_file_path: str) -> str:
        """
        处理微信语音消息
        Args:
            voice_file_path: 语音文件路径
        Returns:
            识别出的文本内容
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(voice_file_path):
                return "语音文件不存在"
            
            # 获取文件扩展名
            ext = os.path.splitext(voice_file_path)[1].lower()
            
            # 如果是微信 SILK 格式，需要先转换
            if ext == '.silk':
                return self._process_silk_voice(voice_file_path)
            else:
                # 其他格式直接识别
                return self._recognize_speech(voice_file_path)
                
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            return f"语音识别失败: {str(e)}"
    
    def _process_silk_voice(self, silk_file_path: str) -> str:
        """处理微信 SILK 格式语音"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_file = tmp.name
            
            # 使用 ffmpeg 转换 SILK 到 WAV
            # 注意：需要安装 ffmpeg
            cmd = ['ffmpeg', '-i', silk_file_path, '-ar', '16000', '-ac', '1', wav_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"SILK 转换失败: {result.stderr}"
            
            # 识别转换后的 WAV 文件
            text = self._recognize_speech(wav_file)
            
            # 清理临时文件
            os.unlink(wav_file)
            
            return text
            
        except Exception as e:
            logger.error(f"SILK 处理失败: {e}")
            return f"SILK 格式处理失败: {str(e)}"
    
    def _recognize_speech(self, audio_file_path: str) -> str:
        """识别语音文件内容"""
        try:
            # 这里可以使用现有的语音识别工具
            # 暂时返回占位符，实际实现需要集成语音识别API
            return "语音识别功能已启用，但需要配置语音识别服务"
            
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return f"语音识别失败: {str(e)}"
    
    def get_voice_duration(self, voice_file_path: str) -> float:
        """获取语音时长（秒）"""
        try:
            if not os.path.exists(voice_file_path):
                return 0.0
            
            # 使用 ffprobe 获取音频时长
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                   voice_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"获取语音时长失败: {e}")
            return 0.0