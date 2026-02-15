import os
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from core.config import conf

# 获取项目根目录下的 temp 路径
TEMP_DIR = conf.project_root / "temp" / "voice_cache"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@tool
def convert_to_silk(input_path: str) -> str:
    """
    [转码] 将 MP3/WAV 音频转换为微信原生 SILK 格式。
    转换后的文件可作为‘原生语音条’发送。
    """
    input_file = Path(input_path)
    if not input_file.exists():
        return f"❌ 错误：找不到输入文件 {input_path}"

    # 定义输出路径
    output_silk = TEMP_DIR / f"{input_file.stem}.silk"
    # 中转采样率必须为 24000Hz 才能被微信识别
    pcm_path = TEMP_DIR / f"{input_file.stem}.pcm"

    try:
        # 1. 第一步：使用 ffmpeg 将音频转为 16bit, 24kHZ, 单声道的原始 PCM
        # [Fix v10.8] 强制 UTF-8 环境以支持 Windows 中文路径
        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", str(input_file),
            "-ar", "24000", "-ac", "1", "-f", "s16le", str(pcm_path)
        ]
        cmd_ffmpeg_str = ' '.join([f'"{s}"' for s in cmd_ffmpeg])
        subprocess.run(
            f"chcp 65001 >nul && {cmd_ffmpeg_str}", 
            shell=True, check=True, capture_output=True
        )

        # 2. 第二步：使用 silk_v3_encoder 进行编码
        # [v11.0 Neuro-Repair] 启动自愈检查
        from core.tools.env_healer import ensure_binary_environment
        ensure_binary_environment("silk_v3_encoder.exe")
        
        encoder_path = conf.project_root / "kernel" / "bin" / "silk_v3_encoder.exe" 
        
        if not encoder_path.exists():
            return "❌ [环境缺失] 无法自动补全 silk_v3_encoder.exe。请手动修复环境。"

        cmd_encoder_str = ' '.join([f'"{s}"' for s in [str(encoder_path), str(pcm_path), str(output_silk)]])
        subprocess.run(
            f"chcp 65001 >nul && {cmd_encoder_str}", 
            shell=True, check=True, capture_output=True
        )

        # 3. 清理中转文件
        if pcm_path.exists():
            os.remove(pcm_path)

        return str(output_silk.absolute())

    except Exception as e:
        return f"❌ 转码失败：{str(e)}"
