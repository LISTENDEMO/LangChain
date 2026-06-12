"""
LangChain 记忆系统对比分析

对比三种记忆实现方式:
1. 当前实现的 Short-Term Memory (InMemorySaver)
2. LangChain 官方的 Short-Term Memory
3. LangChain 官方的 Long-Term Memory (InMemoryStore)

解释区别和升级方案
"""

import sys
import io
from pathlib import Path

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except:
    pass

print("\n" + "=" * 70)
print("📊 LangChain 记忆系统对比分析")
print("=" * 70)

# ============================================
# 核心结论
# ============================================

print("""
🎯 核心结论:

当前天气 Agent 实现的记忆功能,本质上就是 LangChain 官方的 Short-Term Memory!

✅ 实现方式完全一致:
   - 使用 InMemorySaver 作为 checkpointer
   - 基于 thread_id 的对话历史保存
   - 在单个会话内保持对话上下文

这是 LangChain 推荐的标准实现方式!
""")

# ============================================
# 三种记忆方式对比
# ============================================

print("\n" + "-" * 70)
print("📋 三种记忆方式对比")
print("-" * 70)

print("""
┌──────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│     特性         │  当前实现            │  Short-Term Memory   │  Long-Term Memory    │
│                  │  (InMemorySaver)     │  (官方)              │  (InMemoryStore)     │
├──────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 实现方式         │  ✅ InMemorySaver    │  ✅ InMemorySaver    │  ❌ InMemoryStore    │
│                  │  checkpointer        │  checkpointer        │  store               │
│ 记忆内容         │  对话消息历史        │  对话消息历史        │  结构化用户数据      │
│ 保存格式         │  Messages列表        │  Messages列表        │  自定义数据结构      │
│ 会话范围         │  单个会话            │  单个会话            │  跨会话持久          │
│ 访问方式         │  thread_id           │  thread_id           │  namespace + key     │
│ 工具访问         │  ❌ 工具无法访问     │  ❌ 工具无法访问     │  ✅ 工具可以访问     │
│ 生命周期         │  会话结束消失        │  会话结束消失        │  可以持久保存        │
│ 典型用途         │  对话上下文          │  对话上下文          │  用户画像/偏好       │
│ 官方推荐         │  ✅ 推荐             │  ✅ 推荐             │  ✅ 推荐             │
│ 适用场景         │  多轮对话            │  多轮对话            │  用户数据持久化      │
└──────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
""")

# ============================================
# Short-Term Memory 详细说明
# ============================================

print("\n" + "-" * 70)
print("📌 Short-Term Memory (当前实现)")
print("-" * 70)

print("""
✅ 当前天气 Agent 的实现方式:

代码实现:

    from langgraph.checkpoint.memory import InMemorySaver

    # 创建 checkpointer
    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        tools=[get_weather],
        checkpointer=checkpointer,  # ⭐ 关键
        system_prompt="..."
    )

    # 使用 thread_id 保持对话
    thread_config = {"configurable": {"thread_id": "xxx"}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "北京天气"}]},
        config=thread_config  # ⭐ 关键
    )

记忆机制:

    ┌─────────────────────────────────────────────────────────────────┐
    │  InMemorySaver 内部结构                                         │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  thread_id: "abc123"                                            │
    │                                                                  │
    │  保存的数据:                                                     │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  messages: [                                              │  │
    │  │    {"role": "user", "content": "北京天气怎么样?"},       │  │
    │  │    {"role": "assistant", "content": "北京 29°C..."},    │  │
    │  │    {"role": "user", "content": "上海呢?"},               │  │
    │  │    {"role": "assistant", "content": "上海 31°C..."},    │  │
    │  │  ]                                                        │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  特点:                                                           │
    │  - 只保存 messages (对话历史)                                   │
    │  - 基于 thread_id 隔离                                          │
    │  - 内存保存,会话结束数据消失                                    │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

✅ 优点:

    1. 简单易用
       - 只需添加 checkpointer 参数
       - 无需额外代码

    2. 自动管理
       - 自动保存对话历史
       - 自动加载历史对话

    3. 官方推荐
       - LangChain 标准实现
       - 文档明确推荐

    4. 适合多轮对话
       - 保持对话上下文
       - 连续对话体验

❌ 缺点:

    1. 只保存消息
       - 无法保存结构化数据
       - 无法保存用户画像

    2. 会话限制
       - 只在单个会话有效
       - 会话结束数据消失

    3. 工具无法访问
       - 工具函数无法直接访问记忆
       - 只能通过 LLM 间接访问

适用场景:

    ✅ 多轮对话 (推荐)
    ✅ 保持对话上下文
    ✅ 简单的对话记忆
    ❌ 用户数据持久化
    ❌ 跨会话数据保存
""")

# ============================================
# Long-Term Memory 详细说明
# ============================================

