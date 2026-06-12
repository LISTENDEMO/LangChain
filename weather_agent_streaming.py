"""
LangChain 天气查询 Agent - 流式输出版本 + 结构化输出 + 长期记忆

功能特性:
- 实时显示 Agent 的思考过程和回复
- 支持结构化天气报告输出 (JSON格式)
- 长期记忆功能 (InMemorySaver)
- Agent 可以记住之前的对话内容
- 海盗风格的天气助手
"""

import sys
import io
import os
import json
import sqlite3
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime

# 设置 UTF-8 输出编码 (只在需要时)
def setup_utf8_encoding():
    """设置 UTF-8 输出编码"""
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except:
            pass  # 如果失败就保持原样

# 只在直接运行时设置编码
if __name__ == "__main__":
    setup_utf8_encoding()

# ============================================
# 加载 .env 配置
# ============================================

def load_env_file(env_path: str):
    """手动加载 .env 文件"""
    env_file = Path(env_path)

    if not env_file.exists():
        print(f"⚠️  .env 文件不存在: {env_path}")
        return False

    print(f"✅ 加载配置文件: {env_path}")

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

    return True


ENV_PATH = r"C:\Users\92099\.claude\.env"

# 只在直接运行时加载环境变量
if __name__ == "__main__":
    load_env_file(ENV_PATH)


# ============================================
# 定义结构化输出模型
# ============================================

class WeatherReport(BaseModel):
    """结构化天气报告"""
    city: str = Field(description="城市名称")
    temperature: int = Field(description="当前温度(摄氏度)")
    weather_condition: str = Field(description="天气状况描述")
    humidity: int = Field(description="湿度百分比")
    wind_speed: int = Field(description="风速(公里/小时)")
    wind_direction: str = Field(description="风向")
    pressure: int = Field(description="气压(百帕)")
    recommendation: str = Field(description="天气建议")
    pirate_message: str = Field(description="海盗风格的整体消息")


class WeatherComparison(BaseModel):
    """多城市天气对比"""
    reports: list[WeatherReport] = Field(description="各城市天气报告")
    best_city: str = Field(description="最适合活动的城市")
    comparison_summary: str = Field(description="对比总结")


# ============================================
# 定义 Context (用于 Long-Term Memory)
# ============================================

@dataclass
class Context:
    """用户上下文,用于传递 user_id"""
    user_id: str


# ============================================
# SQLite 存储类 (持久化用户数据到数据库)
# ============================================

class SqliteStore:
    """SQLite 数据库存储 - 持久化用户数据到数据库文件

    实现 LangGraph Store 接口，将长期记忆数据保存到 SQLite 数据库
    数据保存在同一个 .db 文件中，统一管理
    """

    def __init__(self, db_path: str = "memory_store.db"):
        """初始化 SQLite 存储

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup()
        print(f"   ✅ SQLite 存储已启用: {db_path}")

    def _setup(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (namespace, key)
            )
        """)
        self.conn.commit()

    def put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
        """存储数据到数据库

        Args:
            namespace: 命名空间 (如 ("users",))
            key: 键 (如 "user_123")
            value: 数据值
        """
        ns_key = "/".join(namespace)
        value_json = json.dumps(value, ensure_ascii=False)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO store (namespace, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (ns_key, key, value_json))
        self.conn.commit()

        print(f"   💾 已保存到数据库: namespace={ns_key}, key={key}")

    def get(self, namespace: tuple[str, ...], key: str) -> Optional[Any]:
        """从数据库获取数据

        Args:
            namespace: 命名空间
            key: 键

        Returns:
            StoreItem 对象 (包含 value 属性) 或 None
        """
        ns_key = "/".join(namespace)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value FROM store WHERE namespace = ? AND key = ?
        """, (ns_key, key))

        row = cursor.fetchone()
        if row:
            class StoreItem:
                def __init__(self, value):
                    self.value = value

            return StoreItem(json.loads(row[0]))

        return None

    def search(self, namespace: tuple[str, ...], query: str = "", limit: int = 10) -> list:
        """搜索数据

        Args:
            namespace: 命名空间
            query: 搜索查询 (忽略)
            limit: 返回数量限制

        Returns:
            匹配的项目列表
        """
        ns_key = "/".join(namespace)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT key, value FROM store WHERE namespace = ? LIMIT ?
        """, (ns_key, limit))

        results = []
        for row in cursor.fetchall():
            class StoreItem:
                def __init__(self, key, value):
                    self.key = key
                    self.value = value

            results.append(StoreItem(row[0], json.loads(row[1])))

        return results

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        """删除数据

        Args:
            namespace: 命名空间
            key: 键
        """
        ns_key = "/".join(namespace)

        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM store WHERE namespace = ? AND key = ?
        """, (ns_key, key))
        self.conn.commit()

        print(f"   🗑️ 已删除: namespace={ns_key}, key={key}")

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


# ============================================
# SQLite 检查点存储 (持久化对话历史)
# ============================================

def get_sqlite_checkpointer(db_path: str = "weather_memory.db"):
    """获取 SQLite 检查点存储 (统一数据库文件)

    Args:
        db_path: SQLite 数据库文件路径

    Returns:
        SqliteSaver 实例
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    # 创建数据库连接
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # 创建 SqliteSaver
    checkpointer = SqliteSaver(conn)

    print(f"   ✅ SQLite 检查点存储已启用: {db_path}")
    print(f"   💾 对话历史将持久化到数据库")

    return checkpointer, conn  # 返回连接供 store 使用


