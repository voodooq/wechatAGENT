"""
消息处理器 (Consumer)

从消息队列消费微信消息，
调用 AI Agent 处理后发送回复。
"""
import time
import threading

import pythoncom
from wechat.listener import msg_queue, WechatMessage
from wechat.sender import sender
from core.agent import processMessage
from core.config import conf
from utils.logger import logger, daily_logger


class MessageProcessor:
    """
    消息处理器

    在独立线程中运行，持续从队列取出消息，
    调用 Agent 处理并发送回复。
    """

    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None

    def _processLoop(self):
        """消息处理主循环"""
        # 初始化线程 COM 环境 (wxauto/uiautomation 必需)
        pythoncom.CoInitialize()
        logger.debug("MessageProcessor 线程 COM 环境已初始化")
        
        try:
            while self._running:
                try:
                    # 阻塞等待消息，超时 1 秒后重新检查运行状态
                    try:
                        message: WechatMessage = msg_queue.get(timeout=1.0)
                    except Exception:
                        continue

                    logger.info(
                        f"开始处理消息 [{message.sender}]: "
                        f"{message.content[:50]}..."
                    )
                    
                    is_voice_input = message.content.startswith("[语音]")
                    user_input = message.content
                    logger.debug(f"[处理诊断] 内容=\"{message.content}\", 是否匹配语音={is_voice_input}")

                    # --- [v10.2.2] 语音消息预处理逻辑 (增强模糊匹配与鲁棒性) ---
                    if is_voice_input:
                        try:
                            # [Fix v10.5.1] 检查消息对象类型。如果是自发消息 (SelfMessage)，wxauto 不支持语音提取，需静默跳过。
                            # [v11.0 Neuro-Repair] 针对“文件传输助手”特殊会话，强行解除 self 限制，实现语音闭环交互。
                            is_self_msg = type(message.raw).__name__ == 'SelfMessage'
                            is_master_thread = message.sender == "文件传输助手"
                            
                            if is_self_msg and not is_master_thread:
                                logger.debug(f"🔇 收到自发语音消息 [{message.content}]，已跳过转录流程 (wxauto 不支持)")
                                user_input = message.content
                                raise StopIteration("跳过自发消息处理")

                            logger.info(f"🎤 正在接收并转录语音消息 [{message.content}] 来自 [{message.sender}]...")
                            # 1. 发送中间状态反馈
                            sender.sendMessage(message.sender, f"🎤 正在聆听您的语音({message.content.replace('[语音]', '')})，请稍候...")
                            
                            # 2. 准备存储目录
                            import os
                            temp_dir = os.path.join(conf.project_root, "temp", "voice")
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # [v11.5 Ghost-Hunter] 幽灵猎手协议：物理解封与快速寻路
                            save_path = None
                            
                            # 1. 尝试常规提取 (如果具备接口)
                            if hasattr(message.raw, 'SaveVoice'):
                                try:
                                    save_path = message.raw.SaveVoice(savepath=temp_dir)
                                except Exception as e:
                                    logger.warning(f"SaveVoice 接口调用失败: {e}，将启动物理探测补救...")

                            # 2. 物理寻路雷达 (自愈降级)
                            if not save_path or not os.path.exists(save_path):
                                logger.info("🎯 [Ghost-Hunter] 启动物理扇区扫描以捕获语音流...")
                                from core.tools.wechat_locator import ultra_wechat_locator
                                from utils.wechat_utils import fast_scan_voice_file
                                
                                # 2.1 动态锚点识别
                                anchor_path = ultra_wechat_locator.invoke({})
                                if "❌" in anchor_path:
                                    logger.error(f"无法定位物理锚点: {anchor_path}")
                                    manual_path = None
                                else:
                                    # 2.2 极速雷达扫描
                                    manual_path = fast_scan_voice_file(anchor_path, scout_seconds=10)
                                
                                if manual_path and os.path.exists(manual_path):
                                    logger.info(f"✅ [Ghost-Hunter] 成功锁定物理路径: {manual_path}")
                                    
                                    # [v11.8 Fix] 语音头部二进制自愈：修复微信 PC 版常见的 Missing magic number 问题
                                    from core.tools.voice_healer import patch_silk_header
                                    repaired_path = patch_silk_header(manual_path)
                                    
                                    import shutil
                                    dest_path = os.path.join(temp_dir, os.path.basename(repaired_path))
                                    shutil.copy2(repaired_path, dest_path)
                                    save_path = dest_path
                                else:
                                    # 如果是 Master 线程必须报错，否则静默跳过
                                    if is_master_thread and not is_self_msg:
                                        raise Exception("物理寻路失败：未能在微信目录中找到刚生成的语音文件")
                                    elif is_self_msg and not is_master_thread:
                                        raise StopIteration("跳过无法寻路的自发消息")
                                    else:
                                        raise Exception("当前消息对象不支持语音提取且物理寻路失败")
                            
                            if save_path and os.path.exists(save_path):
                                # [Fix v10.5.2] 检查文件大小
                                if os.path.getsize(save_path) < 100:
                                    logger.warning(f"语音文件太小 ({os.path.getsize(save_path)} bytes)，跳过")
                                    raise Exception("音频过短或无效")

                                logger.info(f"语音已就绪: {save_path}")
                                
                                # --- [v10.7] 深度解码链路 (Aural Mastery) ---
                                # 如果是加密的 SILK 格式，先通过深度解码器自愈并解码
                                if save_path.lower().endswith(".silk"):
                                    logger.info("🧬 [v10.7] 检测到加密语音流，启动深度解码器...")
                                    from core.tools.voice_decoder import decode_silk_to_wav
                                    decoded_path = decode_silk_to_wav.invoke(save_path)
                                    
                                    if "❌" in decoded_path:
                                        logger.error(f"语音解码失败: {decoded_path}")
                                        raise Exception(decoded_path)
                                    save_path = decoded_path

                                # 3. 调用工具进行识别
                                from tools.default import recognize_speech_from_audio
                                res = recognize_speech_from_audio(save_path)
                                
                                if res.get("status") == "success":
                                    user_input_raw = res.get("recognized_text", "")
                                    logger.info(f"语音识别成功: {user_input_raw}")
                                    
                                    # [v11.9 Empathy] 情感引擎分析
                                    from core.tools.sentiment_engine import analyze_voice_sentiment
                                    duration = 5.0
                                    try:
                                        import subprocess
                                        cmd = f'ffprobe -i "{save_path}" -show_entries format=duration -v quiet -of csv="p=0"'
                                        duration = float(subprocess.check_output(cmd, shell=True).strip() or 5.0)
                                    except: pass
                                    
                                    sentiment_tag = analyze_voice_sentiment.invoke({"transcript": user_input_raw, "duration": duration})
                                    # 注入情感上下文给大脑
                                    message.content = f"{sentiment_tag}\n\n[语音内容]: {user_input_raw}"
                                    
                                    sender.sendMessage(message.sender, f"👂 我听到了: \"{user_input_raw}\"")
                                    # 注意：后续的大脑处理逻辑会使用 message.content
                                else:
                                    error_msg = res.get("message", "识别失败")
                                    logger.error(f"语音识别失败: {error_msg}")
                                    sender.sendMessage(message.sender, f"❌ 语音识别失败: {error_msg}")
                                    msg_queue.task_done()
                                    continue
                            else:
                                raise Exception("无法定位生成的音频文件")
                                
                        except StopIteration:
                            pass
                        except Exception as e:
                            logger.error(f"语音预处理环节崩溃: {e}")
                            sender.sendMessage(message.sender, f"抱歉，我暂时无法听清这段语音: {e}")
                            msg_queue.task_done()
                            continue

                    # 调用 AI Agent 获取回复
                    try:
                        import asyncio
                        # [v7.3 Bridge] 在同步线程中调用异步的 processMessage
                        reply = asyncio.run(processMessage(
                            userInput=user_input,
                            sender=message.sender,
                            role_level=message.role_level
                        ))
                        # [Fix v10.2.7] 动态模型名称日志
                        provider_name = getattr(conf, 'llm_provider', 'AI').capitalize()
                        logger.info(f"{provider_name} 回复获取成功 [{message.sender}]，长度: {len(reply) if reply else 0}")
                    except Exception as e:
                        logger.error(f"AI 处理异常 [{message.sender}]: {e}")
                        reply = f"抱歉，处理消息时发生错误: {str(e)[:80]}，请稍后重试。 (AI)"

                    # 记录审计日志
                    try:
                        from core.audit import audit_logger
                        audit_logger.log_action(
                            user=message.sender,
                            command=message.content,
                            status="SUCCESS" if reply else "NO_REPLY"
                        )
                    except Exception as e:
                        logger.warning(f"审计日志记录失败: {e}")

                    # 通过微信发送回复
                    if reply:
                        try:
                            # [Fix v10.6.1] 修正下发策略：
                            # 只有开启了“发送到微信”且当前是“语音输入”时，才跳过文本回复
                            tts_to_chat = getattr(conf, 'tts_enabled', False) and getattr(conf, 'tts_send_to_chat', False)
                            should_skip_text = tts_to_chat and is_voice_input
                            
                            if not should_skip_text:
                                sender.sendMessage(
                                    receiver=message.sender,
                                    content=reply,
                                )
                                logger.info(f"✅ 文本回复已发送给 [{message.sender}]")
                            else:
                                logger.info(f"🔇 已启用纯语音回复模式，跳过文本发送")
                                
                            # 记录到每日消息日志
                            daily_logger.info(f"[{message.sender}] {reply}")
                            # 发送后强制冷却
                            time.sleep(1.0)
                            
                            # --- [v10.3] 语音播报增强 (TTS) ---
                            # [Optimization] 仅当输入为语音时才触发 TTS 回复
                            if getattr(conf, 'tts_enabled', False) and is_voice_input:
                                try:
                                    from tools.speech_tool import async_tts_and_play
                                    # 异步触发并获取路径 (v10.6 已集成 SILK 转码)
                                    final_audio_path = asyncio.run(async_tts_and_play(reply))
                                    
                                    # 如果开启了微信端发送
                                    if final_audio_path and tts_to_chat:
                                        sender.sendFile(message.sender, final_audio_path)
                                        logger.info(f"📤 语音回复文件已下发 (路径: {final_audio_path})")
                                except Exception as tts_e:
                                    logger.warning(f"语音回复失败: {tts_e}")
                        except Exception as e:
                            logger.error(f"发送回复失败 [{message.sender}]: {e}")

                    # 标记任务完成
                    msg_queue.task_done()

                except Exception as e:
                    logger.error(f"消息循环内部异常: {e}")
                    time.sleep(2)
        finally:
            pythoncom.CoUninitialize()
            logger.debug("MessageProcessor 线程 COM 环境已释放")

    def start(self) -> None:
        """启动处理器线程"""
        if self._running:
            logger.warning("处理器已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._processLoop,
            name="MessageProcessor",
            daemon=True,
        )
        self._thread.start()
        logger.info("消息处理器已启动")

    def stop(self) -> None:
        """停止处理器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("消息处理器已停止")

    @property
    def isRunning(self) -> bool:
        return self._running
