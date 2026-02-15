import os
from pathlib import Path
from utils.logger import logger

def patch_silk_header(file_path: str) -> str:
    """
    [自愈] 微信语音头部修复函数。
    确保所有 .silk/.aud 文件具备标准的 #!SILK_V3 头部。
    微信 PC 端录制的语音往往缺失该魔数，导致 ffmpeg 或解码器报错。
    """
    SILK_MAGIC = b'#!SILK_V3'
    
    target = Path(file_path)
    if not target.exists():
        logger.error(f"❌ [Healer] 找不到文件: {file_path}")
        return file_path

    try:
        # 1. 读取原始数据
        with open(target, 'rb') as f:
            original_data = f.read()

        # 2. 检查头部是否已经存在
        if original_data.startswith(SILK_MAGIC):
            return str(target.absolute())

        # 3. 执行头部补全
        logger.info(f"🧬 [Healer] 正在为 {target.name} 注入 SILK 魔数头部...")
        fixed_data = SILK_MAGIC + original_data
        
        # 4. 写回原文件 (原始文件缺失头部无法被直接使用)
        with open(target, 'wb') as f:
            f.write(fixed_data)
            
        return str(target.absolute())

    except Exception as e:
        logger.error(f"❌ [Healer] 二进制修复失败: {e}")
        return file_path
