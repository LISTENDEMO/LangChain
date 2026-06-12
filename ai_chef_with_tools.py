"""
AI 私厨 LangGraph - 手动构建带工具节点的 Graph
演示如何自定义 Agent + Tools 的调用循环
"""

import os
import asyncio
from pathlib import Path
from typing import Literal

print(">>> ai_chef_with_tools.py 版本: 2026-06-12-v1-MANUAL-TOOLS")

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

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AnyMessage
from langchain_core.tools import tool


# ============================================
# 1. 定义 State（使用 MessagesState 内置类型）
# ============================================
# MessagesState 内置了 messages 字段，并且配置了正确的追加逻辑
# 不需要手动定义 TypedDict

class State(MessagesState):
    """继承 MessagesState，自动处理消息追加"""
    pass


# ============================================
# 2. 定义工具（Tools）
# ============================================

@tool
def search_recipe(ingredient: str) -> str:
    """搜索指定食材的食谱

    Args:
        ingredient: 食材名称，如"番茄"、"鸡蛋"

    Returns:
        相关食谱推荐
    """
    # 模拟搜索结果（实际可以调用 Tavily 等 API）
    recipes = {
        "番茄": "番茄炒蛋、番茄牛腩、番茄意面、番茄汤",
        "鸡蛋": "蒸蛋、炒蛋、蛋炒饭、蛋饼、茶叶蛋",
        "土豆": "土豆丝、土豆泥、薯条、土豆炖牛肉",
        "鸡肉": "宫保鸡丁、鸡丁、白切鸡、鸡汤",
        "牛肉": "红烧牛肉、牛肉面、牛排、孜然牛肉",
    }

    # 模糊匹配
    for key, value in recipes.items():
        if key in ingredient or ingredient in key:
            return f"找到 {key} 相关食谱: {value}"

    return f"未找到 '{ingredient}' 的专门食谱，推荐搜索通用烹饪方法"


@tool
def get_ingredient_info(ingredient: str) -> str:
    """获取食材的营养和烹饪信息

    Args:
        ingredient: 食材名称

    Returns:
        食材的营养价值和烹饪建议
    """
    info_db = {
        "番茄": "富含维生素C和番茄红素，抗氧化。适合炒、煮、生吃。注意：烹饪后番茄红素更易吸收。",
        "鸡蛋": "优质蛋白质，含卵磷脂。适合蒸、炒、煮。注意：不要过度加热，以免营养流失。",
        "土豆": "富含淀粉和钾。适合炒、炖、烤。注意：发芽土豆有毒，不能食用。",
        "鸡肉": "高蛋白低脂肪。适合炒、炖、蒸。注意：煮熟透，避免沙门氏菌。",
        "牛肉": "富含铁和蛋白质。适合炖、炒、烤。注意：不要过度烹饪，保持嫩度。",
    }

    for key, value in info_db.items():
        if key in ingredient or ingredient in key:
            return value

    return f"'{ingredient}' 的营养信息暂未收录，建议查阅专业营养数据库"


@tool
def save_recipe(recipe_name: str, ingredients: str) -> str:
    """保存喜欢的食谱到收藏

    Args:
        recipe_name: 食谱名称
        ingredients: 主要食材

    Returns:
        保存结果确认
    """
    # 模拟保存到数据库
    print(f"[STORE] 已保存食谱: {recipe_name}, 食材: {ingredients}")
    return f"✅ 已将 '{recipe_name}' 添加到你的收藏！食材: {ingredients}"


# 工具列表
tools = [search_recipe, get_ingredient_info, save_recipe]


# ============================================
# 3. 创建 LLM（绑定工具）
# ============================================
llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=120,
    temperature=0.7
)

# 关键：绑定工具到 LLM
llm_with_tools = llm.bind_tools(tools)


# ============================================
# 4. 定义节点（Nodes）
# ============================================

