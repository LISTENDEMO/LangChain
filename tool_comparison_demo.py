"""
LangChain 工具定义方式对比

演示三种工具定义方式:
1. 预定义工具 (LangChain 内置工具)
2. @tool 装饰器 (自定义简单工具)
3. StructuredTool (自定义复杂工具)
"""

import sys
import io
import os
from pathlib import Path

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
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

print("\n" + "=" * 70)
print("📚 LangChain 工具定义方式对比")
print("=" * 70)

# ============================================
# 方式1: 预定义工具 (LangChain 内置工具)
# ============================================

print("\n" + "-" * 70)
print("【方式1】预定义工具 - LangChain 内置工具")
print("-" * 70)

print("""
✅ 特点:
   - LangChain 官方提供的现成工具
   - 无需自己实现功能
   - 开箱即用,配置简单
   - 经过充分测试和优化

📦 常见预定义工具:
""")

try:
    from langchain_community.tools import (
        DuckDuckGoSearchRun,      # DuckDuckGo 搜索
        WikipediaQueryRun,        # Wikipedia 查询
        PythonREPLTool,           # Python REPL
        ShellTool,                # Shell 命令
    )
    from langchain_experimental.tools import PythonAstREPLTool

    print("   1. DuckDuckGoSearchRun  - 搜索引擎工具")
    print("   2. WikipediaQueryRun    - Wikipedia 工具")
    print("   3. PythonREPLTool       - Python 代码执行")
    print("   4. ShellTool            - Shell 命令执行")

    # 示例: DuckDuckGo 搜索工具
    print("\n📝 使用示例:")
    print("""
    from langchain_community.tools import DuckDuckGoSearchRun

    # 创建工具 (无需实现功能)
    search_tool = DuckDuckGoSearchRun()

    # 直接使用
    result = search_tool.invoke("Python LangChain 教程")
    print(result)

    # 工具信息
    print(f"名称: {search_tool.name}")
    print(f"描述: {search_tool.description}")
    """)

    # 实际测试
    print("\n🧪 实际测试:")
    search = DuckDuckGoSearchRun()
    print(f"   工具名称: {search.name}")
    print(f"   工具描述: {search.description[:50]}...")

except ImportError as e:
    print(f"   ⚠️ 导入失败: {e}")
    print("""
   常见预定义工具列表:
   - DuckDuckGoSearchRun  - 搜索引擎
   - WikipediaQueryRun    - Wikipedia 查询
   - PythonREPLTool       - Python 代码执行
   - ShellTool            - Shell 命令
   - RequestsGetTool      - HTTP GET 请求
   - FileManagementTool   - 文件管理
   """)

print("""
❌ 缺点:
   - 功能固定,无法自定义
   - 可能不符合特定需求
   - 需要额外依赖包 (langchain-community)
""")

# ============================================
# 方式2: @tool 装饰器 (自定义简单工具)
# ============================================

print("\n" + "-" * 70)
print("【方式2】@tool 装饰器 - 自定义简单工具 ⭐ 推荐")
print("-" * 70)

print("""
✅ 特点:
   - 最简单的自定义工具方式
   - 用装饰器直接装饰函数
   - 自动从函数签名提取参数信息
   - 从函数文档字符串提取工具描述
   - 适合简单的单一功能工具

📝 定义方式:
""")

from langchain.tools import tool

# 示例1: 简单工具
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息

    Args:
        city: 城市名称,如 "北京"、"上海"

    Returns:
        天气信息字符串
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天,温度 15°C",
        "上海": "多云,温度 20°C",
        "广州": "小雨,温度 25°C",
    }
    return weather_data.get(city, f"未找到 {city} 的天气数据")

# 示例2: 带多个参数的工具
@tool
def calculate_distance(city1: str, city2: str, unit: str = "km") -> str:
    """计算两个城市之间的距离

    Args:
        city1: 第一个城市
        city2: 第二个城市
        unit: 距离单位 (km 或 miles),默认 km

    Returns:
        距离信息
    """
    # 模拟距离计算
    distances = {
        ("北京", "上海"): 1200,
        ("上海", "广州"): 800,
    }
    dist = distances.get((city1, city2), 500)

    if unit == "miles":
        dist = dist * 0.621371

    return f"{city1} 到 {city2} 的距离: {dist} {unit}"

