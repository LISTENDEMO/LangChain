"""
LangGraph 流式客户端示例
演示如何通过 LangGraph SDK 实现真正的流式输出
"""

import os
import asyncio
from pathlib import Path
from langgraph_sdk import get_client

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

# LangGraph 本地服务地址（langgraph dev 启动后的地址）
LANGGRAPH_API_URL = "http://127.0.0.1:2024"


async def stream_chat(message: str):
    """流式调用 LangGraph Agent"""

    # 连接本地 LangGraph 服务
    client = get_client(url=LANGGRAPH_API_URL)

    # 创建一个新的 thread（对话会话）
    thread = await client.threads.create()
    print(f"✅ 创建 thread: {thread['thread_id']}")

    # 流式发送消息
    print(f"\n📨 发送消息: {message}")
    print("=" * 50)
    print("🤖 AI 回复（流式）:\n")

    # 使用 stream 方法获取流式输出
    # mode="messages" 只返回消息，mode="values" 返回完整状态
    async for chunk in client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id="chef",  # langgraph.json 中定义的 graph 名称
        input={
            "messages": [
                {"role": "user", "content": message}
            ]
        },
        stream_mode="messages",  # 流式模式：messages | values | events
    ):
        # chunk.event 类型: "message" | "tool_call" | "tool_result" 等
        if chunk.event == "messages/partial":
            # 流式消息片段
            for msg in chunk.data:
                if msg.get("type") == "ai":
                    content = msg.get("content", "")
                    if content:
                        print(content, end="", flush=True)

        elif chunk.event == "messages/complete":
            # 消息完成
            print("\n")

    print("=" * 50)
    print("✅ 流式输出完成")


async def stream_events(message: str):
    """使用 astream_events 获取更详细的流式事件（包含工具调用）"""

    client = get_client(url=LANGGRAPH_API_URL)
    thread = await client.threads.create()

    print(f"\n📨 发送消息: {message}")
    print("=" * 50)

    async for event in client.runs.stream_events(
        thread_id=thread["thread_id"],
        assistant_id="chef",
        input={
            "messages": [{"role": "user", "content": message}]
        },
    ):
        # 事件类型包括：on_chain_start, on_chain_end, on_tool_start, on_tool_end 等
        event_type = event.event

        if "on_tool_start" in event_type:
            tool_name = event.data.get("name", "unknown")
            print(f"\n🔧 调用工具: {tool_name}")

        elif "on_tool_end" in event_type:
            tool_output = event.data.get("output", "")
            print(f"   ➡️ 结果: {tool_output[:100]}...")

        elif "on_chain_stream" in event_type:
            # LLM 流式输出片段
            content = event.data.get("chunk", {}).get("content", "")
            if content:
                print(content, end="", flush=True)


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 LangGraph 流式客户端测试")
    print("=" * 60)

    # 测试 1: 简单流式
    await stream_chat("番茄怎么做？有什么营养？")

    # 测试 2: 带工具调用的流式
    print("\n" + "-" * 60)
    print("测试 2: 带工具调用的事件流")
    print("-" * 60)
    await stream_events("请帮我查一下鸡蛋的营养信息，然后推荐几个食谱")


if __name__ == "__main__":
    asyncio.run(main())