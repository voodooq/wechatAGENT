import os
import sys
import shutil
from pathlib import Path
from utils.logger import logger

def setup_ffmpeg_environment():
    """
    [环境催化剂] 自动定位 FFmpeg 并注入当前进程环境变量。
    优先顺序：项目 bin 目录 > 系统 PATH > 常见安装路径。
    """
    # 1. 定义潜在的藏身之处
    project_root = Path(os.getcwd())
    potential_bins = [
        project_root / "kernel" / "bin",   # 你的私有工具包
        project_root / "bin",              # 备用 bin
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "ffmpeg" / "bin",
        Path("C:\\ffmpeg\\bin")            # 常见的 Windows 手动安装路径
    ]

    ffmpeg_dir = None

    # 2. 检查系统 PATH 是否已经配置 (shutil.which 是最快的方式)
    existing_path = shutil.which("ffmpeg")
    if existing_path:
        logger.info(f"✅ [Env Catalyst] FFmpeg 已在系统环境变量中: {existing_path}")
        return True

    # 3. 开启“地毯式”搜索
    for folder in potential_bins:
        if folder.exists() and (folder / "ffmpeg.exe").exists():
            ffmpeg_dir = str(folder.absolute())
            break

    # 4. 动态注入环境变量
    if ffmpeg_dir:
        # 关键操作：将路径添加到当前进程的 PATH 开头
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        logger.info(f"🚀 [Env Catalyst] 已动态注入 FFmpeg 路径: {ffmpeg_dir}")
        
        # 验证注入是否成功
        if shutil.which("ffmpeg"):
            return True
    
    logger.warning("❌ [Env Catalyst] 未能在本地或常见路径找到 FFmpeg，语音功能可能会受限。")
    return False

if __name__ == "__main__":
    setup_ffmpeg_environment()
