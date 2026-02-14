from wxauto import WeChat
import time

def probe():
    wx = WeChat()
    print("已连接微信，请发一段语音到‘文件传输助手’...")
    while True:
        msgs = wx.GetListenMessage()
        if msgs:
            for chat, one_msgs in msgs.items():
                for msg in one_msgs:
                    print(f"Type: {msg.type}, Content: {msg.content}")
                    print(f"Dir: {dir(msg)}")
                    if msg.type == '34' or msg.type == 34 or '[语音]' in msg.content:
                         # 尝试寻找下载方法
                         methods = [m for m in dir(msg) if 'save' in m.lower() or 'download' in m.lower()]
                         print(f"Potential download methods: {methods}")
            break
        time.sleep(1)

if __name__ == "__main__":
    try:
        probe()
    except Exception as e:
        print(f"Error: {e}")