# ============================================
# 定义天气工具
# ============================================

from langchain.tools import tool, ToolRuntime
import requests

@tool
def get_real_weather(city: str) -> str:
    """获取真实天气信息"""
    try:
        print(f"\n   🔍 正在查询 {city} 的天气...")
        url = f"https://wttr.in/{city}?format=v2&lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print(f"   ✅ 获取成功!")
            return response.text.strip()
        else:
            return f"获取天气失败: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except Exception as e:
        return f"请求错误: {str(e)}"


@tool
def get_weather_forecast(city: str) -> str:
    """获取未来天气预报"""
    try:
        print(f"\n   🔍 正在查询 {city} 的天气预报...")
        url = f"https://wttr.in/{city}?lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print(f"   ✅ 获取成功!")
            lines = response.text.strip().split('\n')
            return '\n'.join(lines[:10])
        return "获取预报失败"

    except Exception as e:
        return f"错误: {str(e)}"


# ============================================
# 记忆管理配置
# ============================================

MEMORY_CONFIG = {
    "max_favorite_cities": 10,       # 偏好城市最大数量
    "max_query_history": 20,         # 查询历史最大数量
    "max_conversation_messages": 50, # 对话历史最大消息数
    "history_expire_days": 30,       # 查询历史过期天数
    "summary_threshold": 10,         # 触发摘要的消息数阈值
}


# ============================================
# Long-Term Memory 工具 (长期记忆 + 记忆管理)
# ============================================

@tool
def save_favorite_city(city: str, runtime: ToolRuntime[Context]) -> str:
    """保存用户偏好城市到长期记忆 (有上限限制)

    Args:
        city: 要保存的城市名称
        runtime: 工具运行时环境 (自动注入)

    Returns:
        保存结果消息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id
    max_cities = MEMORY_CONFIG["max_favorite_cities"]

    print(f"\n   💾 正在保存偏好城市: {city} (用户: {user_id})")

    # 获取现有数据
    user_data = runtime.store.get(("users",), user_id)

    if user_data:
        cities = user_data.value.get("favorite_cities", [])
        if city in cities:
            return f"{city} 已经在偏好列表中了"

        # 检查是否达到上限
        if len(cities) >= max_cities:
            print(f"   ⚠️ 偏好城市已达上限 ({max_cities} 个)")
            # 移除最旧的城市，添加新的
            removed = cities[0]
            cities = cities[1:] + [city]
            runtime.store.put(("users",), user_id, {"favorite_cities": cities})
            print(f"   🔄 已移除 {removed}, 添加 {city}")
            return f"偏好城市已达上限，已移除 {removed} 并添加 {city}"
        else:
            cities.append(city)
            runtime.store.put(("users",), user_id, {"favorite_cities": cities})
            print(f"   ✅ 已添加到偏好列表 (共 {len(cities)}/{max_cities} 个)")
    else:
        runtime.store.put(("users",), user_id, {"favorite_cities": [city]})
        print(f"   ✅ 已创建偏好列表 (1/{max_cities} 个)")

    return f"已保存 {city} 为偏好城市"


@tool
def get_favorite_cities(runtime: ToolRuntime[Context]) -> str:
    """从长期记忆获取用户偏好城市列表

    Args:
        runtime: 工具运行时环境 (自动注入)

    Returns:
        偏好城市列表
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🔍 正在获取偏好城市 (用户: {user_id})")

    user_data = runtime.store.get(("users",), user_id)

    if user_data and "favorite_cities" in user_data.value:
        cities = user_data.value["favorite_cities"]
        print(f"   ✅ 找到 {len(cities)} 个偏好城市")
        return f"你的偏好城市: {cities}"

    print(f"   ⚠️ 暂无偏好城市")
    return "暂无偏好城市"


