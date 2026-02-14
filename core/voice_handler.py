"""
语音处理模块 - 处理微信语音消息
"""

import os
import tempfile
import json
from pathlib import Path
import subprocess
import logging
import speech_recognition as sr
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class VoiceHandler:
    """处理语音消息的类"""
    
    def __init__(self):
        self.supported_formats = ['.silk', '.amr', '.mp3', '.m4a', '.wav', '.ogg']
        self.recognizer = sr.Recognizer()
        
    def process_wechat_voice(self, voice_file_path: str) -> str:
        """
        处理微信语音消息
        Args:
            voice_file_path: 语音文件路径
        Returns:
            识别出的文本内容
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(voice_file_path):
                return "语音文件不存在"
            
            # 获取文件扩展名
            ext = os.path.splitext(voice_file_path)[1].lower()
            
            # 如果是微信 SILK 格式，需要先转换
            if ext == '.silk':
                return self._process_silk_voice(voice_file_path)
            elif ext == '.amr':
                return self._process_amr_voice(voice_file_path)
            else:
                # 其他格式直接识别
                return self._recognize_speech(voice_file_path)
                
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            return f"语音识别失败: {str(e)}"
    
    def _process_silk_voice(self, silk_file_path: str) -> str:
        """处理微信 SILK 格式语音"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_file = tmp.name
            
            # 使用 ffmpeg 转换 SILK 到 WAV
            cmd = ['ffmpeg', '-i', silk_file_path, '-ar', '16000', '-ac', '1', wav_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"SILK 转换失败: {result.stderr}"
            
            # 识别转换后的 WAV 文件
            text = self._recognize_speech(wav_file)
            
            # 清理临时文件
            os.unlink(wav_file)
            
            return text
            
        except Exception as e:
            logger.error(f"SILK 处理失败: {e}")
            return f"SILK 格式处理失败: {str(e)}"
    
    def _process_amr_voice(self, amr_file_path: str) -> str:
        """处理 AMR 格式语音"""
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_file = tmp.name
            
            # 使用 pydub 转换 AMR 到 WAV
            audio = AudioSegment.from_file(amr_file_path, format="amr")
            audio.export(wav_file, format="wav")
            
            # 识别转换后的 WAV 文件
            text = self._recognize_speech(wav_file)
            
            # 清理临时文件
            os.unlink(wav_file)
            
            return text
            
        except Exception as e:
            logger.error(f"AMR 处理失败: {e}")
            return f"AMR 格式处理失败: {str(e)}"
    
    def _recognize_speech(self, audio_file_path: str) -> str:
        """识别语音文件内容"""
        try:
            # 使用 SpeechRecognition 库
            with sr.AudioFile(audio_file_path) as source:
                # 调整环境噪音
                self.recognizer.adjust_for_ambient_noise(source)
                audio_data = self.recognizer.record(source)
                
                # 尝试使用 Google 语音识别
                try:
                    text = self.recognizer.recognize_google(audio_data, language='zh-CN')
                    return text
                except sr.UnknownValueError:
                    return "无法识别语音内容"
                except sr.RequestError as e:
                    return f"语音识别服务错误: {str(e)}"
                    
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return f"语音识别失败: {str(e)}"
    
    def get_voice_duration(self, voice_file_path: str) -> float:
        """获取语音时长（秒）"""
        try:
            if not os.path.exists(voice_file_path):
                return 0.0
            
            # 使用 pydub 获取音频时长
            audio = AudioSegment.from_file(voice_file_path)
            return len(audio) / 1000.0  # 转换为秒
                
        except Exception as e:
            logger.error(f"获取语音时长失败: {e}")
            return 0.0
    
    def analyze_voice_message(self, voice_file_path: str) -> dict:
        """分析语音消息，返回详细信息"""
        result = {
            "file_path": voice_file_path,
            "exists": False,
            "duration": 0.0,
            "text": "",
            "format": "",
            "size": 0
        }
        
        try:
            if not os.path.exists(voice_file_path):
                return result
            
            result["exists"] = True
            result["format"] = os.path.splitext(voice_file_path)[1].lower()
            result["size"] = os.path.getsize(voice_file_path)
            result["duration"] = self.get_voice_duration(voice_file_path)
            
            # 如果语音时长超过1秒，尝试识别
            if result["duration"] > 1.0:
                result["text"] = self.process_wechat_voice(voice_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"语音分析失败: {e}")
            result["error"] = str(e)
            return result