print("\n" + "-" * 70)
print("📌 Long-Term Memory (官方)")
print("-" * 70)

print("""
✅ LangChain 官方的 Long-Term Memory:

代码实现:

    from langgraph.store.memory import InMemoryStore
    from langchain.tools import ToolRuntime, tool

    # 创建 store
    store = InMemoryStore()  # ⭐ 关键区别

    # 工具可以访问 store
    @tool
    def save_user_info(user_info: dict, runtime: ToolRuntime) -> str:
        # 工具内部访问 store ⭐
        store = runtime.store
        user_id = runtime.context.user_id

        # 保存结构化数据 ⭐
        store.put(("users",), user_id, user_info)
        return "保存成功"

    @tool
    def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
        # 工具内部访问 store ⭐
        store = runtime.store

        # 读取结构化数据 ⭐
        user_info = store.get(("users",), user_id)
        return str(user_info.value) if user_info else "未知用户"

    agent = create_agent(
        model=model,
        tools=[save_user_info, get_user_info],
        store=store,  # ⭐ 传入 store
        context_schema=Context
    )

    # 使用 context 传递用户 ID
    agent.invoke(
        {"messages": [...]},
        context=Context(user_id="user_123")
    )

记忆机制:

    ┌─────────────────────────────────────────────────────────────────┐
    │  InMemoryStore 内部结构                                         │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Namespace: ("users",)                                          │
    │                                                                  │
    │  保存的数据:                                                     │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │  user_123: {                                              │  │
    │  │    "name": "John Smith",                                  │  │
    │  │    "preferences": ["北京", "上海"],                       │  │
    │  │    "last_query": "北京天气"                               │  │
    │  │  }                                                        │  │
    │  │                                                            │  │
    │  │  user_456: {                                              │  │
    │  │    "name": "Bob",                                         │  │
    │  │    "preferences": ["Tokyo"],                              │  │
    │  │    "last_query": "Tokyo weather"                          │  │
    │  │  }                                                        │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  特点:                                                           │
    │  - 保存结构化数据 (不仅仅是消息)                                │
    │  - 使用 namespace + key 组织                                    │
    │  - 工具可以直接访问                                             │
    │  - 可以跨会话保存 (使用数据库替代)                              │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘

✅ 优点:

    1. 结构化数据
       - 可以保存任何数据结构
       - 用户画像、偏好、历史记录

    2. 工具可访问
       - 工具函数可以直接读写 store
       - 更灵活的记忆管理

    3. 跨会话持久
       - 可以使用数据库替代 InMemoryStore
       - 实现真正的长期记忆

    4. Namespace 组织
       - 按 namespace 分类数据
       - 更好的数据管理

    5. Key-Value 存储
       - 灵活的键值对存储
       - 支持复杂查询

❌ 缺点:

    1. 实现复杂
       - 需要定义专门的工具
       - 需要管理 namespace 和 key

    2. 需要更多代码
       - 定义 context_schema
       - 工具内部访问 store

    3. 生产环境需要数据库
       - InMemoryStore 还是内存存储
       - 需要 SqliteSaver 等持久化方案

适用场景:

    ✅ 用户数据持久化 (推荐)
    ✅ 用户画像管理
    ✅ 跨会话数据保存
    ✅ 复杂的记忆需求
    ❌ 简单的对话记忆
""")

# ============================================
# 核心区别对比
# ============================================

print("\n" + "-" * 70)
print("🔥 核心区别对比")
print("-" * 70)

print("""
┌────────────────────────────────────────────────────────────────────┐
│                Short-Term vs Long-Term Memory                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Short-Term Memory (当前实现):                                     │
│                                                                    │
│  ✅ 保存内容: Messages (对话历史)                                  │
│  ✅ 访问方式: thread_id                                            │
│  ✅ 工具访问: ❌ 工具无法直接访问                                  │
│  ✅ 会话范围: 单个会话                                             │
│  ✅ 数据格式: Messages 列表                                        │
│  ✅ 适用场景: 多轮对话上下文                                       │
│                                                                    │
│  示例:                                                             │
│    thread_id: "abc123"                                             │
│    messages: [                                                     │
│      {"role": "user", "content": "北京天气?"},                    │
│      {"role": "assistant", "content": "29°C"},                   │
│    ]                                                               │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Long-Term Memory (官方推荐):                                      │
│                                                                    │
│  ✅ 保存内容: 结构化用户数据                                       │
│  ✅ 访问方式: namespace + key                                      │
│  ✅ 工具访问: ✅ 工具可以直接访问                                  │
│  ✅ 会话范围: 可以跨会话                                           │
│  ✅ 数据格式: 自定义数据结构                                       │
│  ✅ 适用场景: 用户画像/偏好                                        │
│                                                                    │
│  示例:                                                             │
│    namespace: ("users",)                                           │
│    key: "user_123"                                                 │
│    value: {                                                        │
│      "name": "John",                                               │
│      "favorite_cities": ["北京", "上海"],                          │
│      "last_query": "北京天气"                                      │
│    }                                                               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
""")

