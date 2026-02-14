"""
稳定性保障模块

提供异常重试装饰器、微信窗口保活、
全局异常处理等机制确保长时间后台运行。
"""
import time
import functools
from typing import Callable, Any

from utils.logger import logger
from core.config import conf


def retryOnFailure(
    maxRetries: int | None = None,
    delay: float | None = None,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    异常自动重试装饰器

    在目标函数抛出异常时自动重试指定次数，
    每次重试间隔递增（简单指数退避）。

    @param maxRetries 最大重试次数
    @param delay 初始重试延迟（秒）
    @param exceptions 要捕获的异常类型元组
    """
    _max_retries = maxRetries or conf.max_retries
    _delay = delay or conf.retry_delay

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, _max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait_time = _delay * attempt  # 简单线性退避
                    logger.warning(
                        f"[{func.__name__}] 第 {attempt}/{_max_retries} 次重试，"
                        f"等待 {wait_time:.1f}s，错误: {e}"
                    )
                    time.sleep(wait_time)

            logger.error(f"[{func.__name__}] 已达最大重试次数 {_max_retries}，放弃执行")
            raise last_exception  # type: ignore

        return wrapper
    return decorator


def keepAliveWechatWindow(force_focus: bool = True) -> bool:
    """
    确保微信窗口处于可用状态 (IronSentinel 增强版)

    通过 Win32 API 查找微信窗口，
    如果窗口被最小化，则强制恢复。
    
    @param force_focus 是否强制激活并置顶 (用于发送消息前)
    @returns 是否成功激活/找到窗口
    """
    try:
        # [稳定性优化] 在每次窗口操作前，确保 uiautomation 禁用不必要的事件订阅
        # 解决 (-2147220991, '事件无法调用任何订户') 错误
        import uiautomation as auto
        auto.uiautomation.DEBUG_SEARCH_TIME = False
        # 禁用 uiautomation 内部日志，减少 COM 交互触发事件报错的概率
        try:
            auto.uiautomation.DisableLogger()
        except: pass
        
        import win32gui
        import win32con

        hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
        if hwnd:
            # 1. 强制从托盘/最小化状态恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 使用更强力的 SwitchToThisWindow (Win32 特有)
            # 甚至在锁屏或失去焦点时也比 SetForegroundWindow 更有效
            try:
                import ctypes
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
            except: pass

            # 2. 确保窗口是显示的
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            # 3. 按需强力置顶
            if force_focus:
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                    logger.debug("微信窗口已成功激活并强力置顶")
                except Exception as e:
                    logger.debug(f"SetForegroundWindow 受限 (正常现象): {e}")
            
            return True
        else:
            logger.warning("未找到微信窗口，请确保微信已登录且窗口未被完全销毁")
            return False

    except Exception as e:
        logger.error(f"窗口状态检查失败: {e}")
        return False


def setupGlobalExceptionHandler() -> None:
    """
    设置全局未捕获异常处理钩子

    防止未预期的异常导致程序直接退出，
    而是记录错误日志后继续运行。
    """
    import sys
    import threading

    def _handleUncaughtException(
        excType: type,
        excValue: BaseException,
        excTraceback: Any,
    ) -> None:
        if issubclass(excType, KeyboardInterrupt):
            # 允许 Ctrl+C 正常退出
            sys.__excepthook__(excType, excValue, excTraceback)
            return
        logger.critical(
            f"未捕获的异常: {excType.__name__}: {excValue}",
            exc_info=(excType, excValue, excTraceback),
        )

    def _handleThreadException(args: threading.ExceptHookArgs) -> None:
        if args.exc_type is not None and issubclass(args.exc_type, KeyboardInterrupt):
            return
        logger.critical(
            f"线程 [{args.thread}] 未捕获异常: {args.exc_type}: {args.exc_value}",
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _handleUncaughtException
    threading.excepthook = _handleThreadException
    logger.info("全局异常处理钩子已安装")