@tool
def remove_favorite_city(city: str, runtime: ToolRuntime[Context]) -> str:
    """从偏好城市列表中移除城市

    Args:
        city: 要移除的城市名称
        runtime: 工具运行时环境 (自动注入)

    Returns:
        移除结果消息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🗑️ 正在移除偏好城市: {city} (用户: {user_id})")

    user_data = runtime.store.get(("users",), user_id)

    if user_data and "favorite_cities" in user_data.value:
        cities = user_data.value["favorite_cities"]
        if city in cities:
            cities.remove(city)
            runtime.store.put(("users",), user_id, {"favorite_cities": cities})
            print(f"   ✅ 已移除 {city}")
            return f"已从偏好列表移除 {city}"
        else:
            return f"{city} 不在偏好列表中"

    return "暂无偏好城市"


@tool
def save_query_history(city: str, weather: str, runtime: ToolRuntime[Context]) -> str:
    """保存天气查询历史到长期记忆 (自动清理过期记录)

    Args:
        city: 查询的城市名称
        weather: 天气信息摘要
        runtime: 工具运行时环境 (自动注入)

    Returns:
        保存结果消息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id
    max_history = MEMORY_CONFIG["max_query_history"]
    expire_days = MEMORY_CONFIG["history_expire_days"]

    print(f"\n   💾 正在保存查询历史 (用户: {user_id})")

    # 获取现有查询历史
    history_data = runtime.store.get(("query_history",), user_id)

    if history_data:
        history = history_data.value.get("queries", [])
    else:
        history = []

    # 清理过期记录
    now = datetime.now()
    valid_history = []
    expired_count = 0

    for record in history:
        record_time = datetime.fromisoformat(record["timestamp"])
        days_old = (now - record_time).days
        if days_old <= expire_days:
            valid_history.append(record)
        else:
            expired_count += 1

    if expired_count > 0:
        print(f"   🧹 已清理 {expired_count} 条过期记录 (> {expire_days} 天)")

    history = valid_history

    # 添加新的查询记录
    history.append({
        "city": city,
        "weather": weather,
        "timestamp": datetime.now().isoformat()
    })

    # 只保留最近 max_history 条记录
    if len(history) > max_history:
        removed = len(history) - max_history
        history = history[-max_history:]
        print(f"   🧹 已移除 {removed} 条旧记录 (保留最近 {max_history} 条)")

    runtime.store.put(("query_history",), user_id, {"queries": history})
    print(f"   ✅ 已保存查询历史 (共 {len(history)}/{max_history} 条)")
    return "查询历史已保存"


@tool
def get_query_history(runtime: ToolRuntime[Context]) -> str:
    """从长期记忆获取天气查询历史 (返回最近记录)

    Args:
        runtime: 工具运行时环境 (自动注入)

    Returns:
        查询历史记录
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🔍 正在获取查询历史 (用户: {user_id})")

    history_data = runtime.store.get(("query_history",), user_id)

    if history_data and "queries" in history_data.value:
        history = history_data.value["queries"]
        print(f"   ✅ 找到 {len(history)} 条查询记录")

        # 返回最近 5 条记录的摘要
        recent = history[-5:]
        summary = []
        for record in recent:
            summary.append(f"{record['city']} ({record['timestamp'][:10]})")

        return f"最近查询记录: {', '.join(summary)} (共 {len(history)} 条)"

    print(f"   ⚠️ 暂无查询历史")
    return "暂无查询历史"


@tool
def clear_query_history(runtime: ToolRuntime[Context]) -> str:
    """清空查询历史记录

    Args:
        runtime: 工具运行时环境 (自动注入)

    Returns:
        清空结果消息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🗑️ 正在清空查询历史 (用户: {user_id})")

    runtime.store.put(("query_history",), user_id, {"queries": []})
    print(f"   ✅ 查询历史已清空")

    return "查询历史已清空"