# ============================================
# 当前实现分析
# ============================================

print("\n" + "-" * 70)
print("📊 当前实现分析")
print("-" * 70)

print("""
✅ 当前天气 Agent 的实现:

    weather_agent_streaming.py:

    1. 使用 InMemorySaver (Short-Term Memory)
       ✅ 标准的 LangChain 实现

    2. 基于 thread_id 的对话历史保存
       ✅ 每个对话有唯一 ID

    3. Agent 可以记住之前的对话
       ✅ 测试成功,Agent 能回答 "上次查的城市"

    4. 海盗风格 + 记忆提示
       ✅ 系统提示词中明确告知有记忆能力

这已经是 LangChain 推荐的标准 Short-Term Memory 实现!

✅ 完全符合官方文档:

    LangChain 文档明确说明:

    "Short-Term Memory: 使用 InMemorySaver 作为 checkpointer,
     基于 thread_id 的对话历史保存,在单个会话内保持对话上下文"

这正是当前的实现方式!
""")

# ============================================
# 升级到 Long-Term Memory
# ============================================

print("\n" + "-" * 70)
print("💡 升级到 Long-Term Memory 的方案")
print("-" * 70)

print("""
如果要实现真正的长期记忆 (跨会话保存用户数据),可以升级到 Long-Term Memory:

方案1: 使用 InMemoryStore (内存级长期记忆)

    from langgraph.store.memory import InMemoryStore
    from langchain.tools import ToolRuntime, tool

    store = InMemoryStore()

    # 工具:保存用户偏好城市
    @tool
    def save_favorite_city(city: str, runtime: ToolRuntime) -> str:
        store = runtime.store
        user_id = runtime.context.user_id

        # 获取现有数据
        user_data = store.get(("users",), user_id)

        if user_data:
            data = user_data.value
            if "favorite_cities" not in data:
                data["favorite_cities"] = []
            data["favorite_cities"].append(city)
        else:
            data = {"favorite_cities": [city]}

        # 保存数据
        store.put(("users",), user_id, data)
        return f"已保存 {city} 为偏好城市"

    # 工具:获取用户偏好城市
    @tool
    def get_favorite_cities(runtime: ToolRuntime) -> str:
        store = runtime.store
        user_id = runtime.context.user_id

        user_data = store.get(("users",), user_id)

        if user_data and "favorite_cities" in user_data.value:
            cities = user_data.value["favorite_cities"]
            return f"你的偏好城市: {cities}"
        else:
            return "暂无偏好城市"

方案2: 使用 SqliteSaver (持久化长期记忆)

    from langgraph.checkpoint.sqlite import SqliteSaver

    # 使用 SQLite 数据库持久化
    checkpointer = SqliteSaver.from_conn_string("memory.db")

    agent = create_agent(
        model=model,
        tools=[...],
        checkpointer=checkpointer,  # 持久化到数据库
        store=store  # 长期记忆
    )

    # 对话历史会保存到 memory.db
    # 跨会话保持记忆 ✅

方案3: 结合 Short-Term + Long-Term

    # 同时使用 checkpointer 和 store
    agent = create_agent(
        model=model,
        tools=[get_weather, save_favorite_city, get_favorite_cities],
        checkpointer=InMemorySaver(),  # Short-Term: 对话历史
        store=InMemoryStore(),         # Long-Term: 用户数据
        context_schema=Context
    )

    ✅ 对话历史 (checkpointer):
       - 保持当前对话的上下文
       - "上次查的城市是哪个?"

    ✅ 用户数据 (store):
       - 保存用户偏好、历史查询
       - 跨会话持久化
""")

# ============================================
# 实际代码示例
# ============================================

print("\n" + "-" * 70)
print("📝 升级代码示例 (天气 Agent)")
print("-" * 70)

