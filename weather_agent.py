"""
LangChain 天气查询 Agent 示例
功能: 使用 Agent 查询城市天气信息
"""

# ============================================
# 版本 1: 简单版 (模拟数据,适合学习)
# ============================================

from langchain.agents import create_agent
from langchain.tools import tool

# 定义天气工具
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    Args:
        city: 城市名称，如 "北京"、"上海"、"San Francisco"

    Returns:
        天气信息字符串
    """
    # 模拟天气数据 (实际项目中应调用真实 API)
    weather_data = {
        "北京": "晴天，温度 28°C，空气质量良好",
        "上海": "多云，温度 26°C，有轻微雾霾",
        "广州": "小雨，温度 30°C，湿度较高",
        "深圳": "晴天，温度 32°C，紫外线较强",
        "成都": "阴天，温度 22°C，建议带伞",
        "San Francisco": "晴天，温度 75°F，凉爽宜人",
        "New York": "多云，温度 68°F，傍晚可能有雨",
        "London": "阴雨，温度 15°C，典型的伦敦天气",
    }

    # 查找城市
    for key in weather_data:
        if key.lower() in city.lower() or city.lower() in key.lower():
            return weather_data[key]

    return f"未找到 {city} 的天气数据。可用城市: 北京、上海、广州、深圳、成都"


# 创建 Agent
agent = create_agent(
    model="openai:gpt-4o-mini",  # 或使用其他模型
    tools=[get_weather],
    system_prompt="你是一个天气查询助手。使用工具帮助用户查询天气信息。回复要友好且简洁。"
)

# 执行查询
def query_weather(question: str):
    """查询天气"""
    result = agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })
    return result["messages"][-1].content


# 测试
if __name__ == "__main__":
    questions = [
        "北京今天天气怎么样?",
        "上海和广州的天气如何?",
        "San Francisco 的天气如何?"
    ]

    for q in questions:
        print(f"\n用户: {q}")
        print(f"Agent: {query_weather(q)}")


# ============================================
# 版本 2: 真实 API 版 (使用 wttr.in 免费 API)
# ============================================

"""
真实天气 API 版本需要安装:
pip install requests

完整代码如下:
"""

import requests
from langchain.agents import create_agent
from langchain.tools import tool


@tool
def get_real_weather(city: str) -> str:
    """获取真实天气信息 (使用 wttr.in API)。

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    try:
        # wttr.in 是免费的天气 API
        url = f"https://wttr.in/{city}?format=v2&lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"获取天气失败: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        return f"请求错误: {str(e)}"


@tool
def get_weather_forecast(city: str) -> str:
    """获取未来3天的天气预报。

    Args:
        city: 城市名称

    Returns:
        天气预报信息
    """
    try:
        url = f"https://wttr.in/{city}?lang=zh&format=v2"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            # 解析并返回天气信息
            lines = response.text.strip().split('\n')
            return '\n'.join(lines[:6])  # 返回前6行(包含3天预报)
        else:
            return f"获取预报失败"

    except Exception as e:
        return f"错误: {str(e)}"


# 创建完整版 Agent
full_agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_real_weather, get_weather_forecast],
    system_prompt="""你是一个专业的天气助手。

功能:
- 可以查询当前天气
- 可以查询未来3天天气预报

使用工具获取信息后，用友好的方式向用户报告。
如果用户询问多个城市，分别查询并对比天气情况。
"""
)


def run_weather_agent():
    """运行天气 Agent"""
    print("=== 天气查询 Agent ===")
    print("支持功能: 当前天气、天气预报")
    print("输入 'quit' 退出\n")

    while True:
        user_input = input("请输入问题: ")

        if user_input.lower() == 'quit':
            print("再见!")
            break

        result = full_agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        # 获取最终回复
        final_message = result["messages"][-1]

        # 打印回复内容
        if hasattr(final_message, 'content_blocks'):
            print(f"\n天气助手: {final_message.content_blocks}")
        else:
            print(f"\n天气助手: {final_message.content}")

        print()


# ============================================
# 版本 3: 流式输出版本 (更好的用户体验)
# ============================================

def stream_weather_agent(question: str):
    """流式输出天气查询结果"""
    print(f"用户: {question}")
    print("Agent: ", end="", flush=True)

    for step in full_agent.stream({
        "messages": [{"role": "user", "content": question}]
    }):
        last_message = step["messages"][-1]

        # 打印工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tc in last_message.tool_calls:
                print(f"\n[调用工具: {tc['name']}]")
                print(f"参数: {tc['args']}")
                print("Agent: ", end="", flush=True)

        # 打印最终回复
        if last_message.type == 'ai':
            if hasattr(last_message, 'content') and last_message.content:
                print(last_message.content)


# ============================================
# 使用示例
# ============================================

"""
# 1. 简单查询
result = query_weather("北京天气怎么样?")
print(result)

# 2. 多城市查询
result = query_weather("北京和上海的天气有什么区别?")
print(result)

# 3. 运行交互式 Agent
run_weather_agent()

# 4. 流式输出
stream_weather_agent("今天北京天气如何?")
"""

print("天气 Agent 代码已加载!")
print("使用方法:")
print("1. query_weather('北京天气') - 简单查询")
print("2. run_weather_agent() - 交互式查询")
print("3. stream_weather_agent('问题') - 流式输出")