@tool
def get_memory_stats(runtime: ToolRuntime[Context]) -> str:
    """获取记忆使用统计信息

    Args:
        runtime: 工具运行时环境 (自动注入)

    Returns:
        记忆统计信息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   📊 正在获取记忆统计 (用户: {user_id})")

    stats = {
        "user_id": user_id,
        "favorite_cities": 0,
        "max_favorite_cities": MEMORY_CONFIG["max_favorite_cities"],
        "query_history": 0,
        "max_query_history": MEMORY_CONFIG["max_query_history"],
        "history_expire_days": MEMORY_CONFIG["history_expire_days"],
    }

    # 获取偏好城市数量
    user_data = runtime.store.get(("users",), user_id)
    if user_data and "favorite_cities" in user_data.value:
        stats["favorite_cities"] = len(user_data.value["favorite_cities"])

    # 获取查询历史数量
    history_data = runtime.store.get(("query_history",), user_id)
    if history_data and "queries" in history_data.value:
        stats["query_history"] = len(history_data.value["queries"])

    print(f"   ✅ 记忆统计:")
    print(f"      偏好城市: {stats['favorite_cities']}/{stats['max_favorite_cities']}")
    print(f"      查询历史: {stats['query_history']}/{stats['max_query_history']}")

    return f"记忆统计: 偏好城市 {stats['favorite_cities']}/{stats['max_favorite_cities']}, 查询历史 {stats['query_history']}/{stats['max_query_history']} 条"


# ============================================
# 创建 Agent
# ============================================

def create_weather_agent(use_database: bool = True):
    """创建天气 Agent (支持数据库持久化)

    Args:
        use_database: 是否使用数据库持久化 (默认 True)
                      True: 使用 SQLite 数据库存储 (对话历史 + 用户数据)
                      False: 使用内存存储 (数据仅存在于内存)

    Returns:
        Agent 实例
    """

    # 检查环境变量,如果缺失则尝试加载
    required_vars = ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"]
    missing = [v for v in required_vars if not os.environ.get(v)]

    if missing:
        # 尝试加载环境变量
        if Path(ENV_PATH).exists():
            load_env_file(ENV_PATH)
            missing = [v for v in required_vars if not os.environ.get(v)]

        if missing:
            print(f"\n❌ 缺少环境变量: {missing}")
            return None

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain.agents import create_agent
        from langgraph.checkpoint.memory import InMemorySaver  # Short-Term Memory (内存)
        from langgraph.checkpoint.sqlite import SqliteSaver     # Short-Term Memory (数据库)
        from langgraph.store.memory import InMemoryStore        # Long-Term Memory (内存)

        model_name = os.environ.get("ANTHROPIC_MODEL", "glm-5")
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

        print(f"\n🔧 Agent 配置:")
        print(f"   模型: {model_name}")
        print(f"   API: {base_url}")

        # 统一的数据库文件路径
        DB_PATH = "weather_memory.db"

        if use_database:
            print(f"\n   🗄️ 数据库持久化模式:")
            print(f"   💾 所有数据保存到: {DB_PATH}")

            # 创建 SQLite 检查点存储 (对话历史)
            checkpointer, conn = get_sqlite_checkpointer(DB_PATH)

            # 创建 SQLite 存储 (用户数据) - 使用同一个数据库连接
            store = SqliteStore(DB_PATH)
            store.conn = conn  # 共享同一个连接

            print(f"   🧠 Short-Term Memory: SQLite 数据库 (对话历史)")
            print(f"   💾 Long-Term Memory: SQLite 数据库 (用户数据)")
        else:
            print(f"\n   📦 内存存储模式:")
            checkpointer = InMemorySaver()
            store = InMemoryStore()

            print(f"   🧠 Short-Term Memory: InMemorySaver (对话历史)")
            print(f"   💾 Long-Term Memory: InMemoryStore (用户数据)")
            print(f"   ⚠️ 数据仅存在于内存,重启后消失")

        model = ChatAnthropic(
            model=model_name,
            anthropic_api_url=base_url,
            api_key=api_key,
            timeout=30,
            temperature=0.7
        )

        agent = create_agent(
            model=model,
            tools=[
                get_real_weather,
                get_weather_forecast,
                # 基础记忆工具
                save_favorite_city,
                get_favorite_cities,
                save_query_history,
                get_query_history,
                # 记忆管理工具
                remove_favorite_city,
                clear_query_history,
                get_memory_stats,
            ],
            checkpointer=checkpointer,  # Short-Term Memory: 对话历史
            store=store,                 # Long-Term Memory: 用户数据
            context_schema=Context,      # 用户上下文
            system_prompt="""你是一个海盗天气助手，我需要你以海盗的口吻回答问题！

角色设定:
- 你是一位经验丰富的海盗船长，在大海上航行多年
- 用海盗的语气说话：如"嘿，伙计们！"、"听好了，水手们！"、"呀哈！"
- 称呼用户为"水手"、"伙计"或"船员"
- 用航海术语：如"风向"、"海浪"、"航线"等

功能:
- 查询当前天气 (使用 get_real_weather 工具)
- 查询天气预报 (使用 get_weather_forecast 工具)
- 记住用户之前查询的城市和天气信息

偏好城市管理 (有上限限制):
- 保存用户偏好城市 (使用 save_favorite_city 工具，最多 10 个)
- 查看用户偏好城市列表 (使用 get_favorite_cities 工具)
- 移除偏好城市 (使用 remove_favorite_city 工具)

查询历史管理 (自动清理过期记录):
- 保存查询历史 (使用 save_query_history 工具，最多 20 条，30 天过期)
- 查看查询历史记录 (使用 get_query_history 工具)
- 清空查询历史 (使用 clear_query_history 工具)

