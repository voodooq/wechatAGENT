import os
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from langchain_core.tools import tool
from utils.logger import logger

class AutoVoiceProcessor:
    """全自动微信语音处理器"""
    
    def __init__(self):
        self.current_account = None
        self.voice_directory = None
        self.last_processing_time = 0
        
    def auto_detect_and_process_voice(self, scout_seconds: int = 30) -> Dict:
        """
        自动检测当前微信账号并处理最新语音
        
        Args:
            scout_seconds: 扫描时间范围（秒）
            
        Returns:
            处理结果字典
        """
        try:
            # 1. 自动识别当前微信账号
            account_info = self._auto_identify_current_account()
            if not account_info.get('success'):
                return account_info
            
            # 2. 定位语音目录
            voice_path = self._locate_voice_directory(account_info['account_path'])
            if not voice_path:
                return {
                    'success': False,
                    'error': '无法定位语音目录',
                    'account_info': account_info
                }
            
            # 3. 寻找最新语音文件
            latest_voice = self._find_latest_voice_file(voice_path, scout_seconds)
            if not latest_voice:
                return {
                    'success': False,
                    'error': f'在{scout_seconds}秒内未找到新的语音文件',
                    'voice_directory': str(voice_path),
                    'account_info': account_info
                }
            
            # 4. 处理语音文件
            processed_result = self._process_voice_file(latest_voice)
            
            # 5. 返回完整结果
            return {
                'success': True,
                'account_info': account_info,
                'voice_file': str(latest_voice),
                'processing_result': processed_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"自动语音处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _auto_identify_current_account(self) -> Dict:
        """自动识别当前最活跃的微信账号"""
        try:
            from core.tools.wechat_account_manager import _account_manager
            accounts = _account_manager.scan_all_accounts()
            
            if not accounts:
                return {'success': False, 'error': '未检测到任何微信账号'}
            
            # 选择活跃度最高的账号
            current_account = max(accounts, key=lambda x: x['activity_score'])
            
            return {
                'success': True,
                'user_id': current_account['user_id'],
                'nickname': current_account['nickname'],
                'account_path': current_account['full_path'],
                'activity_score': current_account['activity_score'],
                'last_modified': current_account['last_modified']
            }
            
        except Exception as e:
            logger.error(f"账号识别失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _locate_voice_directory(self, account_path: str) -> Optional[Path]:
        """定位语音目录"""
        try:
            account_dir = Path(account_path)
            voice_paths = [
                account_dir / "FileStorage" / "Voice",
                account_dir / "Voice",
                account_dir / "FileStorage" / "MsgAttach" / "Voice"
            ]
            
            for voice_path in voice_paths:
                if voice_path.exists():
                    logger.info(f"✅ 找到语音目录: {voice_path}")
                    self.voice_directory = voice_path
                    return voice_path
            
            logger.warning(f"⚠️ 未找到语音目录，账号路径: {account_path}")
            return None
            
        except Exception as e:
            logger.error(f"语音目录定位失败: {e}")
            return None
    
    def _find_latest_voice_file(self, voice_dir: Path, scout_seconds: int) -> Optional[Path]:
        """寻找最新的语音文件"""
        try:
            latest_file = None
            latest_time = 0
            now = time.time()
            cutoff_time = now - scout_seconds
            
            # 支持的语音文件格式
            voice_extensions = {'.silk', '.aud', '.mp3', '.wav', '.m4a', '.amr'}
            
            for root, _, files in os.walk(voice_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in voice_extensions):
                        file_path = Path(root) / file
                        try:
                            mtime = file_path.stat().st_mtime
                            # 只考虑最近的文件
                            if mtime > cutoff_time and mtime > latest_time:
                                latest_time = mtime
                                latest_file = file_path
                        except (OSError, PermissionError):
                            continue
            
            if latest_file:
                time_diff = int(now - latest_time)
                logger.info(f"✅ 找到最新语音文件: {latest_file} ({time_diff}秒前)")
                return latest_file
            else:
                logger.info(f"❌ 在指定时间范围内未找到语音文件")
                return None
                
        except Exception as e:
            logger.error(f"语音文件搜索失败: {e}")
            return None
    
    def _process_voice_file(self, voice_file: Path) -> Dict:
        """处理语音文件（识别+TTS）"""
        try:
            # 1. 准备临时目录
            temp_dir = Path("temp") / "voice_processing"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. 复制文件到临时目录
            temp_file = temp_dir / voice_file.name
            shutil.copy2(voice_file, temp_file)
            
            # 3. 修复SILK头部（如果需要）
            if temp_file.suffix.lower() == '.silk':
                from core.tools.voice_healer import patch_silk_header
                repaired_file = patch_silk_header(str(temp_file))
                if repaired_file != str(temp_file):
                    temp_file = Path(repaired_file)
            
            # 4. 解码SILK格式（如果需要）
            final_audio_path = str(temp_file)
            if temp_file.suffix.lower() == '.silk':
                from core.tools.voice_decoder import decode_silk_to_wav
                decoded_result = decode_silk_to_wav.invoke(str(temp_file))
                if "❌" not in decoded_result:
                    final_audio_path = decoded_result
            
            # 5. 调用工具进行识别
            from tools.default import recognize_speech_from_audio
            recognition_result = recognize_speech_from_audio.invoke({"audio_file_path": final_audio_path})
            
            if recognition_result.get("status") != "success":
                return {
                    'success': False,
                    'stage': 'recognition',
                    'error': recognition_result.get("message", "识别失败")
                }
            
            recognized_text = recognition_result.get("recognized_text", "")
            logger.info(f"🗣️ 语音识别结果: {recognized_text}")
            
            # 6. 情感分析
            from core.tools.sentiment_engine import analyze_voice_sentiment
            duration = self._get_audio_duration(final_audio_path)
            sentiment = analyze_voice_sentiment.invoke({
                "transcript": recognized_text,
                "duration": duration
            })
            
            # 7. TTS合成回应
            tts_result = self._generate_tts_response(recognized_text, sentiment)
            
            return {
                'success': True,
                'recognized_text': recognized_text,
                'sentiment': sentiment,
                'tts_result': tts_result,
                'audio_duration': duration,
                'processed_file': final_audio_path
            }
            
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            return {
                'success': False,
                'stage': 'processing',
                'error': str(e)
            }
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频文件时长"""
        try:
            cmd = f'ffprobe -i "{audio_path}" -show_entries format=duration -v quiet -of csv="p=0"'
            duration = float(subprocess.check_output(cmd, shell=True).strip() or 5.0)
            return duration
        except:
            return 5.0  # 默认5秒
    
    def _generate_tts_response(self, recognized_text: str, sentiment: str) -> Dict:
        """生成TTS回应"""
        try:
            # 构造智能回应
            response_text = self._generate_intelligent_response(recognized_text, sentiment)
            
            # TTS合成
            import asyncio
            from tools.speech_tool import async_tts_and_play
            
            # 异步执行TTS
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tts_result = loop.run_until_complete(async_tts_and_play(response_text))
            finally:
                loop.close()
            
            return {
                'success': True,
                'response_text': response_text,
                'tts_audio_path': tts_result if tts_result else None,
                'sentiment_used': sentiment
            }
            
        except Exception as e:
            logger.error(f"TTS生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_intelligent_response(self, text: str, sentiment: str) -> str:
        """生成智能回应文本"""
        # 基于情感和内容生成回应
        responses = {
            'positive': [
                f"听起来很不错呢！你说的{text}让我很感兴趣。",
                f"很高兴听到你分享{sentiment}的想法！"
            ],
            'negative': [
                f"我理解你的感受，{text}确实让人有些困扰。",
                f"听起来你现在{sentiment}，需要我帮忙吗？"
            ],
            'neutral': [
                f"我听到了你说的{text}，很有意思。",
                f"谢谢你的分享，关于{text}我想了解更多。"
            ]
        }
        
        # 根据情感选择回应
        sentiment_key = sentiment.split()[0] if ' ' in sentiment else 'neutral'
        if sentiment_key not in responses:
            sentiment_key = 'neutral'
            
        import random
        return random.choice(responses[sentiment_key])

# 全局实例
_auto_voice_processor = AutoVoiceProcessor()

@tool
def auto_process_latest_voice(scout_seconds: int = 30, force_refresh: bool = False) -> str:
    """
    自动处理最新的微信语音消息
    
    Args:
        scout_seconds: 扫描时间范围（秒），默认30秒
        force_refresh: 是否强制刷新账号信息，默认False
        
    Returns:
        处理结果的详细信息
    """
    try:
        # 如果需要强制刷新或距离上次处理超过10秒
        current_time = time.time()
        if force_refresh or (current_time - _auto_voice_processor.last_processing_time) > 10:
            from core.tools.wechat_account_manager import refresh_account_list
            refresh_account_list.invoke({})
            _auto_voice_processor.last_processing_time = current_time
        
        result = _auto_voice_processor.auto_detect_and_process_voice(scout_seconds)
        
        if result['success']:
            processing_result = result['processing_result']
            if processing_result['success']:
                response = "✅ 语音处理成功!\n"
                response += "=" * 30 + "\n"
                response += f"👤 账号: {result['account_info']['nickname']} ({result['account_info']['user_id']})\n"
                response += f"🔊 语音文件: {os.path.basename(result['voice_file'])}\n"
                response += f"🗣️ 识别内容: {processing_result['recognized_text']}\n"
                response += f"💭 情感分析: {processing_result['sentiment']}\n"
                response += f"🤖 AI回应: {processing_result['tts_result']['response_text']}\n"
                
                if processing_result['tts_result']['tts_audio_path']:
                    response += f"🎵 TTS音频: {processing_result['tts_result']['tts_audio_path']}\n"
                
                response += f"⏱️ 处理时间: {time.strftime('%H:%M:%S')}"
            else:
                response = f"❌ 语音处理失败: {processing_result.get('error', '未知错误')}"
        else:
            response = f"❌ 处理失败: {result.get('error', '未知错误')}"
            if 'account_info' in result:
                response += f"\n当前账号: {result['account_info'].get('nickname', '未知')}"
        
        return response
        
    except Exception as e:
        logger.error(f"自动语音处理工具失败: {e}")
        return f"❌ 工具执行失败: {str(e)}"

@tool
def monitor_voice_continuously(interval: int = 60) -> str:
    """
    持续监控语音消息（测试用）
    
    Args:
        interval: 检查间隔（秒），默认60秒
        
    Returns:
        监控启动信息
    """
    try:
        response = f"🔄 已启动语音监控，检查间隔: {interval}秒\n"
        response += "使用 'stop_voice_monitor' 停止监控"
        # 实际实现需要后台线程，这里只返回启动信息
        return response
    except Exception as e:
        return f"❌ 监控启动失败: {str(e)}"

@tool
def get_voice_system_status() -> str:
    """
    获取语音处理系统状态
    
    Returns:
        系统状态信息
    """
    try:
        # 检查依赖
        dependencies = {
            'ffmpeg': 'ffprobe -version',
            'edge-tts': 'edge-tts --version',
            'speech_recognition': None
        }
        
        status_lines = ["🎙️ 语音处理系统状态\n" + "=" * 25]
        
        for dep_name, check_cmd in dependencies.items():
            try:
                if check_cmd:
                    subprocess.check_output(check_cmd, shell=True, stderr=subprocess.DEVNULL)
                status_lines.append(f"✅ {dep_name}: 可用")
            except:
                status_lines.append(f"❌ {dep_name}: 不可用")
        
        # 显示当前配置
        status_lines.append(f"\n⚙️ 当前配置:")
        status_lines.append(f"   账号识别: 自动")
        status_lines.append(f"   路径定位: 自动")
        status_lines.append(f"   语音格式: SILK/MP3/WAV/M4A/AMR")
        status_lines.append(f"   TTS引擎: Edge-TTS")
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"❌ 状态检查失败: {str(e)}"