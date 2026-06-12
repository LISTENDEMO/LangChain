"""
测试 Long-Term Memory 功能
"""

import sys
import io
import os
from pathlib import Path

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except:
    pass

# 加载环境变量
ENV_PATH = r"C:\Users\92099\.claude\.env"
if Path(ENV_PATH).exists():
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

# 导入主模块
import weather_agent_streaming as main_module

# 创建 Agent
print("\n" + "=" * 70)
print("🧪 测试 Long-Term Memory 功能")
print("=" * 70)

agent = main_module.create_weather_agent()

if agent:
    # 运行记忆功能演示
    main_module.run_demo_memory(agent)

    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)
else:
    print("\n❌ Agent 创建失败")