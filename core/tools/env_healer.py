import os
import sys
from pathlib import Path
from utils.logger import logger
from core.tools.binary_manager import download_and_verify_binary

def ensure_binary_environment(bin_name: str) -> bool:
    """
    [环境自愈] 检查二进制文件是否存在，若缺失则自动触发下载。
    """
    from core.config import conf
    bin_dir = conf.project_root / "kernel" / "bin"
    bin_path = bin_dir / bin_name
    
    if bin_path.exists():
        return True
        
    logger.warning(f"⚠️ [Env Healer] 检测到核心组件缺失: {bin_name}，启动自愈链路...")
    try:
        # 调用已有的 binary_manager 进行下载
        result = download_and_verify_binary.invoke(bin_name)
        if "✅" in result:
            logger.info(f"✅ [Env Healer] 组件 {bin_name} 补全成功。")
            return True
        else:
            logger.error(f"❌ [Env Healer] 自愈失败: {result}")
            # [v11.0 Neuro-Repair] 额外暴露详细错误，方便调试
            print(f"DEBUG_HEALER_ERROR: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ [Env Healer] 自愈过程发生异常: {e}")
        return False
