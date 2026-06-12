"""
AI 私厨 LangGraph - 使用 create_react_agent 预构建 Agent
LangGraph API 能正确识别预构建 agent 的工具
"""

import os
from pathlib import Path

print(">>> ai_chef_react.py 版本: 2026-06-12-v2-REACT-AGENT")

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
from langgraph.prebuilt import create_react_agent


# ============================================
# 1. 定义工具（Tools）
# ============================================

@tool
def search_recipe(ingredient: str) -> str:
    """搜索指定食材的食谱

    Args:
        ingredient: 食材名称，如"番茄"、"鸡蛋"

    Returns:
        相关食谱推荐
    """
    recipes = {
        "番茄": "番茄炒蛋、番茄牛腩、番茄意面、番茄汤",
        "鸡蛋": "蒸蛋、炒蛋、蛋炒饭、蛋饼、茶叶蛋",
        "土豆": "土豆丝、土豆泥、薯条、土豆炖牛肉",
        "鸡肉": "宫保鸡丁、鸡丁、白切鸡、鸡汤",
        "牛肉": "红烧牛肉、牛肉面、牛排、孜然牛肉",
    }

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
    print(f"[STORE] 已保存食谱: {recipe_name}, 食材: {ingredients}")
    return f"✅ 已将 '{recipe_name}' 添加到你的收藏！食材: {ingredients}"


# 工具列表
tools = [search_recipe, get_ingredient_info, save_recipe]


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


# ============================================
# 3. 使用 create_react_agent 创建 Agent
# ============================================

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

# 使用 create_react_agent（LangGraph API 能正确识别工具）
graph = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt
)


# ============================================
# 4. 测试运行
# ============================================
if __name__ == "__main__":
    import asyncio
    import json
    from langchain_core.messages import HumanMessage

    async def test():
        print("\n=== 测试 1: 查询番茄 ===")
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="番茄怎么做？有什么营养？")]
        })

        output = []
        for msg in result["messages"]:
            msg_dict = {
                "type": type(msg).__name__,
                "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                "tool_calls": getattr(msg, 'tool_calls', None)
            }
            output.append(msg_dict)

        with open("test_react_output.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"结果已写入 test_react_output.json")
        print(f"总共 {len(result['messages'])} 条消息")

        # 打印消息类型
        for msg in result["messages"]:
            print(f"  - {type(msg).__name__}")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print(f"    tool_calls: {msg.tool_calls}")

    asyncio.run(test())