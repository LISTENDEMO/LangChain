"""
测试 JsonFileStore 类
"""

import sys
import io

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except:
    pass

from weather_agent_streaming import JsonFileStore
from pathlib import Path

print("\n" + "=" * 70)
print("测试 JsonFileStore 类")
print("=" * 70)

# 创建 store
print("\n1. 创建 JsonFileStore:")
store = JsonFileStore("test_store.json")

# 测试 put
print("\n2. 测试 put 方法:")
store.put(("users",), "user_001", {"name": "张三", "favorite_cities": ["北京"]})

# 测试 get
print("\n3. 测试 get 方法:")
result = store.get(("users",), "user_001")
if result:
    print(f"   获取成功: {result.value}")
else:
    print("   获取失败")

# 检查文件是否存在
print("\n4. 检查文件:")
json_file = Path("test_store.json")
if json_file.exists():
    print(f"   ✅ 文件存在")
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"   内容:\n{content}")
else:
    print(f"   ❌ 文件不存在")

print("\n" + "=" * 70)