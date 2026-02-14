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
        # 这是转码为 SILK v3 的标准前置要求
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_file),
            "-ar", "24000", "-ac", "1", "-f", "s16le", str(pcm_path)
        ], check=True, capture_output=True)

        # 2. 第二步：使用 silk_v3_encoder 进行编码
        # 注意：此处假设环境中有 encoder 程序的路径
        encoder_path = conf.project_root / "kernel" / "bin" / "silk_v3_encoder.exe" 
        
        if not encoder_path.exists():
            # 兼容性检查：尝试 tools/bin
            alt_path = conf.project_root / "tools" / "bin" / "silk_v3_encoder.exe"
            if alt_path.exists():
                encoder_path = alt_path
            else:
                return "❌ [环境缺失] 找不到 silk_v3_encoder.exe。请先提供此工具。"

        subprocess.run([str(encoder_path), str(pcm_path), str(output_silk)], check=True, capture_output=True)

        # 3. 清理中转文件
        if pcm_path.exists():
            os.remove(pcm_path)

        return str(output_silk.absolute())

    except Exception as e:
        return f"❌ 转码失败：{str(e)}"