记忆统计:
- 查看记忆使用情况 (使用 get_memory_stats 工具)

回复风格:
- 开头用海盗问候语："呀哈！伙计们！"
- 描述天气时用航海比喻：如"风向有利"、"海浪平静"
- 给出建议时用海盗口吻：如"带上你的防水装备"、"小心暴风雨"
- 结尾用海盗告别语："祝你们航行顺利！"、"扬帆起航吧！"

记忆管理策略:
- 偏好城市最多保存 10 个，超过时自动移除最旧的
- 查询历史最多保存 20 条，超过时自动清理
- 查询历史超过 30 天自动过期删除
- 用户可以手动移除偏好城市或清空历史

工作流程:
1. 用户查询天气时:
   - 先调用 get_real_weather 获取天气
   - 然后调用 save_query_history 保存查询记录 (自动清理过期记录)
2. 用户想保存偏好城市时:
   - 调用 save_favorite_city 保存 (有上限)
3. 用户查看历史记录时:
   - 调用 get_query_history 获取
4. 用户想管理记忆时:
   - 调用 get_memory_stats 查看统计
   - 调用 remove_favorite_city 移除城市
   - 调用 clear_query_history 清空历史

使用工具获取信息后，用海盗的口吻向水手们报告天气情况。
如果天气不好，要提醒船员们注意安全。
"""
        )

        print("\n✅ Agent 创建成功!")
        print("   💾 双重记忆系统已启用:")
        print("      - Short-Term Memory: 记住当前对话")
        print("      - Long-Term Memory: 保存用户偏好和历史")
        return agent

    except Exception as e:
        print(f"\n❌ Agent 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================
# 流式输出函数 ⭐ 正确实现
# ============================================

def run_agent_streaming(agent, question: str):
    """流式运行 Agent - 优雅的连续输出"""

    print(f"\n用户: {question}")
    print("-" * 50)
    print("Agent: ", end="", flush=True)

    try:
        # 流式输出
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="messages",
            version="v2"
        ):
            if chunk["type"] == "messages":
                token, metadata = chunk["data"]

                # 处理文本内容
                if hasattr(token, 'content_blocks'):
                    for block in token.content_blocks:
                        if block.get('type') == 'text':
                            text = block.get('text', '')
                            # 直接打印,不分段
                            print(text, end="", flush=True)

                elif hasattr(token, 'content') and token.content:
                    print(token.content, end="", flush=True)

        print()  # 最后换行
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def run_agent_streaming_simple(agent, question: str):
    """极简流式输出 - 最干净的显示方式"""

    print(f"\n用户: {question}")
    print("Agent: ", end="", flush=True)

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="messages",
            version="v2"
        ):
            if chunk["type"] == "messages":
                token, metadata = chunk["data"]

                if hasattr(token, 'content_blocks'):
                    for block in token.content_blocks:
                        if block.get('type') == 'text':
                            print(block.get('text', ''), end="", flush=True)

                elif hasattr(token, 'content') and token.content:
                    print(token.content, end="", flush=True)

        print()  # 仅换行

    except Exception as e:
        print(f"\n错误: {e}")


def run_agent_streaming_with_updates(agent, question: str):
    """带工具调用提示的流式输出"""

    print(f"\n用户: {question}")
    print("=" * 60)

    current_text = ""

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode=["updates", "messages"],
            version="v2"
        ):
            # 显示步骤更新 (工具调用)
            if chunk["type"] == "updates":
                for node_name in chunk["data"]:
                    if "tool" in node_name.lower() or "agent" in node_name.lower():
                        print(f"\n🔧 正在处理... ")

            # 流式显示文本内容
            elif chunk["type"] == "messages":
                token, metadata = chunk["data"]

                if hasattr(token, 'content_blocks'):
                    for block in token.content_blocks:
                        if block.get('type') == 'text':
                            text = block.get('text', '')
                            print(text, end="", flush=True)

                elif hasattr(token, 'content') and token.content:
                    print(token.content, end="", flush=True)

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


def run_agent_structured_output(agent, city: str):
    """结构化输出 - 返回格式化的天气报告"""

    print(f"\n用户: {city} 的天气如何?")
    print("=" * 60)
    print("🔍 正在获取结构化天气报告...")
    print("-" * 60)

    try:
        # 使用 invoke 获取结果
        result = agent.invoke(
            {"messages": [{"role": "user", "content": f"请为 {city} 提供详细的结构化天气报告"}]}
        )

        # 提取工具返回的天气数据
        weather_data = extract_weather_from_tool_result(result, city)

        # 构建 Pirate 消息
        pirate_msg = generate_pirate_message(weather_data)

        # 创建结构化报告
        report = WeatherReport(
            city=city,
            temperature=weather_data['temperature'],
            weather_condition=weather_data['condition'],
            humidity=weather_data['humidity'],
            wind_speed=weather_data['wind_speed'],
            wind_direction=weather_data['wind_direction'],
            pressure=weather_data['pressure'],
            recommendation=pirate_msg.split('\n')[-2] if '\n' in pirate_msg else pirate_msg,
            pirate_message=pirate_msg
        )

        display_structured_report(report)
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def run_agent_structured_output_with_memory(agent, user_input: str, thread_config: dict, context: Context):
    """带双重记忆功能的结构化输出"""

    print(f"\n用户: {user_input}")
    print("=" * 60)
    print("🔍 正在处理...")
    print("-" * 60)

    try:
        # 使用 invoke 获取结果 (带双重记忆)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=thread_config,  # 使用 thread_config 保持对话历史 (Short-Term)
            context=context        # 使用 context 保持用户数据 (Long-Term)
        )

        # 获取最后一条消息
        last_message = result["messages"][-1]

        # 显示回复内容
        if hasattr(last_message, 'content'):
            content = last_message.content
            if isinstance(content, list):
                # 处理 content_blocks
                for block in content:
                    if hasattr(block, 'get') and block.get('type') == 'text':
                        print(block.get('text', ''), end='', flush=True)
            else:
                print(content)
        else:
            print(str(last_message))

        print("\n" + "-" * 60)

        # 显示记忆提示
        print("\n🧠 双重记忆提示:")
        print("   Short-Term: Agent 已记住这次对话")
        print("   Long-Term: 用户数据已保存")
        print("   你可以问:")
        print("   - '上次查的城市是哪个?'")
        print("   - '我的偏好城市有哪些?'")
        print("   - '我之前查询过哪些城市?'")
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def extract_weather_from_tool_result(result, city: str) -> dict:
    """从工具返回结果中提取天气数据"""

    weather_data = {
        'temperature': 20,
        'condition': '未知',
        'humidity': 50,
        'wind_speed': 10,
        'wind_direction': '未知',
        'pressure': 1013
    }

    # 遍历所有消息,查找工具返回
    for msg in result["messages"]:
        # 检查是否有 name 属性,且 name 不为 None
        msg_name = getattr(msg, 'name', None) if hasattr(msg, 'name') else None

        if msg_name and 'weather' in str(msg_name).lower():
            # 这是天气工具的返回
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)

            import re

            # 解析温度 (格式: +20°C 或 20°C)
            temp_match = re.search(r'[+]?(\d+)°C', content)
            if temp_match:
                weather_data['temperature'] = int(temp_match.group(1))

            # 解析天气状况
            condition_patterns = [
                (r'天气[：:]\s*(\S+)', 1),
                (r'☁️|☀️|🌧️|⛈️|🌤️|🌦️', 0),  # 天气图标
                (r'Sunny|Rain|Cloudy|Clear', 0),
            ]

            for pattern, group_idx in condition_patterns:
                match = re.search(pattern, content)
                if match:
                    if group_idx == 0:
                        weather_data['condition'] = match.group(0)
                    else:
                        weather_data['condition'] = match.group(group_idx)
                    break

            # 解析湿度 (格式: 83% 或 湿度: 83%)
            humidity_match = re.search(r'(\d+)%', content)
            if humidity_match:
                weather_data['humidity'] = int(humidity_match.group(1))

            # 解析风速 (格式: 15km/h 或 15 km/h)
            wind_match = re.search(r'(\d+)\s*km/h', content)
            if wind_match:
                weather_data['wind_speed'] = int(wind_match.group(1))

            # 解析风向 (格式: ← 或 西南风)
            wind_dir_match = re.search(r'([←→↑↓↗↘↙↖]|[东南西北]+风)', content)
            if wind_dir_match:
                weather_data['wind_direction'] = wind_dir_match.group(1)

            # 解析气压 (格式: 1009hPa)
            pressure_match = re.search(r'(\d+)\s*hPa', content)
            if pressure_match:
                weather_data['pressure'] = int(pressure_match.group(1))

            break  # 找到第一个天气工具结果就退出

    # 如果没有找到天气数据,从所有消息中搜索
    if weather_data['temperature'] == 20:
        # 最后一次尝试:从所有内容中提取
        all_content = ""
        for msg in result["messages"]:
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            all_content += content + "\n"

        import re
        temp_match = re.search(r'[+]?(\d+)°C', all_content)
        if temp_match:
            weather_data['temperature'] = int(temp_match.group(1))

        humidity_match = re.search(r'(\d+)%', all_content)
        if humidity_match:
            weather_data['humidity'] = int(humidity_match.group(1))

        wind_match = re.search(r'(\d+)\s*km/h', all_content)
        if wind_match:
            weather_data['wind_speed'] = int(wind_match.group(1))

        pressure_match = re.search(r'(\d+)\s*hPa', all_content)
        if pressure_match:
            weather_data['pressure'] = int(pressure_match.group(1))

    return weather_data


def display_structured_report(report: WeatherReport):
    """显示结构化天气报告"""

    print("\n📊 **结构化天气报告**")
    print("=" * 60)

    # 显示 Pirate 消息
    print("\n" + report.pirate_message)

    # 显示结构化数据表格
    print("\n📋 **详细数据**")
    print("-" * 60)
    print(f"城市: {report.city}")
    print(f"温度: {report.temperature}°C")
    print(f"天气: {report.weather_condition}")
    print(f"湿度: {report.humidity}%")
    print(f"风速: {report.wind_speed} km/h")
    print(f"风向: {report.wind_direction}")
    print(f"气压: {report.pressure} hPa")
    print("-" * 60)

    # 显示 JSON 格式
    print("\n📄 **JSON 格式输出**")
    print("-" * 60)
    print(report.model_dump_json(indent=2))
    print("-" * 60)


def parse_weather_from_message(content, city: str) -> dict:
    """从消息内容解析天气数据"""

    # 将 content 转换为字符串
    if isinstance(content, list):
        # 如果是列表,提取文本内容
        text_content = ""
        for item in content:
            if isinstance(item, str):
                text_content += item
            elif hasattr(item, 'text'):
                text_content += item.text
        content = text_content

    # 默认值
    weather_data = {
        'temperature': 20,
        'condition': '未知',
        'humidity': 50,
        'wind_speed': 10,
        'wind_direction': '未知',
        'pressure': 1013
    }

    # 尝试解析温度
    import re
    temp_match = re.search(r'(\d+)°C', content)
    if temp_match:
        weather_data['temperature'] = int(temp_match.group(1))

    # 尝试解析湿度
    humidity_match = re.search(r'湿度[：:]\s*(\d+)%', content)
    if humidity_match:
        weather_data['humidity'] = int(humidity_match.group(1))

    # 尝试解析风速
    wind_match = re.search(r'(\d+)\s*公里/小时', content)
    if wind_match:
        weather_data['wind_speed'] = int(wind_match.group(1))

    return weather_data


def generate_pirate_message(weather_data: dict) -> str:
    """生成海盗风格消息"""

    temp = weather_data['temperature']
    condition = weather_data['condition']

    if temp > 30:
        warning = "🔥 天气炎热，水手们注意防晒！"
    elif temp < 10:
        warning = "❄️ 天气寒冷，穿上厚外套！"
    else:
        warning = "✨ 天气舒适，适合扬帆起航！"

    return f"""呀哈！伙计们！

