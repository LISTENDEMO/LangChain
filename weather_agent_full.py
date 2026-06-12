"""
LangChain 天气查询 Agent - 完整版
修复中文编码问题,支持多种运行方式
"""

import sys
import io

# 设置 UTF-8 输出编码 (解决 Windows 中文乱码)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============================================
# 版本 1: 工具演示 (不需要 API Key)
# ============================================

from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天,温度 28°C,空气质量良好",
        "上海": "多云,温度 26°C,有轻微雾霾",
        "广州": "小雨,温度 30°C,湿度较高",
        "深圳": "晴天,温度 32°C,紫外线较强",
        "成都": "阴天,温度 22°C,建议带伞",
    }

    for key in weather_data:
        if key.lower() in city.lower() or city.lower() in key.lower():
            return weather_data[key]

    return f"未找到 '{city}' 的天气数据"


def demo_tool_usage():
    """演示工具直接调用"""
    print("=" * 60)
    print("【工具调用演示】")
    print("=" * 60)

    cities = ["北京", "上海", "广州"]
    for city in cities:
        result = get_weather.invoke({"city": city})
        print(f"\n查询 {city}:")
        print(f"  结果: {result}")

    print("\n" + "=" * 60)


# ============================================
# 版本 2: 真实天气 API (wttr.in)
# ============================================

import requests

@tool
def get_real_weather(city: str) -> str:
    """获取真实天气信息 (使用 wttr.in API)"""
    try:
        url = f"https://wttr.in/{city}?format=v2&lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"获取天气失败: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return "请求超时,请稍后重试"
    except Exception as e:
        return f"请求错误: {str(e)}"


@tool
def get_weather_forecast(city: str) -> str:
    """获取未来天气预报"""
    try:
        url = f"https://wttr.in/{city}?lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            return '\n'.join(lines[:8])  # 返回天气概况
        return "获取预报失败"

    except Exception as e:
        return f"错误: {str(e)}"


def demo_real_weather():
    """演示真实天气 API"""
    print("\n【真实天气 API 演示】")
    print("=" * 60)

    test_cities = ["Beijing", "Shanghai", "Tokyo"]

    for city in test_cities:
        print(f"\n查询 {city} 天气:")
        result = get_real_weather.invoke({"city": city})
        print(result[:150])  # 只显示前150字符

    print("\n" + "=" * 60)


# ============================================
# 版本 3: 完整 Agent (需要 API Key)
# ============================================

def create_weather_agent_with_key():
    """创建完整 Agent (需要设置 OPENAI_API_KEY)"""
    import os

    # 检查 API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  需要设置 OPENAI_API_KEY 环境变量!")
        print("\n设置方法:")
        print("  PowerShell: $env:OPENAI_API_KEY = 'sk-your-key'")
        print("  CMD:        set OPENAI_API_KEY=sk-your-key")
        print("  Linux/Mac:  export OPENAI_API_KEY='sk-your-key'")
        return None

    try:
        from langchain.agents import create_agent

        agent = create_agent(
            model="openai:gpt-4o-mini",
            tools=[get_real_weather, get_weather_forecast],
            system_prompt="""你是一个专业的天气助手。

功能:
- 查询当前天气
- 查询天气预报

使用工具获取信息后,用友好的方式向用户报告。
如果用户询问多个城市,分别查询并对比。
"""
        )

        print("\n✅ Agent 创建成功!")
        return agent

    except Exception as e:
        print(f"\n❌ Agent 创建失败: {e}")
        return None


def run_agent_interactive(agent):
    """交互式运行 Agent"""
    print("\n【交互式天气查询】")
    print("=" * 60)
    print("输入问题查询天气,输入 'quit' 退出")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n请输入问题: ")

            if user_input.lower() == 'quit':
                print("再见!")
                break

            result = agent.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

            final_message = result["messages"][-1]

            if hasattr(final_message, 'content_blocks'):
                print(f"\n天气助手: {final_message.content_blocks}")
            else:
                print(f"\n天气助手: {final_message.content}")

        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print("\n🌤️  LangChain 天气查询 Agent")
    print("=" * 60)

    # 1. 演示工具调用
    demo_tool_usage()

    # 2. 演示真实天气 API
    demo_real_weather()

    # 3. 尝试创建完整 Agent
    print("\n【创建完整 Agent】")
    print("=" * 60)
    agent = create_weather_agent_with_key()

    # 4. 如果 Agent 创建成功,运行交互模式
    if agent:
        run_agent_interactive(agent)

    print("\n" + "=" * 60)
    print("程序结束")
    print("=" * 60)


# ============================================
# 快速使用指南
# ============================================

"""
【快速使用】

1. 演示版 (不需要 API Key):
   python weather_agent_full.py

2. 完整版 (需要 API Key):
   # 先设置 API Key
   $env:OPENAI_API_KEY = "sk-your-key"

   # 再运行
   python weather_agent_full.py

3. 只查询真实天气:
   python weather_agent_full.py
   # 会自动调用 wttr.in API

【API 说明】

wttr.in - 免费,无需注册
- 支持全球城市
- 支持中文显示
- 实时天气数据

【扩展建议】

可以添加更多工具:
- 空气质量查询
- 天气预警
- 历史天气
- 穿衣建议
"""