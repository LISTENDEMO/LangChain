"""
AI 私厨智能体 - LangChain 版本

功能特性:
- 使用 LangChain 构建智能体
- 多模态模型识别食材图片
- 工具: 食材识别、食谱生成、记忆管理
- Gradio Web 界面
- 记忆功能 (SQLite)
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

from pydantic import BaseModel, Field

# 设置 UTF-8 编码
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# ============================================
# 加载环境变量
# ============================================

ENV_PATH = r"C:\Users\92099\.claude\.env"

def load_env_file(env_path: str):
    """加载 .env 文件"""
    env_file = Path(env_path)
    if not env_file.exists():
        print(f"⚠️ .env 文件不存在: {env_path}")
        return False

    print(f"✅ 加载配置文件: {env_path}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
                print(f"   {key} = {value[:20]}...")
    return True

load_env_file(ENV_PATH)


# ============================================
# 记忆管理配置
# ============================================

MEMORY_CONFIG = {
    "max_favorite_ingredients": 20,
    "max_recipe_history": 50,
    "history_expire_days": 60,
}


# ============================================
# 用户上下文
# ============================================

@dataclass
class ChefContext:
    """私厨用户上下文"""
    user_id: str


# ============================================
# SQLite 记忆存储
# ============================================

class ChefMemoryStore:
    """私厨记忆存储 - 实现 LangGraph Store 接口"""

    def __init__(self, db_path: str = "chef_memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup()
        print(f"   ✅ 私厨记忆存储已启用: {db_path}")

    def _setup(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (namespace, key)
            )
        """)
        self.conn.commit()

    def put(self, namespace: tuple, key: str, value: dict):
        """存储数据"""
        ns_key = "/".join(namespace)
        value_json = json.dumps(value, ensure_ascii=False)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO store (namespace, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (ns_key, key, value_json))
        self.conn.commit()
        print(f"   💾 已保存: {ns_key}/{key}")

    def get(self, namespace: tuple, key: str):
        """获取数据"""
        ns_key = "/".join(namespace)
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM store WHERE namespace = ? AND key = ?", (ns_key, key))
        row = cursor.fetchone()
        if row:
            class StoreItem:
                def __init__(self, v):
                    self.value = v
            return StoreItem(json.loads(row[0]))
        return None

    def delete(self, namespace: tuple, key: str):
        """删除数据"""
        ns_key = "/".join(namespace)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM store WHERE namespace = ? AND key = ?", (ns_key, key))
        self.conn.commit()

    def close(self):
        self.conn.close()


# ============================================
# LangChain 工具定义
# ============================================

from langchain.tools import tool, ToolRuntime
import base64
import requests

@tool
def identify_ingredients(image_path: str) -> str:
    """识别食材图片中的食材

    Args:
        image_path: 图片文件路径

    Returns:
        识别出的食材列表 (逗号分隔)
    """
    print(f"\n   🔍 正在识别食材: {image_path}")

    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 判断图片类型
        ext = Path(image_path).suffix.lower()
        image_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"

        # 调用多模态 API
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        model = "qwen3.7-plus"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "请识别这张图片中的食材。只列出食材名称，用逗号分隔，不要有其他描述。例如：番茄,鸡蛋,洋葱,土豆"},
                    {"type": "image_url", "image_url": {"url": f"data:{image_type};base64,{image_base64}"}}
                ]
            }],
            "max_tokens": 500
        }

        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            ingredients = [i.strip() for i in content.replace('，', ',').split(',') if i.strip()]
            print(f"   ✅ 识别成功: {len(ingredients)} 种食材")
            return f"识别到的食材: {', '.join(ingredients)}"
        else:
            print(f"   ❌ API 错误: {response.status_code}")
            return f"识别失败: API 错误 {response.status_code}"

    except Exception as e:
        print(f"   ❌ 识别错误: {e}")
        return f"识别失败: {str(e)}"


@tool
def save_favorite_ingredient(ingredient: str, runtime: ToolRuntime[ChefContext]) -> str:
    """保存喜爱的食材到记忆

    Args:
        ingredient: 食材名称
        runtime: 工具运行时环境

    Returns:
        保存结果
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id
    max_count = MEMORY_CONFIG["max_favorite_ingredients"]

    print(f"\n   💾 保存喜爱食材: {ingredient} (用户: {user_id})")

    data = runtime.store.get(("favorite_ingredients",), user_id)
    favorites = data.value if data else []

    if ingredient in favorites:
        return f"{ingredient} 已经在喜爱列表中了"

    if len(favorites) >= max_count:
        # 移除最旧的
        favorites = favorites[1:] + [ingredient]
        runtime.store.put(("favorite_ingredients",), user_id, favorites)
        print(f"   🔄 已替换最旧食材")
        return f"喜爱食材已达上限，已添加 {ingredient}"
    else:
        favorites.append(ingredient)
        runtime.store.put(("favorite_ingredients",), user_id, favorites)
        print(f"   ✅ 已添加 ({len(favorites)}/{max_count})")
        return f"已添加 {ingredient} 到喜爱食材 ({len(favorites)}/{max_count})"


@tool
def get_favorite_ingredients(runtime: ToolRuntime[ChefContext]) -> str:
    """获取用户喜爱的食材列表

    Args:
        runtime: 工具运行时环境

    Returns:
        喜爱食材列表
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🔍 获取喜爱食材 (用户: {user_id})")

    data = runtime.store.get(("favorite_ingredients",), user_id)
    favorites = data.value if data else []

    if favorites:
        print(f"   ✅ 找到 {len(favorites)} 种喜爱食材")
        return f"你喜爱的食材: {', '.join(favorites)} (共 {len(favorites)} 种)"
    else:
        print(f"   ⚠️ 暂无喜爱食材")
        return "暂无喜爱的食材，可以添加一些！"


