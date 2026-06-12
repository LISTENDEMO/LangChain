"""
LangChain 天气查询 Agent - 演示版
不需要 API Key,直接运行即可看到效果
"""

# ============================================
# 演示版: 模拟 Agent 工作流程
# ============================================

from langchain.tools import tool

# 定义天气工具
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    Args:
        city: 城市名称，如 "北京"、"上海"

    Returns:
        天气信息字符串
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，温度 28°C，空气质量良好",
        "上海": "多云，温度 26°C，有轻微雾霾",
        "广州": "小雨，温度 30°C，湿度较高",
        "深圳": "晴天，温度 32°C，紫外线较强",
        "成都": "阴天，温度 22°C，建议带伞",
    }

    # 查找城市
    for key in weather_data:
        if key.lower() in city.lower() or city.lower() in key.lower():
            return weather_data[key]

    return f"未找到 '{city}' 的天气数据。可用城市: 北京、上海、广州、深圳、成都"


# 演示工具调用
print("=" * 50)
print("天气查询工具演示")
print("=" * 50)

# 1. 直接调用工具
print("\n【方式1】直接调用工具:")
print("-" * 30)

cities = ["北京", "上海", "广州"]
for city in cities:
    result = get_weather.invoke({"city": city})
    print(f"查询 {city}: {result}")

# 2. 模拟 Agent 流程
print("\n【方式2】模拟 Agent 工作流程:")
print("-" * 30)

def simulate_agent(user_question: str):
    """模拟 Agent 的决策和执行过程"""
    print(f"用户提问: {user_question}")
    print()

    # 步骤1: 分析意图
    print("步骤1: Agent 分析用户意图...")
    print("→ 识别关键词: '天气', '城市'")

    # 步骤2: 提取参数
    print("\n步骤2: 提取城市名称...")
    if "北京" in user_question:
        city = "北京"
    elif "上海" in user_question:
        city = "上海"
    elif "广州" in user_question:
        city = "广州"
    else:
        city = user_question.split()[-1]  # 简单提取
    print(f"→ 提取城市: {city}")

    # 步骤3: 调用工具
    print(f"\n步骤3: 调用工具 get_weather(city='{city}')")
    tool_result = get_weather.invoke({"city": city})
    print(f"→ 工具返回: {tool_result}")

    # 步骤4: 生成回复
    print("\n步骤4: Agent 生成友好回复...")
    response = f"根据查询结果,{tool_result}。建议您根据天气情况安排出行!"
    print(f"→ 最终回复: {response}")

    print("\n" + "=" * 50)
    return response


# 运行模拟
simulate_agent("北京今天天气怎么样?")
simulate_agent("上海和广州的天气如何?")

print("\n" + "=" * 50)
print("以上演示了 Agent 的工作流程")
print("=" * 50)


# ============================================
# 完整版说明 (需要 API Key)
# ============================================

print("\n\n【完整版使用说明】")
print("-" * 50)
print("""
要使用完整版 Agent (真正调用 LLM):

1. 获取 OpenAI API Key:
   - 访问 https://platform.openai.com/api-keys
   - 创建新的 API Key

2. 设置环境变量:
   Windows PowerShell:
   $env:OPENAI_API_KEY = "sk-your-key-here"

   Linux/Mac:
   export OPENAI_API_KEY="sk-your-key-here"

3. 运行完整代码:
   参考 weather_agent.py 文件

完整版 Agent 优势:
- 自动理解复杂问题
- 自动选择合适工具
- 自动生成自然语言回复
- 支持多轮对话
""")

print("\n【工具定义示例】")
print("-" * 50)
print("""
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    '''获取指定城市的天气信息'''  # ← docstring 很重要!
    return weather_data.get(city, "未找到")

# 工具会被 Agent 自动识别和使用
""")


# ============================================
# 使用真实天气 API (可选)
# ============================================

print("\n【使用真实天气 API】")
print("-" * 50)
print("""
wttr.in 是免费的天气 API,不需要注册:

import requests

@tool
def get_real_weather(city: str) -> str:
    '''获取真实天气'''
    url = f"https://wttr.in/{city}?format=v2&lang=zh"
    response = requests.get(url, timeout=10)
    return response.text

# 查询真实天气
result = get_real_weather.invoke({"city": "Beijing"})
print(result)
""")

# 测试真实 API (可选)
try:
    import requests
    print("\n测试 wttr.in API:")
    print("-" * 30)

    test_cities = ["Beijing", "Shanghai"]
    for city in test_cities:
        try:
            url = f"https://wttr.in/{city}?format=v2&lang=zh"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"\n{city} 天气:")
                print(response.text[:100])
        except Exception as e:
            print(f"获取 {city} 失败: {e}")

except ImportError:
    print("需要安装 requests: pip install requests")

print("\n" + "=" * 50)
print("演示完成!")
print("=" * 50)