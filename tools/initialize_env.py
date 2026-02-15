import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.getcwd())

from core.tools.binary_manager import download_and_verify_binary
from utils.logger import logger

def initialize_environment():
    """
    [初始化] 一键建立 IronSentinel 运行环境。
    """
    logger.info("🚀 开始 IronSentinel v11.0 环境初始化自愈...")
    
    binaries = ["silk_v3_decoder.exe", "silk_v3_encoder.exe", "ffmpeg.exe"]
    
    success_count = 0
    for bin_name in binaries:
        try:
            # 调用 binary_manager 工具进行下载和校验
            result = download_and_verify_binary.invoke(bin_name)
            if "✅" in result:
                logger.info(f"   {result}")
                success_count += 1
            else:
                logger.error(f"   {result}")
        except Exception as e:
            logger.error(f"   ❌ 初始化 {bin_name} 时发生异常: {e}")

    if success_count == len(binaries):
        logger.info("🎉 所有核心组件已就绪。")
    else:
        logger.warning(f"⚠️ 环境初始化部分成功 ({success_count}/{len(binaries)})，请检查网络连接。")

if __name__ == "__main__":
    initialize_environment()