⚓ **港口天气报告** ⚓

**当前状况**:
- 🌡️ 温度: {temp}°C
- 🌤️ 天气: {condition}
- 💧 湿度: {weather_data['humidity']}%
- 💨 风速: {weather_data['wind_speed']} km/h

{warning}

扬帆起航吧，水手们！🏴‍☠️"""


# ============================================
# 运行模式
# ============================================

def run_demo_streaming(agent):
    """流式演示"""
    print("\n" + "=" * 60)
    print("【流式输出演示】")
    print("=" * 60)

    test_questions = [
        "北京今天天气怎么样?",
        "上海天气如何?",
        "Tokyo 的天气?"
    ]

    for question in test_questions:
        run_agent_streaming_simple(agent, question)


def run_demo_memory(agent):
    """记忆功能演示 - Short-Term + Long-Term"""
    print("\n" + "=" * 60)
    print("【双重记忆功能演示】")
    print("=" * 60)
    print("🧠 Short-Term Memory: 记住当前对话")
    print("💾 Long-Term Memory: 保存用户偏好和历史")
    print("=" * 60)

    # 创建 thread_id
    import uuid
    thread_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": thread_id}}

    # 创建用户上下文
    user_id = "demo_user_001"
    context = Context(user_id=user_id)

    print(f"\n💾 对话 ID: {thread_id}")
    print(f"👤 用户 ID: {user_id}")
    print("   (Long-Term Memory 会保存到这个用户的数据)")

    # 模拟对话流程
    conversation_flow = [
        "北京天气怎么样?",
        "请把北京保存为我的偏好城市",
        "上海天气如何?",
        "我的偏好城市有哪些?",
        "我之前查询过哪些城市?",
    ]

    print("\n📝 演示对话流程:")
    for i, question in enumerate(conversation_flow, 1):
        print(f"\n--- 第 {i} 次对话 ---")
        print(f"用户: {question}")

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config=thread_config,
                context=context  # 传递用户上下文
            )

            last_message = result["messages"][-1]

            # 显示回复
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

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ 双重记忆功能演示完成!")
    print("   - Short-Term Memory: Agent 记住了当前对话")
    print("   - Long-Term Memory: Agent 保存了用户偏好和查询历史")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 偏好城市已保存,下次使用相同 user_id 可以获取")
    print("   - 查询历史已保存,可以跨会话访问")
    print("   - 即使使用新的 thread_id,Long-Term Memory 依然可用")
    print("=" * 60)


def run_interactive_streaming_structured(agent):
    """交互式结构化输出 - 带双重记忆功能"""
    print("\n" + "=" * 60)
    print("【交互式天气查询 - 双重记忆功能】")
    print("=" * 60)
    print("输入城市名查询天气，输入 'quit' 退出")
    print("提示: 输出为结构化 JSON 格式!")
    print("🧠 Short-Term Memory: 记住当前对话")
    print("💾 Long-Term Memory: 保存用户偏好和历史")
    print("=" * 60)

    # 创建 thread_id 用于保存对话历史
    import uuid
    thread_id = str(uuid.uuid4())
    thread_config = {"configurable": {"thread_id": thread_id}}

    # 创建用户上下文
    user_id = "interactive_user_001"
    context = Context(user_id=user_id)

    print(f"\n💾 对话 ID: {thread_id}")
    print(f"👤 用户 ID: {user_id}")
    print("   (双重记忆已启用)")
    print("\n💡 可用命令:")
    print("   - 查询城市天气")
    print("   - '保存城市' 或 '添加偏好'")
    print("   - '我的偏好城市' 或 '偏好列表'")
    print("   - '查询历史' 或 '历史记录'")
    print("   - 'quit' 退出")

    while True:
        try:
            user_input = input("\n城市/问题: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见! 👋")
                print("   💾 Short-Term Memory: 对话已保存")
                print("   💾 Long-Term Memory: 用户数据已保存")
                break

            if not user_input:
                print("请输入有效城市名或问题")
                continue

            # 使用结构化输出 (带记忆)
            run_agent_structured_output_with_memory(agent, user_input, thread_config, context)

        except KeyboardInterrupt:
            print("\n\n再见! 👋")
            break


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌤️  LangChain 天气查询 Agent")
    print("   流式输出版本 - 实时显示 + 长期记忆")
    print("=" * 60)

    agent = create_weather_agent()

    if agent:
        print("\n请选择运行模式:")
        print("  1 - 自动演示 (简洁输出)")
        print("  2 - 交互模式 (推荐) - 带记忆功能 ⭐")
        print("  3 - 详细模式 (显示工具调用)")
        print("  4 - 结构化输出 (JSON格式)")
        print("  5 - 记忆功能演示 (自动演示记忆能力) ⭐⭐")
        print("  其他 - 退出")

        choice = input("\n选择 (1-5): ").strip()

        if choice == '1':
            run_demo_streaming(agent)
        elif choice == '2':
            run_interactive_streaming_structured(agent)
        elif choice == '3':
            test_question = "北京天气怎么样?"
            run_agent_streaming_with_updates(agent, test_question)
        elif choice == '4':
            # 结构化输出演示
            print("\n" + "=" * 60)
            print("【结构化输出演示】")
            print("=" * 60)

            cities = ["北京", "上海", "Tokyo"]
            for city in cities:
                run_agent_structured_output(agent, city)
        elif choice == '5':
            # 记忆功能演示
            run_demo_memory(agent)
        else:
            print("\n退出")

    else:
        print("\n无法创建 Agent")

    print("\n" + "=" * 60)


# ============================================
# 使用说明
# ============================================

"""
【流式输出核心要点】

1. 使用 stream_mode 参数:
   - "messages": 流式获取消息内容
   - "updates": 获取步骤更新
   - ["messages", "updates"]: 同时获取两种

2. chunk 格式:
   chunk = {
       "type": "messages" 或 "updates",
       "data": (token, metadata) 或 dict
   }

3. token 类型:
   - AIMessage: AI回复
   - ToolMessage: 工具结果

4. metadata 包含:
   - langgraph_node: 当前节点名称
   - langgraph_step: 步骤编号

【对比传统 invoke】

# 传统方式: 等待全部完成
result = agent.invoke(input)
print(result["messages"][-1].content)

# 流式方式: 实时显示
for chunk in agent.stream(input, stream_mode="messages"):
    print(chunk内容)  # 逐步显示

【优势】

✅ 实时反馈 - 用户不需要等待
✅ 过程透明 - 显示处理步骤
✅ 更好体验 - 流畅自然
✅ 易于调试 - 看到每个阶段
"""