print("""
    from langchain.tools import tool

    @tool
    def get_weather(city: str) -> str:
        # 获取指定城市的天气信息
        return f"{city} 的天气: 晴天"

    # 自动提取:
    # - 工具名: get_weather
    # - 参数: city (string)
    # - 描述: 获取指定城市的天气信息
    """)

print("\n🧪 实际测试:")
print(f"   工具名称: {get_weather.name}")
print(f"   工具描述: {get_weather.description}")
print(f"   参数信息: {get_weather.args}")

# 测试工具调用
print(f"\n   调用结果: {get_weather.invoke({'city': '北京'})}")

print("""
✅ 优点:
   - 定义简单,只需装饰函数
   - 自动提取参数和描述
   - 类型安全 (Python 类型提示)
   - 适合快速开发

❌ 缺点:
   - 只能返回字符串
   - 参数验证有限
   - 不适合复杂逻辑
""")

# ============================================
# 方式3: StructuredTool (自定义复杂工具)
# ============================================

print("\n" + "-" * 70)
print("【方式3】StructuredTool - 自定义复杂工具")
print("-" * 70)

print("""
✅ 特点:
   - 最灵活的工具定义方式
   - 可以自定义参数验证 (使用 Pydantic)
   - 可以返回复杂类型
   - 可以添加更多元数据
   - 适合复杂功能的工具

📝 定义方式:
""")

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# 定义参数模型
class WeatherQuery(BaseModel):
    """天气查询参数"""
    city: str = Field(description="城市名称")
    days: int = Field(default=1, description="查询天数", ge=1, le=7)
    include_forecast: bool = Field(default=False, description="是否包含预报")

# 定义函数
def query_weather_complex(params: WeatherQuery) -> dict:
    """复杂天气查询功能"""
    result = {
        "city": params.city,
        "current": "晴天, 20°C",
        "query_days": params.days
    }

    if params.include_forecast:
        result["forecast"] = ["明天: 多云", "后天: 小雨"]

    return result

# 创建 StructuredTool
weather_tool_complex = StructuredTool(
    name="weather_query_advanced",
    description="高级天气查询工具,支持预报和多天查询",
    func=query_weather_complex,
    args_schema=WeatherQuery
)

print("""
    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel, Field

    # 1. 定义参数模型
    class WeatherQuery(BaseModel):
        city: str = Field(description="城市名称")
        days: int = Field(default=1, ge=1, le=7)

    # 2. 定义函数
    def query_weather(params: WeatherQuery) -> dict:
        return {"city": params.city, "temp": 20}

    # 3. 创建工具
    tool = StructuredTool(
        name="weather_query",
        description="天气查询工具",
        func=query_weather,
        args_schema=WeatherQuery
    )
    """)

print("\n🧪 实际测试:")
print(f"   工具名称: {weather_tool_complex.name}")
print(f"   工具描述: {weather_tool_complex.description}")
print(f"   参数模型: {weather_tool_complex.args_schema.schema()}")

print("""
✅ 优点:
   - 参数验证严格 (Pydantic 验证)
   - 可以返回复杂类型 (dict, list, object)
   - 参数可以设置默认值和约束
   - 适合生产环境使用

❌ 缺点:
   - 定义复杂,需要多个步骤
   - 需要学习 Pydantic
   - 代码量较多
""")

# ============================================
# 对比总结
# ============================================

print("\n" + "=" * 70)
print("📊 三种方式对比总结")
print("=" * 70)

