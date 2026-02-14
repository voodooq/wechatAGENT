"""
语音消息处理模块 v1.0
负责接收、存储、识别和回复语音消息
"""

import os
import time
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VoiceMessageHandler:
    """语音消息处理器"""
    
    def __init__(self, base_dir="data/voice_messages"):
        """
        初始化语音处理器
        
        Args:
            base_dir: 语音文件存储基础目录
        """
        self.base_dir = Path(base_dir)
        self.ensure_directories()
        
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.base_dir,
            self.base_dir / "received",
            self.base_dir / "processed",
            self.base_dir / "tts_output"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保目录存在: {directory}")
    
    def save_voice_message(self, voice_file_path, user_name="unknown"):
        """
        保存接收到的语音消息
        
        Args:
            voice_file_path: 原始语音文件路径
            user_name: 发送者名称
            
        Returns:
            str: 保存后的文件路径
        """
        if not os.path.exists(voice_file_path):
            raise FileNotFoundError(f"语音文件不存在: {voice_file_path}")
        
        # 生成唯一文件名
        timestamp = int(time.time())
        file_ext = Path(voice_file_path).suffix
        new_filename = f"voice_{user_name}_{timestamp}{file_ext}"
        
        # 目标路径
        target_path = self.base_dir / "received" / new_filename
        
        # 复制文件
        shutil.copy2(voice_file_path, target_path)
        logger.info(f"语音消息已保存: {target_path}")
        
        return str(target_path)
    
    def get_latest_voice_message(self, user_name=None):
        """
        获取最新的语音消息文件
        
        Args:
            user_name: 可选，指定用户
            
        Returns:
            str: 最新的语音文件路径，或None
        """
        received_dir = self.base_dir / "received"
        
        if not received_dir.exists():
            return None
        
        # 获取所有语音文件
        voice_files = []
        for ext in ['.silk', '.amr', '.mp3', '.m4a', '.wav']:
            voice_files.extend(received_dir.glob(f"*{ext}"))
        
        if not voice_files:
            return None
        
        # 按修改时间排序
        voice_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 如果指定用户，过滤用户文件
        if user_name:
            user_files = [f for f in voice_files if user_name in f.name]
            if user_files:
                return str(user_files[0])
            return None
        
        return str(voice_files[0])
    
    def move_to_processed(self, voice_file_path):
        """
        将处理完成的语音文件移动到processed目录
        
        Args:
            voice_file_path: 语音文件路径
        """
        if not os.path.exists(voice_file_path):
            return
        
        file_name = Path(voice_file_path).name
        target_path = self.base_dir / "processed" / file_name
        
        try:
            shutil.move(voice_file_path, target_path)
            logger.info(f"语音文件已移动到processed: {target_path}")
        except Exception as e:
            logger.error(f"移动语音文件失败: {e}")
    
    def save_tts_audio(self, audio_data, user_name="unknown", format="mp3"):
        """
        保存TTS生成的音频文件
        
        Args:
            audio_data: 音频数据
            user_name: 接收者名称
            format: 音频格式
            
        Returns:
            str: 保存的文件路径
        """
        timestamp = int(time.time())
        filename = f"tts_{user_name}_{timestamp}.{format}"
        file_path = self.base_dir / "tts_output" / filename
        
        # 这里需要根据实际的音频数据格式进行保存
        # 暂时返回路径，实际保存逻辑需要根据TTS模块实现
        return str(file_path)
    
    def cleanup_old_files(self, max_age_hours=24):
        """
        清理旧文件
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for subdir in ["received", "processed", "tts_output"]:
            dir_path = self.base_dir / subdir
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            logger.info(f"清理旧文件: {file_path}")
                        except Exception as e:
                            logger.error(f"清理文件失败 {file_path}: {e}")