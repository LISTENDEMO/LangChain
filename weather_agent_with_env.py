"""
LangChain 天气查询 Agent - 使用本地 .env 配置
自动加载本地配置文件中的 API Key
"""

import sys
import io
import os
from pathlib import Path

# 设置 UTF-8 输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

            # 解析 key=value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # 设置环境变量
                os.environ[key] = value
                print(f"   {key} = {value[:20]}...")  # 只显示前20字符

    return True


# 加载配置 (使用原始字符串避免转义问题)
ENV_PATH = r"C:\Users\92099\.claude\.env"
load_env_file(ENV_PATH)


# ============================================
# 定义天气工具
# ============================================

from langchain.tools import tool
import requests

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    Args:
        city: 城市名称，如 "北京"、"Beijing"

    Returns:
        天气信息字符串
    """
    # 模拟天气数据 (作为备用)
    weather_data = {
        "北京": "晴天，温度 28°C，空气质量良好",
        "上海": "多云，温度 26°C，有轻微雾霾",
        "广州": "小雨，温度 30°C，湿度较高",
        "深圳": "晴天，温度 32°C，紫外线较强",
    }

    for key in weather_data:
        if key.lower() in city.lower():
            return weather_data[key]

    return f"未找到 '{city}' 的模拟数据，请使用真实天气 API"


@tool
def get_real_weather(city: str) -> str:
    """获取真实天气信息 (使用 wttr.in 免费 API)。

    Args:
        city: 城市名称 (支持中文和英文)

    Returns:
        天气信息字符串
    """
    try:
        # wttr.in 支持中文显示
        url = f"https://wttr.in/{city}?format=v2&lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"获取天气失败: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except Exception as e:
        return f"请求错误: {str(e)}"


@tool
def get_weather_forecast(city: str) -> str:
    """获取未来3天天气预报。

    Args:
        city: 城市名称

    Returns:
        天气预报信息
    """
    try:
        url = f"https://wttr.in/{city}?lang=zh"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            return '\n'.join(lines[:10])  # 返回天气概况
        return "获取预报失败"

    except Exception as e:
        return f"错误: {str(e)}"


# ============================================
# 创建 Agent (使用配置文件中的模型)
# ============================================

def create_weather_agent():
    """创建天气 Agent"""

    # 检查必要的环境变量
    required_vars = ["ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"]
    missing = [v for v in required_vars if not os.environ.get(v)]

    if missing:
        print(f"\n❌ 缺少环境变量: {missing}")
        print("\n请检查 .env 文件内容")
        return None

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain.agents import create_agent

        # 获取配置
        model_name = os.environ.get("ANTHROPIC_MODEL", "glm-5")
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

        print(f"\n🔧 Agent 配置:")
        print(f"   模型: {model_name}")
        print(f"   API: {base_url}")

        # 创建模型
        model = ChatAnthropic(
            model=model_name,
            anthropic_api_url=base_url,
            api_key=api_key,
            timeout=30,
            temperature=0.7
        )

        # 创建 Agent
        agent = create_agent(
            model=model,
            tools=[get_real_weather, get_weather_forecast],
            system_prompt="""你是一个专业的天气助手。

功能:
- 查询当前天气 (使用 get_real_weather 工具)
- 查询天气预报 (使用 get_weather_forecast 工具)

使用工具获取信息后，用友好的中文向用户报告天气情况。
如果用户询问多个城市，分别查询并对比天气。
如果工具返回的信息不够清晰，用自己的理解整理回复。
"""
        )

        print("\n✅ Agent 创建成功!")
        return agent

    except Exception as e:
        print(f"\n❌ Agent 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================
# 运行 Agent
# ============================================

def run_agent_demo(agent):
    """运行 Agent 示例查询"""
    print("\n" + "=" * 60)
    print("【Agent 查询演示】")
    print("=" * 60)

    test_questions = [
        "北京今天天气怎么样?",
        "上海和广州的天气有什么区别?",
        "Tokyo 的天气如何?"
    ]

    for question in test_questions:
        print(f"\n用户: {question}")
        print("-" * 40)

        try:
            result = agent.invoke({
                "messages": [{"role": "user", "content": question}]
            })

            # 获取最终回复
            final_message = result["messages"][-1]

            if hasattr(final_message, 'content_blocks'):
                response = final_message.content_blocks
            elif hasattr(final_message, 'content'):
                response = final_message.content
            else:
                response = str(final_message)

            print(f"Agent: {response}")

        except Exception as e:
            print(f"错误: {e}")

        print()


def run_agent_interactive(agent):
    """交互式运行 Agent"""
    print("\n" + "=" * 60)
    print("【交互式天气查询】")
    print("=" * 60)
    print("输入问题查询天气，输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n请输入问题: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见! 👋")
                break

            if not user_input:
                print("请输入有效问题")
                continue

            print("\n思考中...")
            print("-" * 40)

            result = agent.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

            final_message = result["messages"][-1]

            if hasattr(final_message, 'content_blocks'):
                response = final_message.content_blocks
            elif hasattr(final_message, 'content'):
                response = final_message.content
            else:
                response = str(final_message)

            print(f"\n天气助手: {response}")

        except KeyboardInterrupt:
            print("\n\n再见! 👋")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🌤️  LangChain 天气查询 Agent")
    print("使用本地 .env 配置")
    print("=" * 60)

    # 创建 Agent
    agent = create_weather_agent()

    if agent:
        # 选择运行模式
        print("\n请选择运行模式:")
        print("  1 - 自动演示 (运行预设问题)")
        print("  2 - 交互模式 (自定义问题)")
        print("  其他 - 直接退出")

        choice = input("\n请输入选择 (1/2): ").strip()

        if choice == '1':
            run_agent_demo(agent)
        elif choice == '2':
            run_agent_interactive(agent)
        else:
            print("\n退出程序")

    else:
        print("\n无法创建 Agent，请检查配置文件")

    print("\n" + "=" * 60)
    print("程序结束")
    print("=" * 60)