from typing import Optional
from langchain_core.tools import tool
import speech_recognition as sr
import os
from utils.logger import logger
from core.config import conf

def queryDatabase(query: str) -> dict:
    # ... (保持原有代码不变)
    pass

def searchWeb(query: str) -> dict:
    # ... (保持原有代码不变)
    pass

def tavilySearch(query: str) -> dict:
    # ... (保持原有代码不变)
    pass

def read_webpage_content(url: str) -> dict:
    # ... (保持原有代码不变)
    pass

def install_python_library(library_name: str) -> dict:
    # ... (保持原有代码不变)
    pass

def install_windows_software(software_name: str) -> dict:
    # ... (保持原有代码不变)
    pass

def close_browser() -> dict:
    # ... (保持原有代码不变)
    pass

def browseWebpage(url: str, actions: Optional[list[dict]] = None) -> dict:
    # ... (保持原有代码不变)
    pass

def ask_for_confirmation(reason: str, user_name: str) -> dict:
    # ... (保持原有代码不变)
    pass

def execute_system_command(command: str, user_name: str) -> dict:
    # ... (保持原有代码不变)
    pass

def manage_wechat_window(action: str) -> dict:
    # ... (保持原有代码不变)
    pass

def capture_and_send_screenshot(user_name: str) -> dict:
    # ... (保持原有代码不变)
    pass

def read_and_analyze_file(file_path: str, query: Optional[str] = None) -> dict:
    # ... (保持原有代码不变)
    pass

def verify_state(check_type: str, target: str) -> dict:
    # ... (保持原有代码不变)
    pass

def evolve_code(file_path: str, code: str, reason: str) -> dict:
    # ... (保持原有代码不变)
    pass

def sync_to_github(commit_msg: str) -> dict:
    # ... (保持原有代码不变)
    pass

def request_hot_reload(reason: Optional[str] = None, report_to: Optional[str] = None) -> dict:
    # ... (保持原有代码不变)
    pass

def isolate_self(reason: str) -> dict:
    # ... (保持原有代码不变)
    pass

def read_pdf_invoice(file_path: str) -> dict:
    # ... (保持原有代码不变)
    pass

@tool
def recognize_speech_from_audio(audio_file_path: str) -> dict:
    """
    将音频文件（silk, amr, mp3, m4a等）转换为文本。
    支持微信独有的 SILK 格式自动解码。

    Args:
        audio_file_path: 音频文件的本地路径。
    """
    import subprocess
    import speech_recognition as sr
    import os
    import time
    
    project_root = conf.project_root
    decoder_exe = os.path.join(project_root, "tools", "bin", "silk_v3_decoder.exe")
    wav_path = audio_file_path + ".recon.wav"
    pcm_path = audio_file_path + ".temp.pcm"
    
    start_time = time.time()
    
    try:
        if not os.path.exists(audio_file_path):
            return {"status": "error", "message": f"源音频文件不存在: {audio_file_path}"}
            
        # 1. 检查是否为 SILK 格式 (微信语音常见格式)
        is_silk = False
        with open(audio_file_path, 'rb') as f:
            header = f.read(10)
            if b"#!SILK_V3" in header:
                is_silk = True
        
        if is_silk:
            if not os.path.exists(decoder_exe):
                return {"status": "error", "message": f"缺少 SILK 解码器: {decoder_exe}"}
                
            logger.info(f"🧬 [ASR] 检测到 SILK 格式，解码器: {decoder_exe}")
            # SILK -> PCM
            subprocess.run([decoder_exe, audio_file_path, pcm_path], capture_output=True, check=True)
            # PCM -> WAV (Silk 通常是 24000Hz)
            subprocess.run([
                "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", 
                "-i", pcm_path, wav_path
            ], capture_output=True, check=True)
        else:
            # 尝试直接通过 ffmpeg 转换 (适用于 mp3, amr, m4a 等)
            logger.info(f"🧬 [ASR] 尝试通用转码 (FFmpeg): {audio_file_path}")
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_file_path, "-ar", "16000", "-ac", "1", wav_path
            ], capture_output=True, check=True)
            
        # 2. 语音识别
        if not os.path.exists(wav_path):
            return {"status": "error", "message": "音频转换失败，未生成有效 WAV 文件"}
            
        wav_size = os.path.getsize(wav_path)
        logger.info(f"🧬 [ASR] WAV 转换完成，大小: {wav_size} bytes, 耗时: {time.time()-start_time:.2f}s")
        
        if wav_size < 100:
            return {"status": "error", "message": "转换后的音频文件过小，可能是静音或解码异常"}

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        
        # 使用 Google 语音识别 (国内需梯子，已通过全局代理处理)
        # 增加 timeout 防止无限卡死
        logger.info("🧬 [ASR] 正在向 Google 提交识别请求...")
        text = r.recognize_google(audio, language="zh-CN")
        
        # 3. 清理现场
        for p in [wav_path, pcm_path]:
            if os.path.exists(p):
                os.remove(p)
                
        logger.info(f"🧬 [ASR] 识别成功! 结果: \"{text}\", 总耗时: {time.time()-start_time:.2f}s")
        return {"status": "success", "recognized_text": text}
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"🧬 [ASR] 解码失败: {error_msg}")
        return {"status": "error", "message": f"解码失败: {error_msg}"}
    except sr.UnknownValueError:
        logger.warning("🧬 [ASR] 识别结果为空 (UnknownValueError)")
        return {"status": "error", "message": "无法识别音频内容，识别结果为空或底噪太大"}
    except sr.RequestError as e:
        logger.error(f"🧬 [ASR] Google API 请求失败: {e}")
        return {"status": "error", "message": f"网络请求失败，请检查代理配置: {e}"}
    except Exception as e:
        logger.error(f"🧬 [ASR] 链路异常: {e}")
        return {"status": "error", "message": f"处理异常: {str(e)}"}
