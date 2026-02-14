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
        获取最新的语音文件路径 (v10.8 增强寻路方案)
        
        Returns:
            最新的语音文件路径，如果没有则返回空字符串
        """
        try:
            # 1. 调用定位引擎锁定物理路径
            from core.tools.wechat_locator import get_wechat_storage_path
            target_base = get_wechat_storage_path.invoke({})
            
            if "❌" in target_base:
                logger.warning(f"深度寻路引擎未能返回有效路径: {target_base}")
                # 降级：使用旧的 data_dir 搜索
                voice_files = list(self.data_dir.glob("voice_*.silk"))
                if not voice_files: return ""
                return str(max(voice_files, key=lambda f: f.stat().st_mtime))

            # 2. 执行定向精准探测 (dir /o-d /s /b)
            # 这能发现由于微信版本差异可能隐藏在不同层级的 .silk 文件
            logger.info(f"🧬 [v10.8] 正在精准探测微信语音流: {target_base}")
            from core.tools.binary_manager import BIN_DIR # 借助已有 PATH
            
            # 使用 PowerShell 指令获取最新文件
            import subprocess
            cmd = f'powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-ChildItem -Path \'{target_base}\' -Filter *.silk -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"'
            
            try:
                latest_path = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()
                if latest_path and os.path.exists(latest_path):
                    logger.info(f"✅ [Surgery] 成功捞取最新语音流: {latest_path}")
                    return latest_path
            except Exception as e:
                logger.error(f"PowerShell 深度探测失败: {e}")

            # 最后的残余搜寻逻辑
            return ""
        except Exception as e:
            logger.error(f"寻路逻辑整体异常: {e}")
            return ""
    
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