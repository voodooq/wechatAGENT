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
                    
                    user_input = message.content

                    # --- [v10.2.2] 语音消息预处理逻辑 (增强模糊匹配) ---
                    if message.content.startswith("[语音]"):
                        try:
                            logger.info(f"🎤 正在接收并转录语音消息 [{message.content}] 来自 [{message.sender}]...")
                            # 1. 发送中间状态反馈
                            sender.sendMessage(message.sender, f"🎤 正在聆听您的语音({message.content.replace('[语音]', '')})，请稍候...")
                            
                            # 2. 调用 wxauto 保存语音
                            import os
                            temp_dir = os.path.join(conf.project_root, "temp", "voice")
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # 保存语音文件 (wxauto 的 msg 对象 SaveVoice 方法)
                            save_path = message.raw.SaveVoice(savepath=temp_dir)
                            if not save_path or not os.path.exists(save_path):
                                # 某些版本 SaveVoice 不返回路径，需根据文件类型寻找
                                logger.warning("SaveVoice 未返回路径，尝试在目录中搜索最新文件")
                                files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
                                if files:
                                    save_path = max(files, key=os.path.getmtime)
                            
                            if save_path and os.path.exists(save_path):
                                logger.info(f"语音已保存: {save_path}")
                                
                                # 3. 调用工具进行识别
                                from tools.default import recognize_speech_from_audio
                                res = recognize_speech_from_audio(save_path)
                                
                                if res.get("status") == "success":
                                    user_input = res.get("recognized_text", "")
                                    logger.info(f"语音识别成功: {user_input}")
                                    # 再次反馈识别结果
                                    sender.sendMessage(message.sender, f"👂 我听到了: \"{user_input}\"")
                                else:
                                    error_msg = res.get("message", "识别失败")
                                    logger.error(f"语音识别失败: {error_msg}")
                                    sender.sendMessage(message.sender, f"❌ 语音识别失败: {error_msg}")
                                    msg_queue.task_done()
                                    continue
                            else:
                                raise Exception("无法保存语音文件")
                                
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
                        logger.info(f"AI 回复获取成功 [{message.sender}]，长度: {len(reply) if reply else 0}")
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
                            sender.sendMessage(
                                receiver=message.sender,
                                content=reply,
                            )
                            logger.info(f"✅ 回复已发送给 [{message.sender}]")
                            # 记录到每日消息日志
                            daily_logger.info(f"[{message.sender}] {reply}")
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
