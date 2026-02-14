"""
IronSentinel - 图像处理与截图工具
"""
import os
import time
from langchain_core.tools import tool
# import PIL # 移至函数内部实现惰性加载

from wechat.sender import sender
from core.audit import audit_logger
from core.config import conf
from utils.logger import logger

@tool
def capture_and_send_screenshot(user_name: str) -> str:
    """
    截取当前屏幕并发送给用户。
    
    此工具会自动：
    1. 截取主屏幕内容
    2. 保存为临时文件
    3. 通过微信发送给请求的用户
    4. 清理临时文件
    
    Args:
        user_name: 请求截图的用户名称 (接收者)
    """
    try:
        # 1. 截图
        logger.info(f"正在为 [{user_name}] 截取屏幕...")
        try:
            from PIL import ImageGrab
        except ImportError:
            from tools.tools_common import format_error_payload
            return format_error_payload(
                "capture_and_send_screenshot",
                "缺少 Pillow 库环境",
                "请立即调用 install_python_library('Pillow') 修复环境后重试"
            )
        
        screenshot = ImageGrab.grab()
        
        # 2. 保存临时文件
        timestamp = int(time.time())
        temp_dir = conf.project_root / "data" / "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = temp_dir / f"screenshot_{timestamp}.png"
        screenshot.save(file_path)
        logger.info(f"截图已保存至: {file_path}")
        
        # 3. 发送图片
        sender.sendImage(user_name, str(file_path))
        
        # 4. 记录审计日志
        audit_logger.log_action(user_name, "CAPTURE_SCREENSHOT", "SUCCESS")
        
        return "✅ 屏幕截图已获取并发送给您，请查看微信图片。"
        
    except Exception as e:
        logger.error(f"截图失败: {e}")
        audit_logger.log_action(user_name, "CAPTURE_SCREENSHOT", "FAIL")
        return f"❌ 截图失败: {e}"