print("""
┌─────────────────┬──────────────────┬──────────────────┬──────────────────┐
│     特性        │   预定义工具     │   @tool 装饰器   │  StructuredTool  │
├─────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ 定义难度        │      ⭐ 最简单   │     ⭐⭐ 简单    │    ⭐⭐⭐ 复杂   │
│ 自定义能力      │      ❌ 无       │     ✅ 中等      │      ✅ 强       │
│ 参数验证        │      ✅ 内置     │     ⭐ 基础      │     ⭐⭐⭐ 强    │
│ 返回类型        │      固定        │     仅字符串     │    任意类型      │
│ 开发速度        │      ⚡⚡⚡ 快   │     ⚡⚡ 较快    │      ⚡ 较慢     │
│ 适用场景        │   通用功能       │   简单自定义     │   复杂自定义     │
│ 生产使用        │      ✅ 推荐     │     ✅ 推荐      │     ✅ 推荐      │
└─────────────────┴──────────────────┴──────────────────┴──────────────────┘
""")

print("\n🎯 选择建议:")
print("""
   ┌─────────────────────────────────────────────────────────────────┐
   │  ✅ 使用预定义工具:                                              │
   │     - 需要搜索、Wikipedia、代码执行等通用功能                   │
   │     - 不需要自定义实现                                          │
   │     - 快速原型开发                                              │
   │                                                                  │
   │  ✅ 使用 @tool 装饰器: ⭐⭐⭐ 最推荐                            │
   │     - 需要自定义简单功能                                        │
   │     - 工具逻辑简单,返回字符串即可                              │
   │     - 大多数场景的最佳选择                                      │
   │                                                                  │
   │  ✅ 使用 StructuredTool:                                        │
   │     - 需要严格的参数验证                                        │
   │     - 需要返回复杂类型 (dict, list)                            │
   │     - 生产环境的复杂工具                                        │
   └─────────────────────────────────────────────────────────────────┘
""")

# ============================================
# 实际应用示例
# ============================================

print("\n" + "=" * 70)
print("💡 实际应用示例")
print("=" * 70)

print("\n【场景1】搜索引擎工具")
print("""
   ✅ 推荐: 预定义工具 DuckDuckGoSearchRun

   from langchain_community.tools import DuckDuckGoSearchRun
   search = DuckDuckGoSearchRun()

   # 不需要自己实现搜索功能
""")

print("\n【场景2】天气查询工具 (当前项目)")
print("""
   ✅ 推荐: @tool 装饰器

   @tool
   def get_real_weather(city: str) -> str:
       # 获取真实天气信息
       url = f"https://wttr.in/{city}"
       return requests.get(url).text

   # 简单,清晰,足够使用
""")

print("\n【场景3】复杂查询工具")
print("""
   ✅ 推荐: StructuredTool

   class QueryParams(BaseModel):
       city: str = Field(description="城市")
       date: str = Field(description="日期")
       units: str = Field(default="metric")

   def complex_query(params: QueryParams) -> dict:
       return {
           "city": params.city,
           "data": {...},
           "units": params.units
       }

   tool = StructuredTool(
       name="complex_weather",
       func=complex_query,
       args_schema=QueryParams
   )

   # 参数验证 + 复杂返回
""")

# ============================================
# 工具使用对比
# ============================================

print("\n" + "=" * 70)
print("🔧 工具在 Agent 中的使用")
print("=" * 70)

print("""
所有工具类型在 Agent 中使用方式相同:

    from langchain.agents import create_agent

    # 1. 预定义工具
    tools = [DuckDuckGoSearchRun()]

    # 2. @tool 工具
    tools = [get_weather, calculate_distance]

    # 3. StructuredTool
    tools = [weather_tool_complex]

    # Agent 创建和使用方式完全一致
    agent = create_agent(model=model, tools=tools)
""")

print("\n" + "=" * 70)
print("✅ 总结完成!")
print("=" * 70)

print("""
🎯 关键要点:

1. 预定义工具:
   - LangChain 提供的现成工具
   - 开箱即用,无需实现
   - 搜索、Wikipedia、代码执行等

2. @tool 装饰器 ⭐⭐⭐ 推荐:
   - 最简单的自定义方式
   - 自动提取参数和描述
   - 当前项目使用的方式

3. StructuredTool:
   - 最灵活的自定义方式
   - Pydantic 参数验证
   - 复杂返回类型

💡 建议:
   - 简单工具用 @tool (当前项目 ✓)
   - 通用功能用预定义工具
   - 复杂工具用 StructuredTool
""")