async def agent_node(state: State) -> State:
    """Agent 节点：调用 LLM，可能返回 tool_calls"""
    messages = state["messages"]

    system_prompt = """你是热情友好的AI私厨！

**重要：你必须使用工具来完成任务！**

当用户提供食材或询问问题时：
1. **必须先调用 get_ingredient_info 工具**查询食材的营养信息
2. **必须调用 search_recipe 工具**搜索相关食谱
3. 如果用户要求保存/收藏，**必须调用 save_recipe 工具**

**禁止直接回答！你必须先调用工具获取数据，再基于工具返回的结果生成回复！**

示例对话：
用户: 番茄怎么做？
正确做法:
  - 先调用 get_ingredient_info("番茄")
  - 再调用 search_recipe("番茄")
  - 最后基于工具返回的数据，热情友好地回复

错误做法: 直接回答番茄的营养和食谱（禁止！）

如果用户说"保存xxx"，必须调用 save_recipe 工具！"""

    # 构建消息列表
    full_messages = [HumanMessage(content=system_prompt)] + messages

    # 调用 LLM（可能返回 tool_calls）
    # 使用 asyncio.to_thread 包装同步调用
    def call_llm():
        return llm_with_tools.invoke(full_messages)

    response = await asyncio.to_thread(call_llm)

    print(f"[DEBUG] Agent response: type={type(response).__name__}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"[DEBUG] Tool calls: {response.tool_calls}")

    # 返回新消息（追加到 state.messages）
    return {"messages": [response]}


# ============================================
# 5. 定义条件边（Conditional Edge）
# ============================================

def should_continue(state: State) -> Literal["tools", "end"]:
    """判断是否需要调用工具

    如果最后一条消息有 tool_calls，继续调用工具
    否则结束对话
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 检查是否有 tool_calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"  # 路由到工具节点

    return "end"  # 结束


# ============================================
# 6. 构建 Graph
# ============================================

def build_graph():
    """手动构建带工具节点的 Graph"""

    # 创建 StateGraph
    graph = StateGraph(State)

    # 添加节点
    graph.add_node("agent", agent_node)

    # 使用 LangGraph 预置的 ToolNode（自动执行工具并返回 ToolMessage）
    graph.add_node("tools", ToolNode(tools))

    # 添加边
    # START → agent
    graph.add_edge(START, "agent")

    # agent → 条件边
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # 有 tool_calls → 工具节点
            "end": END         # 无 tool_calls → 结束
        }
    )

    # tools → agent（工具执行后返回 agent 继续处理）
    graph.add_edge("tools", "agent")

    return graph.compile()


# 导出 graph（LangGraph CLI 使用）
graph = build_graph()


# ============================================
# 7. 测试运行
# ============================================
if __name__ == "__main__":
    async def test():
        import json

        print("\n=== 测试 1: 查询番茄 ===")
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="番茄怎么做？有什么营养？")]
        })

        # 写入文件查看完整结果
        output = []
        for msg in result["messages"]:
            msg_dict = {
                "type": type(msg).__name__,
                "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                "tool_calls": getattr(msg, 'tool_calls', None)
            }
            output.append(msg_dict)

        with open("test_tools_output.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"结果已写入 test_tools_output.json")
        print(f"总共 {len(result['messages'])} 条消息")

        print("\n=== 测试 2: 保存食谱 ===")
        result2 = await graph.ainvoke({
            "messages": [HumanMessage(content="把番茄炒蛋保存到我的收藏")]
        })

        output2 = []
        for msg in result2["messages"]:
            msg_dict = {
                "type": type(msg).__name__,
                "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                "tool_calls": getattr(msg, 'tool_calls', None)
            }
            output2.append(msg_dict)

        with open("test_tools_output2.json", "w", encoding="utf-8") as f:
            json.dump(output2, f, ensure_ascii=False, indent=2)

        print(f"结果已写入 test_tools_output2.json")
        print(f"总共 {len(result2['messages'])} 条消息")

    asyncio.run(test())