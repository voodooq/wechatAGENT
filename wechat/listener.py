"""
微信消息监听器 (Producer)

在独立线程中轮询微信消息，
过滤白名单后将消息投递到队列。
"""
import time
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.config import conf
from utils.logger import logger, daily_logger
from utils.stability import retryOnFailure, keepAliveWechatWindow
from utils.ui_lock import ui_lock


@dataclass
class WechatMessage:
    """标准化的微信消息对象"""
    sender: str          # 发送者（联系人/群名称）
    content: str         # 消息文本内容
    is_group: bool       # 是否为群消息
    role_level: int      # 权限等级 (RoleLevel)
    room: Optional[str] = None  # 群名称
    timestamp: datetime = field(default_factory=datetime.now)
    raw: object = None   # 原始消息对象，保留备用


# 全局消息队列（线程安全）
msg_queue: queue.Queue[WechatMessage] = queue.Queue(maxsize=100)


class WechatListener:
    """
    微信消息监听器

    使用 wxauto 库监听指定联系人/群的新消息，
    过滤白名单并将消息封装入队。
    """

    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._wx = None
        # [防回环] 启动时标记为首次轮询，用于忽略启动前的历史消息
        self._first_poll = True

    @retryOnFailure(maxRetries=5, delay=3.0)
    def _initWechat(self):
        """
        初始化微信连接 (无锁版)
        调用方必须负责持有 ui_lock，以确保注册监听时的 UI 原子性。
        """
        from wxauto import WeChat
        self._wx = WeChat()
        try:
            self._wx.UiaAPI.SwitchToThisWindow()
        except: pass
        
        logger.info("微信客户端连接成功")

        # 注册监听的联系人/群
        for name in conf.whitelist:
            try:
                # AddListenChat 前先确保窗口状态，减少超时概率
                keepAliveWechatWindow(force_focus=False)
                
                # [FIX] 在尝试 AddListenChat 之前，先使用键盘流搜索激活聊天窗口
                # 这可以确保联系人列表中的控件是可见的
                from utils.wx_interaction import activate_chat_window
                activation_success = activate_chat_window(name)
                
                if not activation_success:
                    logger.warning(f"无法激活聊天窗口 [{name}]，跳过监听注册")
                    continue
                
                # 给微信一点时间让UI稳定
                time.sleep(1.0)
                
                # 尝试注册监听
                self._wx.AddListenChat(who=name)
                logger.info(f"已注册监听: {name}")
            except Exception as e:
                logger.warning(
                    f"⚠️ 无法锁定控件 [{name}] (Find Control Timeout)，"
                    f"已自动切换到‘全局监听模式’。详细错误: {e}"
                )

    def _pollMessages(self):
        """
        轮询消息主循环
        """
        try:
            import pythoncom
            # 在后台线程初始化 COM
            pythoncom.CoInitialize()
            logger.debug("监听器线程 COM 初始化成功")
            
            # 在后台线程实例化微信对象，确保线程亲和性
            with ui_lock:
                self._initWechat()
        except Exception as e:
            logger.error(f"监听器初始化失败: {e}")
            return

        while self._running:
            try:
                with ui_lock:
                    keepAliveWechatWindow(force_focus=False)
                    try:
                        msgs = self._wx.GetListenMessage()
                    except Exception as e:
                        if "(-2147220991" in str(e) or "事件无法调用任何订户" in str(e):
                            logger.error(f"检测到致命 COM 异常 (0x80040201)，正在尝试重置连接: {e}")
                            # 给 COM 系统一点缓冲时间释放资源
                            time.sleep(1.0)
                            # 此时已在 ui_lock 内，安全调用 _initWechat
                            self._initWechat()
                            continue
                        raise e
                
                # 周期性心跳日志 (每 60 轮，约 1 分钟一次)
                if not hasattr(self, '_poll_count'): self._poll_count = 0
                self._poll_count += 1
                if self._poll_count % 60 == 0:
                    logger.info("💓 监听器心跳: 正在轮询新消息...")

                # 诊断日志：每轮轮询结果
                if msgs:
                    # [v8.3 核心修复] 启动“消息风暴”屏蔽 (Full Flush)
                    if self._first_poll:
                        total_chats = len(msgs)
                        logger.warning(f"🚫 启动检测：发现 {total_chats} 个会话存在存量消息，正在执行物理清空...")
                        # 彻底丢弃第一批存量，不进入任何下游逻辑
                        self._first_poll = False
                        continue 
                    
                    logger.debug(f"[诊断] GetListenMessage 返回 {len(msgs)} 个会话")
                else:
                    if self._first_poll:
                        self._first_poll = False
                
                for chat in msgs:
                    who = chat.who
                    one_msgs = msgs.get(chat, [])
                    
                    if not one_msgs:
                        continue

                    is_group = hasattr(chat, "is_group") and chat.is_group
                    room_name = who if is_group else None

                    # 鉴权
                    from core.security import security_gate, RoleLevel
                    auth_info = security_gate.authenticate(who, room_name)
                    
                    if auth_info.role_level == RoleLevel.STRANGER:
                        continue

                    from wechat.commands import handle_admin_command
                    
                    for msg in one_msgs:
                        msg_type = getattr(msg, 'type', 'UNKNOWN')
                        msg_content = str(getattr(msg, 'content', ''))
                        logger.debug(f"[监听诊断] 收到消息: from={who}, type={msg_type}, content={msg_content[:20]}")
                        
                        # 兼容性获取 is_self
                        msg_is_self = getattr(msg, 'is_self', None)
                        if msg_is_self is None:
                            msg_is_self = (msg_type == 'self')
                        
                        # 2. [核心] 基于指纹的自发消息拦截
                        # 无论是否带签名，只要内容哈希与 AI 最近发送的一致，视为自发消息
                        if msg_is_self:
                            logger.debug(f"🛑 拦截自发消息 (is_self=True): {msg_content[:20]}...")
                            continue
                            
                        # 3. [v12.2] 原子级指纹去重 (视网膜识别)
                        if deduplicator.is_duplicate(who, msg_content, msg_type):
                            logger.debug(f"🛑 拦截重复消息指纹: {msg_content[:20]}...")
                            continue

                        # 拦截常见的系统级消息类型
                        if msg_type in ("time", "sys", "recall"):
                            continue

                        # --- [v10.2] 语音捕获增强 ---
                        if msg_type == 'voice' or msg_type == 34:
                            msg_content = "[语音]"
                            logger.info(f"🎤 捕获到语音消息来自 [{who}]")

                        # 管理指令拦截 (# 开头且由 Root 发出)
                        if auth_info.role_level == RoleLevel.ROOT and msg_content.startswith("#"):
                            if handle_admin_command(msg_content, who):
                                logger.info(f"[诊断] 管理指令已处理: {msg_content}")
                                continue

                        wechat_msg = WechatMessage(
                            sender=who,
                            content=msg_content,
                            is_group=is_group,
                            role_level=auth_info.role_level,
                            room=room_name,
                            raw=msg,
                        )

                        # 入队
                        try:
                            msg_queue.put_nowait(wechat_msg)
                            daily_logger.info(f"[{who}] {msg_content}")
                            logger.info(f"✅ 消息已入队 [{who}]: {msg_content[:50]}...")
                        except queue.Full:
                            msg_queue.get_nowait()
                            msg_queue.put_nowait(wechat_msg)
                            logger.warning("消息队列已满，丢弃最早的消息")

            except Exception as e:
                logger.error(f"消息轮询异常: {e}")
                time.sleep(conf.retry_delay)

            time.sleep(conf.listen_interval)
            
        # 退出循环时释放 COM
        try:
            pythoncom.CoUninitialize()
        except: pass

    def start(self) -> None:
        """启动监听器线程"""
        if self._running:
            logger.warning("监听器已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._pollMessages,
            name="WechatListener",
            daemon=True,
        )
        self._thread.start()
        logger.info("微信监听器已启动")

    def stop(self) -> None:
        """停止监听器"""
        self._running = False
        if self._thread:
            # 不要 join 太久，防止卡死
            self._thread.join(timeout=2)
        logger.info("微信监听器已停止")

    @property
    def isRunning(self) -> bool:
        return self._running
