import os
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from core.config import conf
from utils.logger import logger

# 获取项目根目录下的 temp 路径
TEMP_DIR = conf.project_root / "temp" / "voice_cache"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def fix_silk_header(file_path):
    """
    [修复] 确保 Silk 文件具备标准的 #!SILK_V3 头部。
    """
    SILK_HEADER = b'#!SILK_V3'
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        if not data.startswith(SILK_HEADER):
            # 注入缺失的头部
            logger.info(f"🧬 [Fixer] 注入缺失的 Silk 头部: {file_path}")
            fixed_data = SILK_HEADER + data
            # 使用 .silk_fixed 后缀避免覆盖原始文件，或根据需要替换
            fixed_path = str(file_path).replace(".silk", "_fixed.silk").replace(".aud", "_fixed.silk")
            if fixed_path == str(file_path):
                fixed_path = str(file_path) + "_fixed.silk"
            
            with open(fixed_path, 'wb') as f:
                f.write(fixed_data)
            return fixed_path
        return str(file_path)
    except Exception as e:
        logger.error(f"头部修复失败: {e}")
        return str(file_path)

@tool
def decode_silk_to_wav(silk_path: str) -> str:
    """
    [解码] 将微信原生加密 SILK 语音转为标准 WAV (24kHZ)。
    支持 v11.0 头部自修复逻辑。
    """
    silk_file_raw = Path(silk_path)
    if not silk_file_raw.exists():
        return f"❌ 错误：找不到语音文件 {silk_path}"

    # 1. 头部修复
    silk_path_fixed = fix_silk_header(silk_file_raw)
    silk_file = Path(silk_path_fixed)

    wav_path = TEMP_DIR / f"{silk_file.stem}_decoded.wav"
    pcm_path = TEMP_DIR / f"{silk_file.stem}.pcm"

    try:
        # 1. 环境自检与自愈
        # [v11.0 Neuro-Repair] 启动自愈检查
        from core.tools.env_healer import ensure_binary_environment
        ensure_binary_environment("silk_v3_decoder.exe")
        
        decoder_path = conf.project_root / "kernel" / "bin" / "silk_v3_decoder.exe"
        if not decoder_path.exists():
            return "❌ [环境缺失] 无法自动补全 silk_v3_decoder.exe。请手动修复环境。"

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
        # 如果生成了修复文件，也标记为可清理（或者根据业务逻辑保留）
        if silk_path_fixed != silk_path:
            logger.info(f"中转修复文件可清理: {silk_path_fixed}")

        logger.info(f"🧬 [Decoder] 成功解码原生语音: {wav_path}")
        return str(wav_path.absolute())

    except Exception as e:
        logger.error(f"❌ 语音解码链路崩溃: {e}")
        return f"❌ 解码失败：{str(e)}"
