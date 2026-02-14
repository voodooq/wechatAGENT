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
        获取最新的语音文件路径 (v10.9 Omni-Path 方案)
        
        Returns:
            最新的语音文件路径，如果没有则返回空字符串
        """
        try:
            # 1. 调用雷达定位引擎精确锁定物理路径
            from core.tools.wechat_locator import ultra_wechat_locator
            target_base = ultra_wechat_locator.invoke({})
            
            if "❌" in target_base:
                logger.warning(f"路径雷达未能锁定目标: {target_base}")
                # 降级：使用旧的 data_dir 搜索
                voice_files = list(self.data_dir.glob("voice_*.silk"))
                if not voice_files: return ""
                return str(max(voice_files, key=lambda f: f.stat().st_mtime))

            # 2. 执行定向精准探测 (寻找 .silk 或可能的加密 .dat)
            import subprocess
            cmd = f'powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-ChildItem -Path \'{target_base}\' -Filter *.silk -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"'
            
            try:
                latest_path = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()
                if latest_path and os.path.exists(latest_path):
                    logger.info(f"✅ [Radar] 成功截获最新音频流: {latest_path}")
                    
                    # [v10.9 Extension] 如果文件是加密的 .dat，尝试自动解密
                    if latest_path.lower().endswith(".dat"):
                        from core.tools.wechat_decryptor import decrypt_wechat_dat
                        decrypted = decrypt_wechat_dat.invoke({"file_path": latest_path})
                        if not decrypted.startswith("❌"):
                            logger.info(f"🔓 [Auto-Decrypt] 媒体流已解密: {decrypted}")
                            return decrypted
                            
                    return latest_path
            except Exception as e:
                logger.error(f"PowerShell 探测链路异常: {e}")

            return ""
        except Exception as e:
            logger.error(f"语音寻路逻辑中断: {e}")
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