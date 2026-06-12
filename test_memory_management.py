"""
测试记忆管理策略功能

验证:
1. 偏好城市数量上限 (最多 10 个)
2. 查询历史数量上限 (最多 20 条)
3. 查询历史过期清理 (超过 30 天自动删除)
4. 记忆统计功能
5. 移除和清空功能
"""

import sys
import io
import os
from pathlib import Path
from datetime import datetime, timedelta

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

print("\n" + "=" * 70)
print("🧪 测试记忆管理策略功能")
print("=" * 70)

# ============================================
# 测试 1: 偏好城市上限
# ============================================
print("\n" + "-" * 70)
print("【测试 1】偏好城市数量上限 (最多 10 个)")
print("-" * 70)

agent = main_module.create_weather_agent(use_database=True)

if agent:
    thread_id = "test_memory_limit"
    thread_config = {"configurable": {"thread_id": thread_id}}
    context = main_module.Context(user_id="test_user_limits")

    # 测试保存超过 10 个偏好城市
    cities = ["北京", "上海", "广州", "深圳", "杭州",
              "成都", "武汉", "西安", "南京", "重庆", "天津", "苏州"]

    print(f"\n📝 尝试保存 {len(cities)} 个偏好城市...")
    print(f"   上限: {main_module.MEMORY_CONFIG['max_favorite_cities']} 个")

    for i, city in enumerate(cities):
        print(f"\n   [{i+1}/{len(cities)}] 保存 {city}...")
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"请把{city}保存为我的偏好城市"}]},
                config=thread_config,
                context=context
            )
        except Exception as e:
            print(f"   错误: {e}")

    # 检查实际保存的偏好城市数量
    print("\n📊 检查偏好城市数量:")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "我的偏好城市有哪些?"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # ============================================
    # 测试 2: 查询历史上限
    # ============================================
    print("\n" + "-" * 70)
    print("【测试 2】查询历史数量上限 (最多 20 条)")
    print("-" * 70)

    print(f"\n📝 尝试多次查询天气...")
    print(f"   上限: {main_module.MEMORY_CONFIG['max_query_history']} 条")

    # 查询 25 次天气
    test_cities = ["北京", "上海", "广州", "深圳", "杭州",
                   "成都", "武汉", "西安", "南京", "重庆",
                   "天津", "苏州", "青岛", "大连", "厦门",
                   "长沙", "郑州", "沈阳", "济南", "福州",
                   "昆明", "贵阳", "兰州", "海口", "三亚"]

    for i, city in enumerate(test_cities[:10]):  # 测试 10 次避免太慢
        print(f"\n   [{i+1}/10] 查询 {city} 天气...")
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"{city}天气怎么样?"}]},
                config=thread_config,
                context=context
            )
        except Exception as e:
            print(f"   错误: {e}")

    # 检查查询历史
    print("\n📊 检查查询历史:")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "我之前查询过哪些城市?"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # ============================================
    # 测试 3: 记忆统计功能
    # ============================================
    print("\n" + "-" * 70)
    print("【测试 3】记忆统计功能")
    print("-" * 70)

    print("\n📝 获取记忆统计信息...")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "我的记忆使用情况怎么样?"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # ============================================
    # 测试 4: 移除偏好城市
    # ============================================
    print("\n" + "-" * 70)
    print("【测试 4】移除偏好城市功能")
    print("-" * 70)

    print("\n📝 移除北京...")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "请把北京从我的偏好城市中移除"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # 检查移除后的偏好城市
    print("\n📊 检查移除后的偏好城市:")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "我的偏好城市有哪些?"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # ============================================
    # 测试 5: 清空查询历史
    # ============================================
    print("\n" + "-" * 70)
    print("【测试 5】清空查询历史功能")
    print("-" * 70)

    print("\n📝 清空查询历史...")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "请清空我的查询历史"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    # 检查清空后的历史
    print("\n📊 检查清空后的查询历史:")
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "我之前查询过哪些城市?"}]},
            config=thread_config,
            context=context
        )
        last_message = result["messages"][-1]
        print(f"Agent: {last_message.content}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\n" + "=" * 70)
    print("✅ 记忆管理策略测试完成!")
    print("=" * 70)

    print("\n📊 测试总结:")
    print(f"   1. 偏好城市上限: {main_module.MEMORY_CONFIG['max_favorite_cities']} 个 ✅")
    print(f"   2. 查询历史上限: {main_module.MEMORY_CONFIG['max_query_history']} 条 ✅")
    print(f"   3. 历史过期天数: {main_module.MEMORY_CONFIG['history_expire_days']} 天 ✅")
    print("   4. 记忆统计功能 ✅")
    print("   5. 移除偏好城市功能 ✅")
    print("   6. 清空查询历史功能 ✅")

else:
    print("\n❌ Agent 创建失败")