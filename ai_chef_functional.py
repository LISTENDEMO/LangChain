"""
AI 私厨 LangGraph - 使用 Functional API
测试 LangGraph API 是否能正确处理工具调用
"""

import os
from pathlib import Path

print(">>> ai_chef_functional.py 版本: 2026-06-12-v1-FUNCTIONAL-API")

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

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages


# ============================================
# 1. 定义工具
# ============================================

@tool
def search_recipe(ingredient: str) -> str:
    """搜索指定食材的食谱

    Args:
        ingredient: 食材名称

    Returns:
        相关食谱推荐
    """
    recipes = {
        "番茄": "番茄炒蛋、番茄牛腩、番茄意面、番茄汤",
        "鸡蛋": "蒸蛋、炒蛋、蛋炒饭、蛋饼、茶叶蛋",
    }
    for key, value in recipes.items():
        if key in ingredient or ingredient in key:
            return f"找到 {key} 相关食谱: {value}"
    return f"未找到 '{ingredient}' 的专门食谱"


@tool
def get_ingredient_info(ingredient: str) -> str:
    """获取食材的营养和烹饪信息

    Args:
        ingredient: 食材名称

    Returns:
        食材的营养价值和烹饪建议
    """
    info_db = {
        "番茄": "富含维生素C和番茄红素，抗氧化。适合炒、煮、生吃。",
        "鸡蛋": "优质蛋白质，含卵磷脂。适合蒸、炒、煮。",
    }
    for key, value in info_db.items():
        if key in ingredient or ingredient in key:
            return value
    return f"'{ingredient}' 的营养信息暂未收录"


# 工具列表和映射
tools = [search_recipe, get_ingredient_info]
tools_by_name = {tool.name: tool for tool in tools}


# ============================================
# 2. 创建 LLM
# ============================================
llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=120,
    temperature=0.7
)

llm_with_tools = llm.bind_tools(tools)


# ============================================
# 3. 使用 Functional API 定义 Agent
# ============================================

SYSTEM_PROMPT = """你是热情友好的AI私厨！

**重要：你必须使用工具来完成任务！**

当用户提供食材时：
1. 必须先调用 get_ingredient_info 工具查询营养信息
2. 必须调用 search_recipe 工具搜索食谱
3. 基于工具返回的结果生成热情友好的回复

禁止直接回答！"""


@task
def call_llm(messages: list[BaseMessage]):
    """LLM 决定是否调用工具"""
    return llm_with_tools.invoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + messages
    )


@task
def call_tool(tool_call: dict):
    """执行工具调用"""
    tool = tools_by_name[tool_call["name"]]
    return tool.invoke(tool_call)


@entrypoint()
def agent(messages: list[BaseMessage]):
    """Agent 入口"""
    model_response = call_llm(messages).result()

    while True:
        if not model_response.tool_calls:
            break

        # 执行工具
        tool_result_futures = [
            call_tool(tool_call) for tool_call in model_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]

        # 添加消息
        messages = add_messages(messages, [model_response, *tool_results])

        # 再次调用 LLM
        model_response = call_llm(messages).result()

    # 返回最终消息
    messages = add_messages(messages, model_response)
    return messages


# ============================================
# 4. 导出 graph
# ============================================
graph = agent


# ============================================
# 5. 测试
# ============================================
if __name__ == "__main__":
    import asyncio
    import json

    async def test():
        print("\n=== 测试 ===")
        result = await graph.ainvoke([HumanMessage(content="番茄怎么做？")])

        print(f"消息数量: {len(result)}")
        for msg in result:
            print(f"  - {type(msg).__name__}")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print(f"    tool_calls: {msg.tool_calls}")

    asyncio.run(test())