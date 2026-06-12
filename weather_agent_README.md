# 天气查询 Agent 使用指南

## 📦 安装依赖

```bash
# 核心依赖
pip install langchain langchain-core

# 模型提供商 (选择其一)
pip install langchain-openai      # OpenAI
pip install langchain-anthropic   # Anthropic (Claude)

# HTTP 请求 (用于真实 API)
pip install requests

# 设置 API Key
export OPENAI_API_KEY=sk-xxx      # Linux/Mac
# 或
set OPENAI_API_KEY=sk-xxx         # Windows PowerShell
```

## 🚀 快速开始

### 方式 1: 简单版 (模拟数据)

```python
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    # 模拟数据
    weather_data = {
        "北京": "晴天，28°C",
        "上海": "多云，26°C",
    }
    return weather_data.get(city, "未找到该城市")

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    system_prompt="你是天气助手，使用工具查询天气"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "北京天气怎么样?"}]
})

print(result["messages"][-1].content)
```

### 方式 2: 真实 API 版

```python
import requests
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def get_real_weather(city: str) -> str:
    """获取真实天气 (wttr.in API)"""
    url = f"https://wttr.in/{city}?format=v2&lang=zh"
    response = requests.get(url, timeout=10)
    return response.text.strip()

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_real_weather],
    system_prompt="你是专业天气助手"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "查询北京天气"}]
})
print(result["messages"][-1].content)
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `weather_agent.py` | 完整代码示例 |
| `weather_agent_README.md` | 本使用指南 |

## 🔧 运行代码

```bash
cd "G:\claude code\.claude\LangChain"

# 运行完整示例
python weather_agent.py
```

## 🌐 支持的模型

```python
# OpenAI
agent = create_agent(model="openai:gpt-4o-mini", tools=[get_weather])

# Anthropic Claude
agent = create_agent(model="claude-sonnet-4-6", tools=[get_weather])

# Google Gemini
agent = create_agent(model="google_genai:gemini-2.5-flash", tools=[get_weather])

# 本地模型 (Ollama)
agent = create_agent(model="ollama:llama3", tools=[get_weather])
```

## 💬 查询示例

```python
# 单城市查询
query_weather("北京天气怎么样?")

# 多城市对比
query_weather("北京和上海的天气有什么区别?")

# 天气预报
query_weather("未来三天北京的天气预报")

# 英文城市
query_weather("What's the weather in Tokyo?")
```

## 🎯 Agent 工作流程

```
用户提问: "北京天气怎么样?"
    ↓
Agent 分析意图
    ↓
选择工具: get_weather(city="北京")
    ↓
执行工具: 返回 "晴天，28°C"
    ↓
Agent 生成回复: "北京今天天气晴朗，温度28°C，适合出行..."
    ↓
返回用户
```

## 📊 输出解析

```python
result = agent.invoke({"messages": [{"role": "user", "content": "北京天气"}]})

# 获取最终消息
final_message = result["messages"][-1]

# 获取内容
if hasattr(final_message, 'content_blocks'):
    print(final_message.content_blocks)
else:
    print(final_message.content)
```

## 🔍 流式输出 (推荐)

```python
# 流式输出 - 更好的用户体验
for step in agent.stream({"messages": [{"role": "user", "content": "北京天气"}]}):
    last_message = step["messages"][-1]
    
    # 查看工具调用
    if hasattr(last_message, 'tool_calls'):
        print(f"[工具调用: {last_message.tool_calls}]")
    
    # 打印回复
    if last_message.type == 'ai':
        print(last_message.content)
```

## 🛠️ 添加更多工具

```python
from langchain.tools import tool

@tool
def get_weather_forecast(city: str) -> str:
    """获取未来天气预报"""
    url = f"https://wttr.in/{city}?lang=zh"
    response = requests.get(url)
    return response.text

@tool
def get_air_quality(city: str) -> str:
    """获取空气质量"""
    # 实现空气质量查询
    return f"{city} 空气质量指数: 85"

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_real_weather, get_weather_forecast, get_air_quality],
    system_prompt="你是全方位天气助手，提供天气、预报、空气质量信息"
)
```

## ⚠️ 注意事项

1. **API Key**: 确保设置正确的 `OPENAI_API_KEY` 或其他模型 API Key

2. **网络请求**: 真实 API 版需要网络连接，wttr.in 可能需要几秒响应

3. **超时处理**: 添加 `timeout=10` 防止请求卡住

4. **错误处理**: 工具函数中添加 try-except

```python
@tool
def get_weather(city: str) -> str:
    """获取天气"""
    try:
        response = requests.get(url, timeout=10)
        return response.text
    except requests.exceptions.Timeout:
        return "请求超时"
    except Exception as e:
        return f"错误: {str(e)}"
```

## 📚 相关学习

查看完整 LangChain 教程:
- `LangChain全面学习指南.md` - 从基础到高级的完整教程

## 🐛 常见问题

### Q: 报错 "OpenAI API key not found"

```bash
# 设置环境变量
export OPENAI_API_KEY=sk-your-key-here
```

### Q: 工具没有被调用

确保工具函数有正确的 docstring，Agent 通过 docstring 理解工具用途:

```python
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""  # ← 这个很重要!
    return weather_data.get(city)
```

### Q: 响应太慢

```python
# 使用更快的模型
agent = create_agent(model="openai:gpt-4o-mini", tools=[...])

# 或使用流式输出
for chunk in agent.stream(...):
    print(chunk)
```

## 🎉 扩展方向

- 添加更多天气 API (如 OpenWeatherMap、WeatherAPI)
- 支持地理位置查询
- 添加天气预警功能
- 集成到聊天机器人
- 添加历史天气查询

---

**祝你使用愉快!** 🌤️