import os
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from core.config import conf
from utils.logger import logger

# 获取项目根目录下的 temp 路径
TEMP_DIR = conf.project_root / "temp" / "voice_cache"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@tool
def decode_silk_to_wav(silk_path: str) -> str:
    """
    [解码] 将微信原生加密 SILK 语音转为标准 WAV (24kHZ)。
    含环境自诊：若缺少解码器将自动触发自愈任务。
    """
    silk_file = Path(silk_path)
    if not silk_file.exists():
        return f"❌ 错误：找不到语音文件 {silk_path}"

    wav_path = TEMP_DIR / f"{silk_file.stem}_decoded.wav"
    pcm_path = TEMP_DIR / f"{silk_file.stem}.pcm"

    try:
        # 1. 环境自检与自愈
        decoder_path = conf.project_root / "kernel" / "bin" / "silk_v3_decoder.exe"
        if not decoder_path.exists():
            from core.tools.binary_manager import download_and_verify_binary
            res = download_and_verify_binary.invoke("silk_v3_decoder.exe")
            if "❌" in res: return res

        # 2. 第一步：Silk -> PCM
        # 强制 UTF-8 环境以支持 Windows 中文路径
        cmd_silk_str = ' '.join([f'"{s}"' for s in [str(decoder_path), str(silk_file), str(pcm_path)]])
        subprocess.run(
            f"chcp 65001 >nul && {cmd_silk_str}", 
            shell=True, check=True, capture_output=True
        )

        # 3. 第二步：PCM -> WAV
        # 强制 24kHZ/16bit/单声道 以适配后续 ASR 或处理
        cmd_ffmpeg_args = [
            "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", 
            "-i", str(pcm_path), str(wav_path)
        ]
        cmd_ffmpeg_str = ' '.join([f'"{s}"' for s in cmd_ffmpeg_args])
        subprocess.run(
            f"chcp 65001 >nul && {cmd_ffmpeg_str}", 
            shell=True, check=True, capture_output=True
        )

        # 4. 清理中转文件
        if pcm_path.exists(): os.remove(pcm_path)

        logger.info(f"🧬 [Decoder] 成功解码原生语音: {wav_path}")
        return str(wav_path.absolute())

    except Exception as e:
        logger.error(f"❌ 语音解码链路崩溃: {e}")
        return f"❌ 解码失败：{str(e)}"
