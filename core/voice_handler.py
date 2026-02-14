"""
语音消息处理模块
负责接收、保存和识别微信语音消息
"""

import os
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VoiceMessageHandler:
    """语音消息处理器"""
    
    def __init__(self, data_dir: str = "data/voice_messages"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def save_voice_message(self, voice_data: bytes, file_extension: str = "silk") -> str:
        """
        保存语音消息到本地文件
        
        Args:
            voice_data: 语音数据字节
            file_extension: 文件扩展名
            
        Returns:
            保存的文件路径
        """
        # 生成文件名：voice_年月日_时分秒_序号.silk
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 查找当前时间戳下的最大序号
        existing_files = list(self.data_dir.glob(f"voice_{timestamp}_*.{file_extension}"))
        if existing_files:
            max_num = max(int(f.stem.split('_')[-1]) for f in existing_files)
            sequence = max_num + 1
        else:
            sequence = 1
            
        filename = f"voice_{timestamp}_{sequence}.{file_extension}"
        file_path = self.data_dir / filename
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(voice_data)
            
        logger.info(f"语音消息已保存: {file_path}")
        return str(file_path)
    
    def get_latest_voice_file(self) -> str:
        """
        获取最新的语音文件路径
        
        Returns:
            最新的语音文件路径，如果没有则返回空字符串
        """
        voice_files = list(self.data_dir.glob("voice_*.silk"))
        if not voice_files:
            return ""
            
        # 按修改时间排序，获取最新的文件
        latest_file = max(voice_files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        清理旧的语音文件
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for voice_file in self.data_dir.glob("voice_*.silk"):
            file_age = current_time - voice_file.stat().st_mtime
            if file_age > max_age_seconds:
                voice_file.unlink()
                logger.info(f"已清理旧语音文件: {voice_file}")