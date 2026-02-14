"""
微信交互工具类 (Shared Utils)

提供通用的微信窗口操作功能，如激活聊天窗口、搜索联系人等。
使用 uiautomation 库实现键盘流操作，比鼠标点击更稳定。
"""
import time
import uiautomation as auto
from utils.logger import logger
from utils.stability import keepAliveWechatWindow

def activate_chat_window(who: str) -> bool:
    """
    搜索并激活指定聊天窗口。
    
    采用键盘流 (Ctrl+F -> Input -> Enter) 替代鼠标点击，
    解决列表滚动或者是窗口未激活导致找不到元素的问题。
    
    Args:
        who (str): 联系人名称或备注
        
    Returns:
        bool: 是否成功激活
    """
    try:
        # [稳定性增强] 设置全局查找超时为较低值
        auto.SetGlobalSearchTimeout(1.0)
        
        wx_window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
        if not wx_window.Exists(0.5):
            logger.warning("未找到或未激活微信主窗口，尝试保活...")
            keepAliveWechatWindow(force_focus=True)
            wx_window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
            if not wx_window.Exists(1.0):
                return False

        # 0. 强力清理：先按两次 Esc，退出任何可能的右键菜单、搜索框残留或弹出层
        wx_window.SendKeys('{Esc}{Esc}', waitTime=0.3)
        
        # 1. 触发搜索 (Ctrl+F)
        wx_window.SendKeys('{Ctrl}f', waitTime=0.3)
        
        # 2. 清除并输入名称
        wx_window.SendKeys('{Ctrl}a{Back}', waitTime=0.2)
        
        # [Fix v10.2.6] 使用剪贴板复制粘贴代替模拟按键，彻底解决中文输入法 (IME) 干扰
        auto.SetClipboardText(who)
        wx_window.SendKeys('{Ctrl}v', waitTime=0.8)
        
        # 3. 回车确认 (激活搜索结果第一项)
        wx_window.SendKeys('{Enter}', waitTime=1.0)
        
        # [NEW] 再次强力清理，确保搜索列表消失，焦点回到输入框
        wx_window.SendKeys('{Esc}', waitTime=0.2)
        
        # [关键] 验证是否真的切换到了指定聊天
        try:
            found = False
            for _ in range(3): # 重试几次验证
                current_chat_name = wx_window.TextControl(searchDepth=15, Name=who)
                if current_chat_name.Exists(0.1):
                    logger.info(f"验证成功：当前会话已指向 [{who}]")
                    found = True
                    break
                time.sleep(0.3)
            
            if not found:
                 logger.warning(f"验证提醒：未能明确在 UI 中验证当前会话为 [{who}]")
        except:
             pass

        logger.info(f"已运行键盘流搜索激活: {who}")
        return True
    except Exception as e:
        logger.error(f"键盘流搜索激活异常 [{who}]: {e}")
        return False
    finally:
        # 恢复默认超时
        auto.SetGlobalSearchTimeout(10.0)
