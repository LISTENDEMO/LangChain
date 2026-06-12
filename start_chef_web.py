"""
AI 私厨 Web 界面启动脚本
"""

import subprocess
import sys
import os

# 设置环境
os.chdir(r"G:\claude code\.claude\LangChain")

# 启动命令
cmd = ["uv", "run", "python", "ai_chef_agent.py"]

print("=" * 60)
print("启动 AI 私厨 Web 界面...")
print("=" * 60)
print()
print("请在浏览器中打开: http://127.0.0.1:7860")
print()
print("按 Ctrl+C 停止服务")
print("=" * 60)

# 运行
try:
    subprocess.run(cmd, check=True)
except KeyboardInterrupt:
    print("\n服务已停止")
except Exception as e:
    print(f"\n启动失败: {e}")