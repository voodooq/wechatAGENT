import os
import asyncio
import edge_tts
import pygame
from core.config import conf
from utils.logger import logger

async def text_to_speech(text: str, output_path: str = None) -> str:
    """
    将文本转换为语音文件 (MP3)
    
    Args:
        text: 要转换的文本
        output_path: 输出文件路径，若为 None 则自动生成
        
    Returns:
        str: 生成的语音文件路径
    """
    if not output_path:
        temp_dir = os.path.join(conf.project_root, "temp", "tts")
        os.makedirs(temp_dir, exist_ok=True)
        import time
        output_path = os.path.join(temp_dir, f"tts_{int(time.time())}.mp3")
    
    voice = getattr(conf, 'tts_voice', 'zh-CN-XiaoxiaoNeural')
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        logger.info(f"TTS 合成成功: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"TTS 合成失败: {e}")
        return ""

def play_audio(file_path: str):
    """
    在本地播放音频文件
    使用 pygame.mixer 实现，支持非阻塞播放。
    """
    if not os.path.exists(file_path):
        logger.error(f"播放失败：文件不存在 {file_path}")
        return

    try:
        # 初始化界面
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # 加载并播放
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # 等待播放结束 (可选，根据需求决定是否阻塞)
        # while pygame.mixer.music.get_busy():
        #     time.sleep(0.1)
        
        logger.info(f"🔊 正在播放语音: {file_path}")
    except Exception as e:
        logger.error(f"音频播放异常: {e}")

async def async_tts_and_play(text: str):
    """
    封装好的异步 TTS 合成、播放并支持微信原生 SILK 转码。
    """
    if not text:
        return None
        
    # 1. 合成语音 (MP3)
    audio_path = await text_to_speech(text)
    
    if not audio_path:
        return None

    # 2. 本地播放 (可选)
    if getattr(conf, 'tts_local_play', True):
        play_audio(audio_path)
        
    # 3. [v10.6] 微信原生转码：MP3 -> SILK
    # 只有当开启了下发到微信的功能时，才执行耗时的转码操作
    if getattr(conf, 'tts_send_to_chat', False):
        try:
            from core.tools.audio_converter import convert_to_silk
            logger.info(f"🧬 [Native Voice] 正在执行 SILK 格式转码...")
            # [v11.0 Neuro-Repair] 使用 .invoke() 调用以消除弃用警告
            silk_path = convert_to_silk.invoke(audio_path)
            
            if silk_path and not silk_path.startswith("❌"):
                logger.info(f"✅ SILK 转码成功: {silk_path}")
                return silk_path
            else:
                logger.warning(f"⚠️ SILK 转码失败，将尝试直接发送原始文件: {silk_path}")
        except Exception as e:
            logger.error(f"❌ 转码逻辑执行异常: {e}")

    return audio_path