@tool
def save_recipe_history(recipe_name: str, ingredients: str, runtime: ToolRuntime[ChefContext]) -> str:
    """保存食谱到历史记录

    Args:
        recipe_name: 食谱名称
        ingredients: 食材列表 (逗号分隔)
        runtime: 工具运行时环境

    Returns:
        保存结果
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id
    max_count = MEMORY_CONFIG["max_recipe_history"]

    print(f"\n   💾 保存食谱历史: {recipe_name} (用户: {user_id})")

    data = runtime.store.get(("recipe_history",), user_id)
    history = data.value if data else []

    # 添加新记录
    ingredient_list = [i.strip() for i in ingredients.split(',') if i.strip()]
    history.append({
        "name": recipe_name,
        "ingredients": ingredient_list,
        "timestamp": datetime.now().isoformat()
    })

    # 检查上限
    if len(history) > max_count:
        history = history[-max_count:]

    runtime.store.put(("recipe_history",), user_id, history)
    print(f"   ✅ 已保存 ({len(history)}/{max_count})")
    return f"已保存食谱 {recipe_name} 到历史 ({len(history)}/{max_count})"


@tool
def get_recipe_history(runtime: ToolRuntime[ChefContext]) -> str:
    """获取用户的历史食谱

    Args:
        runtime: 工具运行时环境

    Returns:
        历史食谱列表
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   🔍 获取食谱历史 (用户: {user_id})")

    data = runtime.store.get(("recipe_history",), user_id)
    history = data.value if data else []

    if history:
        print(f"   ✅ 找到 {len(history)} 条食谱")
        recent = history[-5:]
        result = "最近食谱:\n"
        for i, r in enumerate(recent, 1):
            result += f"{i}. {r['name']} ({r['timestamp'][:10]})\n"
        return result
    else:
        print(f"   ⚠️ 暂无历史食谱")
        return "暂无历史食谱记录"


@tool
def get_memory_stats(runtime: ToolRuntime[ChefContext]) -> str:
    """获取记忆使用统计

    Args:
        runtime: 工具运行时环境

    Returns:
        记忆统计信息
    """
    assert runtime.store is not None
    user_id = runtime.context.user_id

    print(f"\n   📊 获取记忆统计 (用户: {user_id})")

    fav_data = runtime.store.get(("favorite_ingredients",), user_id)
    favorites = fav_data.value if fav_data else []

    hist_data = runtime.store.get(("recipe_history",), user_id)
    history = hist_data.value if hist_data else []

    stats = f"""记忆统计:
- 喜爱食材: {len(favorites)}/{MEMORY_CONFIG['max_favorite_ingredients']}
- 食谱历史: {len(history)}/{MEMORY_CONFIG['max_recipe_history']}"""

    print(f"   ✅ {stats}")
    return stats


# ============================================
# LangChain Agent 创建
# ============================================

def create_chef_agent(store: ChefMemoryStore):
    """创建私厨 Agent"""
    from langchain_anthropic import ChatAnthropic
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    model_name = "qwen3.7-plus"
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    print(f"\n🔧 Agent 配置:")
    print(f"   模型: {model_name}")
    print(f"   API: {base_url}")

    model = ChatAnthropic(
        model=model_name,
        anthropic_api_url=base_url,
        api_key=api_key,
        timeout=60,
        temperature=0.7
    )

    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        tools=[
            identify_ingredients,
            save_favorite_ingredient,
            get_favorite_ingredients,
            save_recipe_history,
            get_recipe_history,
            get_memory_stats,
        ],
        checkpointer=checkpointer,
        store=store,
        context_schema=ChefContext,
        system_prompt="""你是一位专业的 AI 私厨，擅长根据食材推荐美味食谱。

角色设定:
- 你是一位经验丰富的大厨，擅长各种菜系
- 热情友好，乐于帮助用户烹饪美食
- 会根据用户偏好调整推荐

功能:
1. 食材识别 (identify_ingredients): 识别用户上传的食材图片
2. 食谱推荐: 根据食材推荐合适的做法
3. 记忆管理:
   - 保存喜爱食材 (save_favorite_ingredient)
   - 获取喜爱食材 (get_favorite_ingredients)
   - 保存食谱历史 (save_recipe_history)
   - 获取历史食谱 (get_recipe_history)
   - 获取记忆统计 (get_memory_stats)

工作流程:
1. 用户上传图片 → 调用 identify_ingredients 识别食材
2. 根据识别的食材 → 推荐合适的食谱和做法
3. 保存食谱到历史 → 调用 save_recipe_history
4. 用户喜欢某些食材 → 调用 save_favorite_ingredient

回复风格:
- 友好热情的问候
- 清晰的烹饪步骤说明
- 实用的烹饪小贴士
"""
    )

    print("\n✅ Agent 创建成功!")
    return agent