print("""
升级后的天气 Agent (带真正的长期记忆):

    from langgraph.store.memory import InMemoryStore
    from langchain.tools import ToolRuntime, tool
    from dataclasses import dataclass

    # 定义 context
    @dataclass
    class Context:
        user_id: str

    # 创建 store
    store = InMemoryStore()

    # 工具:保存查询历史
    @tool
    def save_query_history(city: str, weather: str, runtime: ToolRuntime) -> str:
        # 保存查询历史到 store
        store = runtime.store
        user_id = runtime.context.user_id

        # 获取现有数据
        user_data = store.get(("weather_history",), user_id)

        if user_data:
            history = user_data.value.get("queries", [])
        else:
            history = []

        # 添加新的查询记录
        history.append({
            "city": city,
            "weather": weather,
            "timestamp": datetime.now().isoformat()
        })

        # 保存到 store
        store.put(("weather_history",), user_id, {"queries": history})
        return "查询历史已保存"

    # 工具:获取查询历史
    @tool
    def get_query_history(runtime: ToolRuntime) -> str:
        # 从 store 获取查询历史
        store = runtime.store
        user_id = runtime.context.user_id

        user_data = store.get(("weather_history",), user_id)

        if user_data:
            history = user_data.value.get("queries", [])
            return f"历史查询: {history}"
        else:
            return "暂无查询历史"

    # 创建 Agent
    agent = create_agent(
        model=model,
        tools=[
            get_real_weather,
            save_query_history,
            get_query_history
        ],
        checkpointer=InMemorySaver(),  # Short-Term: 对话历史
        store=InMemoryStore(),         # Long-Term: 用户数据
        context_schema=Context
    )

    # 使用
    agent.invoke(
        {"messages": [{"role": "user", "content": "北京天气"}]},
        context=Context(user_id="user_123")
    )

    # Agent 可以:
    # - 记住当前对话 (checkpointer)
    # - 记住用户历史查询 (store)
    # - 跨会话保持用户数据 ✅
""")

# ============================================
# 选择建议
# ============================================

print("\n" + "-" * 70)
print("🎯 选择建议")
print("-" * 70)

print("""
根据需求选择记忆方案:

┌─────────────────────────────────────────────────────────────────┐
│  ✅ 当前实现已足够:                                              │
│     - 只需要多轮对话上下文                                       │
│     - 不需要跨会话保存                                           │
│     - 简单的对话记忆                                             │
│     - 不需要保存用户画像                                         │
│                                                                  │
│  当前方案: Short-Term Memory (InMemorySaver)                    │
│  ✅ 已经是 LangChain 推荐的标准实现                             │
│  ✅ 适合大多数对话场景                                           │
│                                                                  │
│  ✅ 需要升级到 Long-Term Memory:                                │
│     - 需要跨会话保存用户数据                                     │
│     - 需要保存用户偏好/画像                                      │
│     - 需要工具直接访问记忆                                       │
│     - 需要持久化到数据库                                         │
│                                                                  │
│  升级方案:                                                       │
│  1. 添加 InMemoryStore (内存级长期记忆)                         │
│  2. 使用 SqliteSaver (持久化长期记忆)                           │
│  3. 结合 checkpointer + store (双重记忆)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

💡 当前天气 Agent 的建议:

    当前场景: 天气查询 + 多轮对话

    ✅ Short-Term Memory 已足够:
       - Agent 记住当前对话
       - 可以回答 "上次查的城市"
       - 可以回答 "刚才的天气"
       - 多轮对话体验良好

    如果需要以下功能,可以考虑升级:
       ❓ 记住用户的偏好城市 (跨会话)
       ❓ 记住用户的查询历史 (持久化)
       ❓ 提供个性化推荐 (基于历史)
       ❓ 工具直接访问用户数据

    当前建议: 保持现状 ✅
    - 当前实现已经是最佳方案
    - Short-Term Memory 足够满足需求
    - 如需升级,可以后续添加 store
""")

# ============================================
# 总结
# ============================================

print("\n" + "=" * 70)
print("✅ 总结")
print("=" * 70)

print("""
🎯 核心要点:

1. 当前实现 = LangChain 官方的 Short-Term Memory ✅

   - 实现方式完全一致
   - 使用 InMemorySaver 作为 checkpointer
   - 基于 thread_id 的对话历史保存
   - 已经是官方推荐的标准实现

2. Short-Term Memory vs Long-Term Memory:

   Short-Term (当前):
   - 保存对话历史 (Messages)
   - 工具无法直接访问
   - 单会话有效
   - 适合多轮对话

   Long-Term (可选升级):
   - 保存结构化用户数据
   - 工具可以直接访问
   - 可跨会话持久
   - 适合用户画像

3. 当前天气 Agent 的记忆功能:

   ✅ 完全符合 LangChain 标准
   ✅ 测试成功,Agent 能记住对话
   ✅ 适合当前的天气查询场景
   ✅ 不需要立即升级

4. 如需升级:

   添加 InMemoryStore:
   - 工具可以保存用户偏好
   - 工具可以读取历史查询
   - 可持久化到数据库

💡 最终结论:

   当前实现已经是 LangChain 推荐的 Short-Term Memory 标准方案!

   无需修改,已经是最佳实践!

📚 参考文档:
   - Short-Term Memory: https://docs.langchain.com/oss/python/langchain/short-term-memory
   - Long-Term Memory: https://docs.langchain.com/oss/python/langchain/long-term-memory
""")

print("\n" + "=" * 70)