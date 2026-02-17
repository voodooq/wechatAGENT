import time
import random
import os
from typing import Optional
from threading import local, Lock
from pathlib import Path
from utils.config import conf
from utils.logger import logger
from utils.stability import retryOnFailure, keepAliveWechatWindow
from utils.ui_lock import ui_lock


class WechatSender:
    """
    微信消息发送器
    """

    def __init__(self):
        # 使用线程本地存储，解决 COM 对象跨线程失效问题
        self._local = threading.local()
        # [v8.3] 发送存根：记录最近发送的消息指纹，用于防止自回环
        # 记录 (接收者, 消息内容哈希)
        self._sent_cache = collections.deque(maxlen=100)
        self._cache_lock = threading.Lock()

    def is_recently_sent(self, receiver: str, content: str) -> bool:
        """检查消息是否是最近由 AI 发送的 (支持文本指纹与文件类型识别)"""
        # 兼容性处理：移除换行符和首尾空格进行比对
        clean_content = str(content).strip().replace("\n", "")
        fingerprint = hashlib.md5(clean_content.encode('utf-8')).hexdigest()
        
        with self._cache_lock:
            for r, f in self._sent_cache:
                if r == receiver:
                    # 1. 文本哈希完全匹配
                    if f == fingerprint:
                        return True
                    # 2. [v10.3] 模糊文件匹配：如果 AI 刚刚发送了语音/图片，且内容指纹为占位符
                    if clean_content in ("[语音]", "[图片]", "[视频]", "[文件]") and f == clean_content:
                        return True
        return False

    def _record_sent(self, receiver: str, content: str):
        """记录发送存根 (文本)"""
        clean_content = str(content).strip().replace("\n", "")
        fingerprint = hashlib.md5(clean_content.encode('utf-8')).hexdigest()
        with self._cache_lock:
            self._sent_cache.append((receiver, fingerprint))

    def _record_sent_type(self, receiver: str, msg_type_label: str):
        """记录发送存根 (特殊类型占位符，如语音/图片)"""
        with self._cache_lock:
            self._sent_cache.append((receiver, msg_type_label))

    def _ensureWechat(self):
        """确保当前线程的微信连接可用 (增强 COM 鲁棒性)"""
        try:
            if not hasattr(self._local, 'wx'):
                import pythoncom
                pythoncom.CoInitialize()
                from wxauto import WeChat
                # 在当前线程初始化新的 WeChat 实例
                self._local.wx = WeChat()
            else:
                # 连通性测试：尝试访问 UiaAPI.Name 确保句柄仍然有效
                _ = self._local.wx.UiaAPI.Name
        except Exception as e:
            logger.warning(f"♻️ [COM Guard] 检测到微信句柄失效 ({e})，正在重新初始化...")
            import pythoncom
            pythoncom.CoInitialize()
            from wxauto import WeChat
            self._local.wx = WeChat()

    def _activateChat(self, who: str):
        """
        [重点优化] 搜索并激活指定聊天。
        将核心逻辑委托给 shared utils，便于 listener 复用。
        """
        from utils.wx_interaction import activate_chat_window
        success = activate_chat_window(who)
        
        if not success:
             # 失败后尝试降级回 wxauto 的默认行为（虽然通常也不会成功，但保留原有流程）
            try:
                self._local.wx.ChatWith(who)
            except: pass
            return False
        return True

    @retryOnFailure(maxRetries=3, delay=2.0)
    def sendMessage(self, receiver: str, content: str, context: Optional[str] = None) -> None:
        """
        向指定联系人发送消息（智能版本）
        
        Args:
            receiver: 接收者
            content: 消息内容
            context: 上下文信息（用于智能去重）
        """
        # 智能回复检查
        from core.smart_responder import smart_responder
        should_send, reason = smart_responder.should_send_reply(receiver, content, context)
        
        if not should_send:
            logger.info(f"🚫 智能拦截重复回复 [{receiver}]: {reason}")
            logger.info(f"原计划发送内容: {content[:50]}...")
            return
            
        self._ensureWechat()
        
        # 自动追加 AI 签名，防止回环
        if conf.ai_signature and not content.endswith(conf.ai_signature):
            content = f"{content}{conf.ai_signature}"
        
        try:
            with ui_lock:
                # 在发送前强制聚焦微信窗口
                keepAliveWechatWindow(force_focus=True)
                time.sleep(0.5)
                
                # [优化] 使用更音定的键盘流搜索激活会话
                # 激活后，微信 UI 应该已经定格在 receiver 的聊天窗口
                search_success = self._activateChat(receiver)
                
                wx = self._local.wx
                
                # 随机延迟
                delay = random.uniform(conf.reply_delay_min, conf.reply_delay_max)
                time.sleep(delay)

                # 如果搜索激活成功，我们其实已经处于 receiver 的聊天窗口了
                # 直接调用 SendMsg，如果 wxauto 发现 who 已经是当前窗口，它会执行得更快更稳
                if len(content) > conf.max_message_length:
                    segments = self._splitMessage(content)
                    for i, segment in enumerate(segments):
                        # [稳定性] 确保输入框已就位
                        time.sleep(0.5)
                        # 记录存根，防止回环
                        self._record_sent(receiver, segment)
                        wx.SendMsg(msg=segment, who=receiver)
                        logger.info(f"已发送消息段 {i + 1}/{len(segments)} 给 [{receiver}]")
                        time.sleep(1.0) 
                else:
                    # [核心稳定性修复] 如果之前的键盘流搜索成功，这里会非常快
                    # 如果失败，wxauto 的 SendMsg 会尝试它自己的兜底搜索
                    time.sleep(0.5)
                    self._record_sent(receiver, content)
                    wx.SendMsg(msg=content, who=receiver)
                    logger.info(f"✅ 智能回复已发送给 [{receiver}]，长度: {len(content)}")
                    logger.info(f"发送原因: {reason}")
                    time.sleep(1.0)
                
                # [Fix v10.2.7] 增强缓和 COM 冲突：在 lock 内多留一点“冷却”时间，确保 UI 事件循环清空
                time.sleep(1.0)
        except Exception as e:
            # 遇到 COM 错误或发送失败，强制清理当前线程的微信对象
            # 下次重试时会重新初始化
            if hasattr(self._local, 'wx'):
                del self._local.wx
            logger.warning(f"[sendMessage] 发送异常，已清理微信对象以备重试: {e}")
            raise e

    @retryOnFailure(maxRetries=3, delay=2.0)
    def sendImage(self, receiver: str, image_path: str) -> None:
        """
        向指定联系人发送图片
        """
        self._ensureWechat()
        
        try:
            with ui_lock:
                # 在发送前强制聚焦微信窗口
                keepAliveWechatWindow(force_focus=True)
                
                # [优化] 使用更稳定的键盘流搜索激活会话
                self._activateChat(receiver)
                
                wx = self._local.wx
                
                # 随机延迟
                delay = random.uniform(conf.reply_delay_min, conf.reply_delay_max)
                time.sleep(delay)

                # 发送文件
                self._record_sent_type(receiver, "[图片]")
                wx.SendFiles(filepath=image_path, who=receiver)
                logger.info(f"已发送图片 [{image_path}] 给 [{receiver}]")
                
                time.sleep(1.0) # 核心锁定
                time.sleep(0.2)
        except Exception as e:
            if hasattr(self._local, 'wx'):
                del self._local.wx
            logger.warning(f"[sendImage] 发送异常，已清理微信对象以备重试: {e}")
            raise e

    @retryOnFailure(maxRetries=3, delay=2.0)
    def sendFile(self, receiver: str, file_path: str) -> None:
        """
        向指定联系人发送文件
        """
        self._ensureWechat()
        
        try:
            with ui_lock:
                keepAliveWechatWindow(force_focus=True)
                self._activateChat(receiver)
                wx = self._local.wx
                
                # 随机延迟
                delay = random.uniform(conf.reply_delay_min, conf.reply_delay_max)
                time.sleep(delay)

                # 发送文件
                # 如果是 MP3，优先标记为语音，便于 listener 拦截回环
                type_label = "[语音]" if file_path.lower().endswith(".mp3") else "[文件]"
                self._record_sent_type(receiver, type_label)
                wx.SendFiles(filepath=file_path, who=receiver)
                logger.info(f"已发送文件 [{file_path}] 给 [{receiver}]")
                
                time.sleep(1.0) # 核心锁定
                time.sleep(0.2)
        except Exception as e:
            if hasattr(self._local, 'wx'):
                del self._local.wx
            logger.warning(f"[sendFile] 发送异常，已清理微信对象以备重试: {e}")
            raise e

    def _splitMessage(self, content: str) -> list[str]:
        """
        将长消息按段落智能分割
        """
        max_len = conf.max_message_length
        paragraphs = content.split("\n")
        segments: list[str] = []
        current = ""

        for para in paragraphs:
            # 单段超长时强制截断
            if len(para) > max_len:
                if current:
                    segments.append(current.strip())
                    current = ""
                for i in range(0, len(para), max_len):
                    segments.append(para[i:i + max_len])
                continue

            # 累积段落，超出上限时切分
            if len(current) + len(para) + 1 > max_len:
                segments.append(current.strip())
                current = para
            else:
                current = f"{current}\n{para}" if current else para

        if current.strip():
            segments.append(current.strip())

        return segments


# 全局发送器单例
sender = WechatSender()
