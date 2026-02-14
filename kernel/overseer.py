import subprocess
import time
import sys
import os

class Overseer:
    """
    IronSentinel 守护内核
    负责维护 Agent 的生命周期、Git 同步以及异常回滚
    """
    def __init__(self):
        self.process = None
        self.crash_count = 0
        self.max_crashes = 3
        self.last_crash_time = 0
        self.agent_path = os.path.join("core", "agent_executor.py") 

    def init_repo(self):
        """初始化仓库连接"""
        if not os.path.exists(".git"):
            print("🔧 [Overseer] 初始化 Git 仓库...")
            subprocess.run(["git", "init"])
            # [重要] 这里由用户在实际部署时配置远程仓库
            print("⚠️ 请确保手动执行: git remote add origin <您的仓库地址>")

    def start_agent(self):
        """启动 AI Agent 主进程"""
        print(f"🚀 [Overseer] 正在启动 IronSentinel Core (Time: {time.strftime('%H:%M:%S')})...")
        # 运行 main.py (包含监听器和处理器)
        self.process = subprocess.Popen([sys.executable, "main.py"])

    def rollback(self):
        """代码写坏了？执行 Git 硬回滚"""
        print("🚑 [Overseer] 检测到持续性崩溃，正在执行‘熔断保护’协议...")
        print("🚑 [Overseer] 正在回滚至上一稳定版本 (Git Rollback)...")
        subprocess.run(["git", "reset", "--hard", "HEAD^"])

    def monitor(self):
        """核心监控循环"""
        self.init_repo()
        self.start_agent()

        while True:
            ret_code = self.process.poll()
            now = time.time()
            
            if ret_code is not None:
                # 100: AI 申请热重载 (代码已进化)
                if ret_code == 100:
                    print("✨ [Overseer] 收到热更新信号，系统正在重启...")
                    self.crash_count = 0
                    time.sleep(1)
                    self.start_agent()
                
                # 999: AI 申请自我隔离 (逻辑失控)
                elif ret_code == 999:
                    print("🔒 [Overseer] AI 触发“自我隔离”保护协议。系统已锁定并停止运行。")
                    break
                
                # 0: 正常退出 (手动关闭)
                elif ret_code == 0:
                    print("👋 [Overseer] 管理员请求退出，守护进程关闭。")
                    break
                
                # 其他: 异常崩溃
                else:
                    self.crash_count += 1
                    print(f"💀 [Overseer] 核心进程异常崩溃 (Code: {ret_code}) | 崩溃计数: {self.crash_count}/{self.max_crashes}")
                    
                    # 崩溃熔断机制 (60秒内崩3次 -> 回滚)
                    if self.crash_count >= self.max_crashes and (now - self.last_crash_time < 60):
                        self.rollback()
                        self.crash_count = 0
                    
                    self.last_crash_time = now
                    print("⏳ 3秒后尝试重启...")
                    time.sleep(3)
                    self.start_agent()
            
            time.sleep(1)

if __name__ == "__main__":
    try:
        Overseer().monitor()
    except KeyboardInterrupt:
        print("\n👋 守护进程已手动停止。")
