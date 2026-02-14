import threading

# 全局 UI 锁，用于协调对微信窗口的独占操作
# 发送消息、切换窗口、窗口保活等涉及 UI 焦点和键盘鼠标的操作都应申请此锁
ui_lock = threading.Lock()
