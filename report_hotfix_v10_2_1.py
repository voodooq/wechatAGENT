import sys
import os

sys.path.append(os.getcwd())

from core.config import conf
from wechat.sender import sender

def report():
    msg = (
        "🤖 **IronSentinel v10.2.1 紧急热修复**\n"
        "--------------------------------\n"
        "⚠️ 检测到启动异常: 部分消息处理触发 `'function' has no attribute 'get'`。\n"
        "🔍 诊断结果: 新增工具 `recognize_speech_from_audio` 缺失合规装饰器，导致 Agent 大脑解析受挫。\n"
        "🛠️ 正在修复: 正在补全工具链装饰器，并强化异步链路健壮性。\n"
        "🚀 状态: 修复补丁已就绪，即将二次热重启。"
    )
    sender.sendMessage(conf.master_remark, msg)

if __name__ == "__main__":
    report()
