import sys
import os

sys.path.append(os.getcwd())

from core.config import conf
from wechat.sender import sender

def report():
    msg = (
        "🤖 **IronSentinel v10.2 进度更新**\n"
        "--------------------------------\n"
        "✅ 监听层拦截: 已成功打通，语音不再被误判为普通文字。\n"
        "🛠️ 正在进行: 消息处理器 `processor.py` 的“音频预处理”逻辑注入。\n"
        "📈 下一步: 整合 ffmpeg 自动降噪转码，实现语音即兴对话。\n"
        "🚀 状态: 研发进度 70%... 即将进入测试热启动阶段。"
    )
    sender.sendMessage(conf.master_remark, msg)

if __name__ == "__main__":
    report()
