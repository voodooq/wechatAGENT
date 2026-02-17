import os
import shutil
import time
from pathlib import Path
from typing import Dict, Optional
from langchain_core.tools import tool
from utils.logger import logger

@tool
def process_im_voice(im_type: str, scout_seconds: int = 30, temp_dir: str = None) -> Dict[str, str]:
    """
    [多IM支持] 处理指定IM的语音消息
    
    Args:
        im_type: IM类型 ('wechat', 'qq', 'dingtalk', 'lark', 'telegram')
        scout_seconds: 扫描时间范围（秒）
        temp_dir: 临时目录路径
        
    Returns:
        包含处理结果的字典
    """
    try:
        # 1. 定位语音文件
        from core.tools.im_locator import locate_im_voice
        voice_path = locate_im_voice.invoke({"im_type": im_type, "scout_seconds": scout_seconds})
        
        if "❌" in voice_path:
            return {"status": "error", "message": voice_path}
            
        if not os.path.exists(voice_path):
            return {"status": "error", "message": f"语音文件不存在: {voice_path}"}
            
        # 2. 创建临时目录
        if temp_dir is None:
            temp_dir = os.path.join("temp", "voice")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 3. 复制语音文件到临时目录
        dest_path = os.path.join(temp_dir, os.path.basename(voice_path))
        shutil.copy2(voice_path, dest_path)
        
        # 4. 修复语音头部（如果需要）
        if dest_path.lower().endswith(".silk"):
            from core.tools.voice_healer import patch_silk_header
            repaired_path = patch_silk_header(dest_path)
            if repaired_path != dest_path:
                dest_path = repaired_path
                
        # 5. 解码SILK格式（如果需要）
        if dest_path.lower().endswith(".silk"):
            from core.tools.voice_decoder import decode_silk_to_wav
            decoded_path = decode_silk_to_wav.invoke(dest_path)
            if "❌" in decoded_path:
                return {"status": "error", "message": f"语音解码失败: {decoded_path}"}
            dest_path = decoded_path
            
        # 6. 语音识别
        from tools.default import recognize_speech_from_audio
        recognition_result = recognize_speech_from_audio(dest_path)
        
        if recognition_result.get("status") == "success":
            # 7. 情感分析
            from core.tools.sentiment_engine import analyze_voice_sentiment
            duration = 5.0
            try:
                import subprocess
                cmd = f'ffprobe -i "{dest_path}" -show_entries format=duration -v quiet -of csv="p=0"'
                duration = float(subprocess.check_output(cmd, shell=True).strip() or 5.0)
            except: 
                pass
                
            sentiment_tag = analyze_voice_sentiment.invoke({
                "transcript": recognition_result.get("recognized_text", ""), 
                "duration": duration
            })
            
            return {
                "status": "success",
                "recognized_text": recognition_result.get("recognized_text", ""),
                "sentiment": sentiment_tag,
                "audio_path": dest_path,
                "original_path": voice_path
            }
        else:
            return {
                "status": "error", 
                "message": recognition_result.get("message", "语音识别失败")
            }
            
    except Exception as e:
        logger.error(f"处理{im_type}语音时发生错误: {e}")
        return {"status": "error", "message": str(e)}