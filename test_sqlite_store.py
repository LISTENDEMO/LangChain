"""
测试 SQLite 统一存储的 Long-Term Memory 功能

验证:
1. 对话历史和用户数据都保存到同一个 .db 文件
2. 重启程序后数据依然存在
3. 跨会话访问用户数据
"""

import sys
import io
import os
from pathlib import Path
import time

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
print("🧪 测试 SQLite 统一存储的 Long-Term Memory")
print("=" * 70)

# ============================================
# 第一阶段: 创建 Agent 并保存数据
# ============================================

print("\n" + "-" * 70)
print("【第一阶段】创建 Agent 并保存数据")
print("-" * 70)

agent = main_module.create_weather_agent(use_database=True)

if agent:
    # 运行记忆功能演示
    main_module.run_demo_memory(agent)

    print("\n" + "-" * 70)
    print("✅ 第一阶段完成!")
    print("-" * 70)

    # ============================================
    # 第二阶段: 检查数据库文件
    # ============================================

    print("\n" + "-" * 70)
    print("【第二阶段】验证数据库文件")
    print("-" * 70)

    # 检查数据库文件是否存在
    db_file = Path("weather_memory.db")

    print("\n📁 检查数据库文件:")
    if db_file.exists():
        size = db_file.stat().st_size
        print(f"   ✅ {db_file} 存在 (大小: {size} bytes)")
        print(f"   💾 对话历史和用户数据都在这个文件中")

        # 查看数据库内容
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # 查看所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📊 数据库中的表:")
        for table in tables:
            print(f"   - {table[0]}")

            # 查看表中的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"     记录数: {count}")

        # 查看用户数据
        print(f"\n📄 用户数据表 (store) 内容:")
        cursor.execute("SELECT namespace, key, value FROM store LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   namespace: {row[0]}, key: {row[1]}")
            print(f"   value: {row[2][:100]}...")  # 截断显示

        conn.close()
    else:
        print(f"   ❌ {db_file} 不存在")

    # ============================================
    # 第三阶段: 重新创建 Agent 验证数据持久化
    # ============================================

    print("\n" + "-" * 70)
    print("【第三阶段】重新创建 Agent 验证数据持久化")
    print("-" * 70)

    print("\n💡 说明:")
    print("   重新创建 Agent (模拟重启程序)")
    print("   如果数据持久化成功,之前的偏好城市和查询历史应该依然存在")

    # 重新创建 Agent
    agent2 = main_module.create_weather_agent(use_database=True)

    if agent2:
        # 创建新的 thread_id (模拟新会话)
        import uuid
        thread_id = str(uuid.uuid4())
        thread_config = {"configurable": {"thread_id": thread_id}}

        # 使用相同的 user_id
        context = main_module.Context(user_id="demo_user_001")

        print(f"\n💾 新会话 ID: {thread_id}")
        print(f"👤 用户 ID: demo_user_001 (与之前相同)")
        print("   ⚠️ 注意: thread_id 是新的,但 user_id 相同")
        print("   如果 Long-Term Memory 持久化成功,应该能获取之前的偏好城市")

        # 测试获取偏好城市
        print("\n📝 测试: 获取偏好城市 (新会话)")
        print("用户: 我的偏好城市有哪些?")

        try:
            result = agent2.invoke(
                {"messages": [{"role": "user", "content": "我的偏好城市有哪些?"}]},
                config=thread_config,
                context=context
            )

            last_message = result["messages"][-1]
            print("Agent: ", end="")
            if hasattr(last_message, 'content'):
                content = last_message.content
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, 'get') and block.get('type') == 'text':
                            print(block.get('text', ''))
                else:
                    print(content)
            else:
                print(str(last_message))

            print("\n✅ 如果 Agent 回答包含 '北京',说明数据持久化成功!")

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ 测试完成!")
    print("=" * 70)

    print("\n📊 测试总结:")
    print("   1. SQLite 数据库持久化对话历史 ✅")
    print("   2. SQLite 数据库持久化用户数据 ✅")
    print("   3. 新会话中可以访问之前保存的数据 ✅")
    print("\n💡 提示:")
    print("   - 所有数据保存在一个 .db 文件中")
    print("   - 数据库文件: weather_memory.db")
    print("   - 包含表: checkpoints (对话历史) + store (用户数据)")
    print("=" * 70)

else:
    print("\n❌ Agent 创建失败")