# ============================================
# Gradio Web 界面
# ============================================

def create_web_interface():
    """创建 Gradio Web 界面"""
    import gradio as gr

    # 创建 Agent 和存储
    store = ChefMemoryStore("chef_memory.db")
    agent = create_chef_agent(store)

    default_user = "web_user_001"

    def process_image(image, user_id, dietary_pref, spice_level):
        """处理图片"""
        if image is None:
            return "请上传食材图片！", "", ""

        # 保存临时图片
        temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        if isinstance(image, str):
            temp_path = image
        else:
            import cv2
            cv2.imwrite(temp_path, image)

        # 创建上下文
        context = ChefContext(user_id=user_id)
        thread_config = {"configurable": {"thread_id": f"chef_{user_id}_{datetime.now().strftime('%H%M%S')}"}}

        # 构建请求
        user_prefs = f"\n饮食偏好: {dietary_pref}\n辣度偏好: {spice_level}"
        prompt = f"""请识别这张食材图片，并根据识别的食材推荐一道美味的菜肴。

{user_prefs}

请提供:
1. 识别的食材列表
2. 食谱名称
3. 所需食材
4. 详细烹饪步骤
5. 烹饪时间
6. 小贴士

图片路径: {temp_path}"""

        try:
            # 调用 Agent
            result = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=thread_config,
                context=context
            )

            # 获取回复
            last_msg = result["messages"][-1]
            response = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

            # 获取统计
            stats_result = agent.invoke(
                {"messages": [{"role": "user", "content": "获取我的记忆统计"}]},
                config=thread_config,
                context=context
            )
            stats = stats_result["messages"][-1].content

            return temp_path, response, stats

        except Exception as e:
            return temp_path, f"处理失败: {e}", ""

    def add_favorite(ingredient, user_id):
        """添加喜爱食材"""
        context = ChefContext(user_id=user_id)
        thread_config = {"configurable": {"thread_id": f"fav_{datetime.now().strftime('%H%M%S')}"}}

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"请把 {ingredient} 添加到我的喜爱食材"}]},
                config=thread_config,
                context=context
            )
            return result["messages"][-1].content
        except Exception as e:
            return f"添加失败: {e}"

    def get_history(user_id):
        """获取历史"""
        context = ChefContext(user_id=user_id)
        thread_config = {"configurable": {"thread_id": f"hist_{datetime.now().strftime('%H%M%S')}"}}

        try:
            # 获取历史食谱
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "查看我的历史食谱"}]},
                config=thread_config,
                context=context
            )
            return result["messages"][-1].content
        except Exception as e:
            return f"获取失败: {e}"

    # 创建界面
    with gr.Blocks(title="AI 私厨") as demo:
        gr.Markdown("""
        # AI 私厨智能体

        上传食材图片，智能识别食材并推荐合适的食谱！

        **使用 LangChain 构建**
        """)

        with gr.Row():
            with gr.Column(scale=2):
                image_input = gr.Image(label="上传食材图片", type="filepath")
                user_id_input = gr.Textbox(label="用户 ID", value=default_user)

                with gr.Row():
                    dietary_input = gr.Dropdown(
                        label="饮食偏好",
                        choices=["无限制", "素食", "低糖", "低脂", "清真"],
                        value="无限制"
                    )
                    spice_input = gr.Dropdown(
                        label="辣度",
                        choices=["不辣", "微辣", "中辣", "特辣"],
                        value="微辣"
                    )

                analyze_btn = gr.Button("分析食材并推荐食谱", variant="primary")

            with gr.Column(scale=3):
                image_output = gr.Textbox(label="图片路径")
                recipe_output = gr.Textbox(label="食谱推荐", lines=15)
                stats_output = gr.Textbox(label="记忆统计")

        with gr.Row():
            favorite_input = gr.Textbox(label="添加喜爱食材")
            add_btn = gr.Button("添加")
            favorite_result = gr.Textbox(label="结果")

        with gr.Row():
            history_btn = gr.Button("查看历史食谱")
            history_output = gr.Textbox(label="历史", lines=10)

        # 绑定事件
        analyze_btn.click(
            process_image,
            inputs=[image_input, user_id_input, dietary_input, spice_input],
            outputs=[image_output, recipe_output, stats_output]
        )

        add_btn.click(
            add_favorite,
            inputs=[favorite_input, user_id_input],
            outputs=[favorite_result]
        )

        history_btn.click(
            get_history,
            inputs=[user_id_input],
            outputs=[history_output]
        )

    return demo


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI 私厨智能体 - LangChain 版本")
    print("=" * 60)

    print("\n启动 Web 界面...")
    print("   地址: http://127.0.0.1:7860")

    try:
        demo = create_web_interface()
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()