import sys
import os

# 确保能加载项目模块
sys.path.append(os.getcwd())

from core.config import conf
from wechat.sender import sender

def report():
    msg = (
        "🤖 **IronSentinel Mutation v10.2: 听觉进化启动**\n"
        "--------------------------------\n"
        "ℹ️ 目标: 彻底打通微信语音消息处理闭环。\n"
        "🛠️ 第一步: 正在初始化音频解码环境，并对齐核心处理逻辑。\n"
        "🚀 状态: 方案已锁定，开发中... 请稍候。"
    )
    sender.sendMessage(conf.master_remark, msg)
    print("Report sent.")

if __name__ == "__main__":
    report()
