from typing import Optional
from langchain_core.tools import tool
import speech_recognition as sr
import os
from utils.logger import logger
from core.config import conf

# 导入实际的搜索工具实现
from tools.web_search_tool import searchWeb, tavilySearch

def queryDatabase(query: str) -> dict:
    """
    执行数据库查询，返回查询结果
    """
    pass

def searchWeb(query: str) -> dict:
    """
    执行网页搜索，返回搜索结果
    """
    try:
        # 调用实际的异步搜索工具
        import asyncio
        result = asyncio.run(searchWeb(query))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def tavilySearch(query: str) -> dict:
    """
    使用 Tavily API 执行深度搜索
    """
    try:
        import asyncio
        result = asyncio.run(tavilySearch(query))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_webpage_content(url: str) -> dict:
    """
    读取网页内容
    """
    pass

def install_python_library(library_name: str) -> dict:
    """
    安装 Python 库
    """
    pass

def install_windows_software(software_name: str) -> dict:
    """
    安装 Windows 软件
    """
    pass

def close_browser() -> dict:
    """
    关闭浏览器
    """
    pass

def browseWebpage(url: str, actions: Optional[list[dict]] = None) -> dict:
    """
    浏览网页并执行操作
    """
    pass

def ask_for_confirmation(reason: str, user_name: str) -> dict:
    """
    请求用户确认
    """
    pass

def execute_system_command(command: str, user_name: str) -> dict:
    """
    执行系统命令
    """
    pass

def manage_wechat_window(action: str) -> dict:
    """
    管理微信窗口
    """
    pass

def capture_and_send_screenshot(user_name: str) -> dict:
    """
    捕获并发送截图
    """
    pass

def read_and_analyze_file(file_path: str, query: Optional[str] = None) -> dict:
    """
    读取并分析文件
    """
    pass

def verify_state(check_type: str, target: str) -> dict:
    """
    验证状态
    """
    pass

def evolve_code(file_path: str, code: str, reason: str) -> dict:
    """
    进化代码
    """
    pass

def sync_to_github(commit_msg: str) -> dict:
    """
    同步到 GitHub
    """
    pass

def request_hot_reload(reason: Optional[str] = None, report_to: Optional[str] = None) -> dict:
    """
    请求热重载
    """
    pass

def isolate_self(reason: str) -> dict:
    """
    隔离自己
    """
    pass

def read_pdf_invoice(file_path: str) -> dict:
    """
    读取 PDF 发票
    """
    pass

@tool
def recognize_speech_from_audio(audio_file_path: str) -> dict:
    """
    将音频文件（silk, amr, mp3, m4a等）转换为文本。
    支持微信独有的 SILK 格式自动解码与头部修复 (v11.0)。

    Args:
        audio_file_path: 音频文件的本地路径。
    """
    import subprocess
    import speech_recognition as sr
    import os
    import time
    
    project_root = conf.project_root
    decoder_exe = os.path.join(project_root, "kernel", "bin", "silk_v3_decoder.exe")
    wav_path = audio_file_path + ".recon.wav"
    pcm_path = audio_file_path + ".temp.pcm"
    
    start_time = time.time()
    
    try:
        if not os.path.exists(audio_file_path):
            return {"status": "error", "message": f"源音频文件不存在: {audio_file_path}"}
            
        # 1. 检查是否为 SILK 格式并处理缺失头部 (v11.0 逻辑)
        is_silk = False
        SILK_HEADER = b"#!SILK_V3"
        with open(audio_file_path, 'rb') as f:
            header = f.read(10)
        
        if SILK_HEADER in header:
            is_silk = True
        elif audio_file_path.lower().endswith((".silk", ".aud")):
            # 可能是缺失头部的 silk 文件，尝试通过后缀名辅助判断并修复
            from core.tools.voice_decoder import fix_silk_header
            fixed_path = fix_silk_header(audio_file_path)
            if fixed_path != audio_file_path:
                logger.info(f"🧬 [ASR] 自动修复缺失头部的 Silk 文件: {audio_file_path}")
                audio_file_path = fixed_path
                is_silk = True

        # [Fix v11.0] 统一转码标准：强制使用 chcp 65001 确保 Windows 路径兼容
        if is_silk:
            if not os.path.exists(decoder_exe):
                # 尝试从备份路径加载
                decoder_exe = os.path.join(project_root, "tools", "bin", "silk_v3_decoder.exe")
                if not os.path.exists(decoder_exe):
                    return {"status": "error", "message": f"缺少 SILK 解码器: {decoder_exe}"}
                
            logger.info(f"🧬 [ASR] 检测到 SILK 格式，解码器: {decoder_exe}")
            # SILK -> PCM
            cmd_silk = f'chcp 65001 >nul && "{decoder_exe}" "{audio_file_path}" "{pcm_path}"'
            subprocess.run(cmd_silk, shell=True, capture_output=True, check=True)
            
            # [Core Patch] PCM -> WAV (通过 FFmpeg 重新采样至 16k 黄金频率)
            logger.info(f"🧬 [ASR] 执行 PCM 到 WAV 转换 (采样率校准: 16000Hz)")
            cmd_ffmpeg = f'chcp 65001 >nul && ffmpeg -y -f s16le -ar 24000 -ac 1 -i "{pcm_path}" -ar 16000 "{wav_path}"'
            subprocess.run(cmd_ffmpeg, shell=True, capture_output=True, check=True)
        else:
            # 尝试直接通过 ffmpeg 转换 (适用于 mp3, amr, m4a 等)
            logger.info(f"🧬 [ASR] 执行通用转码 (FFmpeg, 目标频率: 16000Hz): {audio_file_path}")
            cmd_ffmpeg_generic = f'chcp 65001 >nul && ffmpeg -y -i "{audio_file_path}" -ar 16000 -ac 1 "{wav_path}"'
            subprocess.run(cmd_ffmpeg_generic, shell=True, capture_output=True, check=True)
            
        # 2. 语音识别校验
        if not os.path.exists(wav_path):
            return {"status": "error", "message": "音频转换失败，未生成有效 WAV 文件"}
            
        wav_size = os.path.getsize(wav_path)
        logger.info(f"🧬 [ASR] WAV 转换完成，大小: {wav_size} bytes, 耗时: {time.time()-start_time:.2f}s")
        
        if wav_size < 100:
            return {"status": "error", "message": "转换后的音频文件过小，可能是静音或解码异常"}

        r = sr.Recognizer()
        r.energy_threshold = 300 
        r.dynamic_energy_threshold = True
        
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        
        # 使用 Google 语音识别
        logger.info("🧬 [ASR] 正在向 Google 提交识别请求...")
        text = r.recognize_google(audio, language="zh-CN")
        
        # 3. 清理现场
        for p in [wav_path, pcm_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        
        # 如果是修复生成的文件，也清理掉
        if "_fixed.silk" in audio_file_path:
             try: os.remove(audio_file_path)
             except: pass
                
        logger.info(f"🧬 [ASR] 识别成功! 结果: \"{text}\"")
        return {"status": "success", "recognized_text": text}
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        logger.error(f"🧬 [ASR] 解码失败: {error_msg}")
        return {"status": "error", "message": f"解码失败: {error_msg}"}
    except sr.UnknownValueError:
        return {"status": "error", "message": "无法识别音频内容，识别结果为空或底噪太大"}
    except sr.RequestError as e:
        return {"status": "error", "message": f"网络请求失败，请检查代理配置: {e}"}
    except Exception as e:
        logger.error(f"🧬 [ASR] 链路异常: {e}")
        return {"status": "error", "message": f"处理异常: {str(e)}"}
