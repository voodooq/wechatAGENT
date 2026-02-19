#!/usr/bin/env python3
"""
OpenClaw 连接诊断工具
检查配置、端口和服务状态
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import conf

print("=" * 60)
print("🔍 OpenClaw 连接诊断")
print("=" * 60)

# 1. 检查配置
print("\n📋 配置检查:")
print(f"  OPENCLAW_MODE: {conf.openclaw_mode}")
print(f"  OPENCLAW_ENABLED: {conf.openclaw_enabled}")
print(f"  LLM_PROVIDER: {conf.llm_provider}")

# 检查 HTTP API 配置
if hasattr(conf, 'openclaw_http_api'):
    print(f"  OPENCLAW_HTTP_API: {conf.openclaw_http_api}")
else:
    print(f"  OPENCLAW_HTTP_API: 未配置 (默认: http://localhost:9848)")

# 2. 检查环境变量
print("\n🌍 环境变量检查:")
print(f"  OPENCLAW_MODE: {os.getenv('OPENCLAW_MODE', '未设置')}")
print(f"  OPENCLAW_ENABLED: {os.getenv('OPENCLAW_ENABLED', '未设置')}")
print(f"  OPENCLAW_HTTP_API: {os.getenv('OPENCLAW_HTTP_API', '未设置')}")

# 3. 检查端口状态
print("\n🔌 端口检查:")
import socket

def check_port(host, port, name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"  ✅ {name} ({host}:{port}) - 正在运行")
            return True
        else:
            print(f"  ❌ {name} ({host}:{port}) - 未运行")
            return False
    except Exception as e:
        print(f"  ⚠️  {name} ({host}:{port}) - 检查失败: {e}")
        return False
    finally:
        sock.close()

bridge_running = check_port("localhost", 9847, "Bridge Server")
http_bridge_running = check_port("localhost", 9848, "HTTP Bridge Server")

# 4. 测试连接
print("\n🧪 连接测试:")

async def test_connection():
    mode = conf.openclaw_mode
    
    if mode == 'bridge':
        api_base = "http://localhost:9847"
    elif mode == 'http':
        api_base = getattr(conf, 'openclaw_http_api', 'http://localhost:9848')
    else:
        print(f"  跳过连接测试 (模式: {mode})")
        return
    
    print(f"  测试 {api_base}/health ...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_base}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  ✅ 连接成功!")
                    print(f"     状态: {data.get('status', 'unknown')}")
                    print(f"     模式: {data.get('mode', 'unknown')}")
                else:
                    print(f"  ❌ 连接失败: HTTP {resp.status}")
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")

asyncio.run(test_connection())

# 5. 提供解决方案
print("\n💡 解决方案:")

if not bridge_running and not http_bridge_running:
    print("  没有检测到任何 Bridge 服务器在运行!")
    print("")
    print("  请启动对应的服务器:")
    print("  1. Bridge 模式 (默认, 端口 9847):")
    print("     python bridge_server.py")
    print("")
    print("  2. HTTP Bridge 模式 (端口 9848):")
    print("     python http_bridge_server.py")
    print("")
    print("  3. 或者切换到 File 模式 (无需服务器):")
    print("     在 .env 中设置: OPENCLAW_MODE=file")
elif conf.openclaw_mode == 'bridge' and not bridge_running:
    print("  配置为 Bridge 模式，但 Bridge Server (9847) 未运行!")
    print("  请运行: python bridge_server.py")
elif conf.openclaw_mode == 'http' and not http_bridge_running:
    print("  配置为 HTTP 模式，但 HTTP Bridge Server (9848) 未运行!")
    print("  请运行: python http_bridge_server.py")
else:
    print("  配置和服务器状态看起来正常。")
    print("  如果仍有问题，请检查:")
    print("  1. 防火墙是否阻挡了端口")
    print("  2. 是否有其他程序占用了端口")
    print("  3. 查看服务器日志是否有错误")

print("\n" + "=" * 60)
