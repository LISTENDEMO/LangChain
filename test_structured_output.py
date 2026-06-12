"""
测试交互式结构化输出
"""

import sys
import io
import os
from pathlib import Path

# 在导入主模块前设置 UTF-8 编码
# 保存原始 stdout/stderr
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception as e:
    # 如果失败,恢复原始设置
    sys.stdout = _original_stdout
    sys.stderr = _original_stderr
    print(f"编码设置失败: {e}")

# 加载 .env 配置
ENV_PATH = r"C:\Users\92099\.claude\.env"
env_file = Path(ENV_PATH)

if env_file.exists():
    print(f"✅ 加载配置文件: {ENV_PATH}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
                print(f"   {key} = {value[:20]}...")

# 导入主程序模块
import weather_agent_streaming as main_module

# 创建 Agent
print("\n" + "=" * 60)
print("🧪 测试交互式结构化输出")
print("=" * 60)

agent = main_module.create_weather_agent()

if agent:
    # 测试结构化输出函数
    print("\n📍 测试城市: 广州")
    main_module.run_agent_structured_output(agent, "广州")

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
else:
    print("\n❌ Agent 创建失败")