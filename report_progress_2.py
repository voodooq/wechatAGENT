import sys
import os

sys.path.append(os.getcwd())

from core.config import conf
from wechat.sender import sender

def report():
    msg = (
        "🤖 **IronSentinel v10.2 进度更新**\n"
        "--------------------------------\n"
        "✅ 监听端升级完成: 已能捕获并锁定原始语音消息。\n"
        "🛠️ 正在进行: 音频解码组件 (`pilk/ffmpeg`) 的环境适配与逻辑注入。\n"
        "📈 下一步: 修改处理器 `processor.py` 实现自动下载并转写。\n"
        "🚀 状态: 正常推进中。"
    )
    sender.sendMessage(conf.master_remark, msg)

if __name__ == "__main__":
    report()
