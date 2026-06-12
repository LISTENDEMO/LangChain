# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LangChain 学习与实践项目，包含多个 Agent 实现示例和教程文档。

核心应用:
- **AI 私厨**: Flask Web + 流式输出 + 多模态图片识别
- **天气 Agent**: LangGraph Agent + 工具调用 + 流式输出 + 长期记忆
- **LangGraph 部署**: 支持 LangGraph CLI 本地部署和 LangSmith Studio 可视化

## Environment & Commands

```bash
# 包管理器: uv (优先使用)
cd "G:\claude code\.claude\LangChain"

# 安装依赖
uv sync

# 运行 Python 文件
uv run python <file>.py

# 运行测试
uv run python test_memory.py

# LangGraph CLI 本地部署 (用于 LangSmith Studio)
uv run langgraph dev --no-browser
# 访问 http://127.0.0.1:2024 在 LangSmith Studio 连接

# 运行 AI 私厨 Web 服务 (Flask)
uv run python ai_chef_v4.py
# 访问 http://127.0.0.1:5000
```

## Python Version

- Python 3.11 (见 `.python-version`)
- 虚拟环境: `.venv/`

## Environment Variables

API 配置位于 `C:\Users\92099\.claude\.env`:
```
ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
ANTHROPIC_AUTH_TOKEN="sk-sp-xxx"
```

加载方式:
```python
ENV_PATH = r"C:\Users\92099\.claude\.env"
# 手动读取文件加载环境变量
```

## Key Applications

| 文件 | 功能 | 说明 |
|------|------|------|
| `ai_chef_v4.py` | AI 私厨 Web | Flask + 流式输出 + 多模态图片识别 |
| `ai_chef_graph.py` | LangGraph 版 AI 私厨 | 用于 LangGraph CLI 部署 |
| `weather_agent_streaming.py` | 天气 Agent | LangGraph Agent + Tools + 流式 + 长期记忆 |
| `langgraph.json` | LangGraph 配置 | 定义 graph 入口和依赖 |
| `test_*.py` | 测试文件 | 记忆、数据库持久化等测试 |

## Architecture

**LangGraph 部署架构**:
```
ai_chef_graph.py:graph  ← langgraph.json 定义入口
    ↓
LangGraph CLI (langgraph dev)
    ↓
LangSmith Studio (http://127.0.0.1:2024)
    ↓
Chat 交互 / Debug 可视化
```

**天气 Agent 记忆系统**:
- `InMemorySaver`: checkpointer，保存对话历史 (Short-Term)
- `InMemoryStore`: store，保存结构化用户数据 (Long-Term)
- 数据库持久化: SQLite (`weather_checkpoints.db`)

## API Configuration

使用 DashScope Anthropic 格式 API:
- Endpoint: `https://coding.dashscope.aliyuncs.com/apps/anthropic`
- Key 格式: `sk-sp-xxx` (App SDK专用)

模型选择:
- `qwen3.7-plus`: 多模态模型，支持图片识别
- `glm-5`: 文本模型 (响应较慢)

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
)
```

## Streaming Implementation

Flask 流式响应:
```python
from flask import Response, stream_with_context

def generate():
    for chunk in llm.stream(prompt):
        # 过滤空 chunk (LangChain stream 可能返回大量空 chunk)
        if chunk.content:
            yield chunk.content

return Response(
    stream_with_context(generate()),
    mimetype='text/plain; charset=utf-8'
)
```

## Documentation

- `LangChain全面学习指南.md` - 完整教程
- `LangChain官方文档总结.md` - 官方文档要点
- `weather_agent_README.md` - 天气 Agent 使用指南

## Dependencies

见 `pyproject.toml`:
- langchain, langchain-anthropic, langgraph
- flask, gradio
- dashscope, requests

## Common Patterns

**环境变量加载** (项目中多处使用):
```python
ENV_PATH = r"C:\Users\92099\.claude\.env"
if Path(ENV_PATH).exists():
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ[key] = value.strip().strip('"').strip("'")
```

**LangGraph State 定义**:
```python
from langgraph.graph import StateGraph, MessagesState

class State(MessagesState):
    """继承 MessagesState，自动支持 Chat 功能"""
    pass
```

**注意**: LangSmith Studio Chat 模式发送的消息 content 可能是 list 格式 (多模态)，需要处理:
```python
content = last_message.content
if isinstance(content, list):
    # 提取文本部分
    text_parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_parts.append(item.get("text", ""))
    content = " ".join(text_parts)
```