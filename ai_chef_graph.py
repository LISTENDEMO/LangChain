"""
AI 私厨 LangGraph - 用于 LangGraph CLI 本地部署
支持流式输出和多模态图片输入
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Annotated

print(">>> ai_chef_graph.py 模块重新加载！版本: 2026-06-12-v8-FIX-IMAGE-FORMAT")

# 加载环境变量
ENV_PATH = r"C:\Users\92099\.claude\.env"
if Path(ENV_PATH).exists():
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ[key] = value.strip().strip('"').strip("'")

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage


# 使用 MessagesState (LangGraph 内置的消息状态，支持 Chat)
class State(MessagesState):
    """继承 MessagesState，自动支持 Chat 功能和流式输出"""
    pass


# 创建模型
llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=120,
    temperature=0.7
)


def convert_image_format(content_item: dict) -> dict:
    """
    将 LangSmith Studio 的图片格式转换为 LangChain/Anthropic 期望的格式

    LangSmith Studio 格式:
    {'type': 'image', 'data': 'base64...', 'source_type': 'base64', 'mime_type': 'image/png'}

    Anthropic API 期望格式:
    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': 'base64...'}}
    """
    if content_item.get("type") != "image":
        return content_item

    # 检查是否已经是正确的格式
    if "source" in content_item:
        return content_item

    # 转换格式
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": content_item.get("mime_type", "image/png"),
            "data": content_item.get("data", "")
        }
    }


def convert_message_content(content):
    """转换消息内容中的图片格式"""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        converted = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "image":
                    converted.append(convert_image_format(item))
                else:
                    converted.append(item)
            else:
                converted.append(item)
        return converted

    return content


# 定义节点 - 支持流式输出和多模态输入
async def chat(state: State) -> State:
    """
    与 LLM 对话，支持：
    1. 流式输出 (token-by-token)
    2. 多模态输入 (文本+图片)
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    print(f"[DEBUG] chat: messages count = {len(messages)}")

    # 构建完整的对话历史，转换图片格式
    conversation_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            # 转换图片格式
            converted_content = convert_message_content(msg.content)
            conversation_messages.append(HumanMessage(content=converted_content))

            # 调试：检查图片数量
            if isinstance(msg.content, list):
                image_count = sum(1 for item in msg.content if isinstance(item, dict) and item.get("type") == "image")
                if image_count > 0:
                    print(f"[DEBUG] converted {image_count} images in message")
        elif isinstance(msg, AIMessage):
            conversation_messages.append(msg)

    # 系统提示
    system_prompt = """你是热情友好的AI私厨，擅长推荐食谱和烹饪建议。

当用户提供食材或询问烹饪问题时：
1. 分析食材特点和用户需求
2. 提供多种烹饪方案（简单家常、进阶特色等）
3. 给出详细的步骤和独家小贴士
4. 用热情活泼的语气回复，多用表情符号

如果用户发送了图片，请先识别图片中的食材，然后给出相应的烹饪建议。"""

    # 构建完整的消息列表
    full_messages = [HumanMessage(content=system_prompt)] + conversation_messages

    # 使用流式调用 - 在 async 函数中使用 asyncio.to_thread 包装同步调用
    full_response = ""
    try:
        # 使用 asyncio.to_thread 包装阻塞的流式调用
        def stream_llm():
            response = ""
            for chunk in llm.stream(full_messages):
                content_chunk = chunk.content
                if isinstance(content_chunk, str) and content_chunk:
                    response += content_chunk
                elif isinstance(content_chunk, list):
                    for item in content_chunk:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            if text:
                                response += text
            return response

        full_response = await asyncio.to_thread(stream_llm)

    except Exception as e:
        print(f"[ERROR] LLM stream error: {e}")
        full_response = f"抱歉，处理您的请求时遇到了问题：{str(e)}"

    print(f"[DEBUG] response length: {len(full_response)} chars")

    # 返回 AI 消息
    return {"messages": [AIMessage(content=full_response)]}


# 构建图
def build_graph():
    """构建 LangGraph，支持流式输出"""
    graph = StateGraph(State)

    # 添加节点
    graph.add_node("chat", chat)

    # 添加边
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph.compile()


# 导出 graph (LangGraph CLI 会使用这个)
graph = build_graph()


if __name__ == "__main__":
    # 测试
    import asyncio

    async def test():
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="番茄怎么做？")]
        })
        print("结果:", result.get("messages", [])[-1].content[:100])

    asyncio.run(test())