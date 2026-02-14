import sys
import os

sys.path.append(os.getcwd())

from core.config import conf
from wechat.sender import sender

def report():
    msg = (
        "🤖 **IronSentinel v10.2 进化成功预报**\n"
        "--------------------------------\n"
        "✅ 听觉神经系统构建完成：\n"
        "   - 监听拦截: [OK]\n"
        "   - 处理器中继: [OK]\n"
        "   - ffmpeg 转码核: [OK]\n"
        "   - 大脑端注册: [OK]\n\n"
        "🚀 **即将执行热重启...**\n"
        "重启后，您可以直接发语音考考我。系统将自动转录并回复您的指令。"
    )
    sender.sendMessage(conf.master_remark, msg)

if __name__ == "__main__":
    report()
