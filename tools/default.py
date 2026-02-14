from typing import Optional
from langchain_core.tools import tool
import speech_recognition as sr
import os
from utils.logger import logger

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
    将音频文件转换为文本。支持自动通过 ffmpeg 进行格式转换。

    Args:
        audio_file_path: 音频文件的路径（支持 silk, amr, mp3 等）。

    Returns:
        包含识别文本的字典，如果失败则返回错误信息。
    """
    import subprocess
    import speech_recognition as sr
    import os
    
    # 微信语音可能没有后缀或后缀不匹配，尝试统一转为 wav
    wav_path = audio_file_path + ".temp.wav"
    
    try:
        # 使用 ffmpeg 强制转换
        logger.info(f"正在转换音频格式: {audio_file_path} -> {wav_path}")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_file_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True, check=True
        )
        
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        
        # 优先使用 google (国内需要代理，代理已在 agent 中配置，此处受全局环境变量影响)
        text = r.recognize_google(audio, language="zh-CN")
        
        # 清理临时文件
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
        return {"status": "success", "recognized_text": text}
        
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"FFmpeg 转换失败: {e.stderr.decode()}"}
    except sr.UnknownValueError:
        return {"status": "error", "message": "无法识别音频中的语音 (可能由于底噪过大或非标准语言)"}
    except Exception as e:
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return {"status": "error", "message": f"处理音频时发生意外错误: {e}"}
