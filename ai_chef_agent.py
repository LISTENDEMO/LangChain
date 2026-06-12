"""
AI 私厨智能体 - 食材识别 + 食谱推荐 + Web 界面

功能特性:
- 上传食材图片自动识别食材
- 根据食材推荐合适的食谱和做法
- 保存用户偏好食材和历史食谱
- Web 界面 (Gradio)
- 多模态模型 (qwen3.7-plus)
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field  # 导入 pydantic

# 设置 UTF-8 编码
if __name__ == "__main__":
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

# 加载环境变量
load_env_file(ENV_PATH)

# ============================================
# 记忆管理配置
# ============================================

MEMORY_CONFIG = {
    "max_favorite_ingredients": 20,    # 喜爱食材最大数量
    "max_recipe_history": 50,          # 食谱历史最大数量
    "max_dietary_preferences": 10,     # 饮食偏好最大数量
    "history_expire_days": 60,         # 食谱历史过期天数
}


# ============================================
# 数据模型
# ============================================

@dataclass
class UserContext:
    """用户上下文"""
    user_id: str


class Recipe(BaseModel):
    """食谱结构"""
    name: str = Field(description="食谱名称")
    ingredients: list[str] = Field(description="所需食材列表")
    steps: list[str] = Field(description="烹饪步骤")
    cooking_time: str = Field(description="预计烹饪时间")
    difficulty: str = Field(description="难度等级 (简单/中等/困难)")
    tips: list[str] = Field(description="烹饪小贴士")


# ============================================
# SQLite 存储 (记忆功能)
# ============================================

class ChefMemoryStore:
    """私厨记忆存储 - SQLite 数据库"""

    def __init__(self, db_path: str = "chef_memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup()
        print(f"   ✅ 私厨记忆存储已启用: {db_path}")

    def _setup(self):
        """创建数据库表"""
        cursor = self.conn.cursor()

        # 用户偏好表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                favorite_ingredients TEXT,
                dietary_restrictions TEXT,
                cuisine_preferences TEXT,
                spice_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 食谱历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                recipe_name TEXT,
                ingredients TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 食材识别历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredient_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                identified_ingredients TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def save_preference(self, user_id: str, preference_type: str, value: Any):
        """保存用户偏好"""
        cursor = self.conn.cursor()

        # 检查用户是否存在
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            cursor.execute(f"""
                UPDATE user_preferences
                SET {preference_type} = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (json.dumps(value, ensure_ascii=False), user_id))
        else:
            cursor.execute("""
                INSERT INTO user_preferences (user_id, favorite_ingredients, dietary_restrictions, cuisine_preferences, spice_level)
                VALUES (?, ?, '{}', '{}', 'medium')
            """, (user_id, json.dumps(value, ensure_ascii=False) if preference_type == 'favorite_ingredients' else '{}'))

        self.conn.commit()
        print(f"   💾 已保存偏好: {preference_type}")

    def get_preference(self, user_id: str, preference_type: str) -> Any:
        """获取用户偏好"""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT {preference_type} FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

    def save_recipe_history(self, user_id: str, recipe_name: str, ingredients: list, rating: int = None):
        """保存食谱历史"""
        cursor = self.conn.cursor()

        # 检查历史数量，清理过期记录
        cursor.execute("""
            SELECT id, created_at FROM recipe_history WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        records = cursor.fetchall()

        # 超过上限时删除最旧的
        if len(records) >= MEMORY_CONFIG["max_recipe_history"]:
            to_delete = records[MEMORY_CONFIG["max_recipe_history"]:]
            for record in to_delete:
                cursor.execute("DELETE FROM recipe_history WHERE id = ?", (record[0],))
            print(f"   🧹 已清理 {len(to_delete)} 条旧食谱记录")

        cursor.execute("""
            INSERT INTO recipe_history (user_id, recipe_name, ingredients, rating)
            VALUES (?, ?, ?, ?)
        """, (user_id, recipe_name, json.dumps(ingredients, ensure_ascii=False), rating))

        self.conn.commit()
        print(f"   💾 已保存食谱: {recipe_name}")

    def get_recipe_history(self, user_id: str, limit: int = 10) -> list:
        """获取食谱历史"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT recipe_name, ingredients, rating, created_at
            FROM recipe_history WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        return cursor.fetchall()

    def save_ingredient_detection(self, user_id: str, ingredients: list, image_path: str = None):
        """保存食材识别记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ingredient_history (user_id, identified_ingredients, image_path)
            VALUES (?, ?, ?)
        """, (user_id, json.dumps(ingredients, ensure_ascii=False), image_path))
        self.conn.commit()
        print(f"   💾 已保存食材识别: {len(ingredients)} 种食材")

    def get_user_stats(self, user_id: str) -> dict:
        """获取用户统计"""
        cursor = self.conn.cursor()

        stats = {
            "favorite_ingredients_count": 0,
            "recipe_history_count": 0,
            "max_favorite_ingredients": MEMORY_CONFIG["max_favorite_ingredients"],
            "max_recipe_history": MEMORY_CONFIG["max_recipe_history"],
        }

        # 喜爱食材数量
        favorites = self.get_preference(user_id, "favorite_ingredients")
        if favorites:
            stats["favorite_ingredients_count"] = len(favorites)

        # 食谱历史数量
        cursor.execute("SELECT COUNT(*) FROM recipe_history WHERE user_id = ?", (user_id,))
        stats["recipe_history_count"] = cursor.fetchone()[0]

        return stats

    def close(self):
        """关闭连接"""
        self.conn.close()


# ============================================
# 食材识别 (多模态模型)
# ============================================

def identify_ingredients_from_image(image_path: str) -> list[str]:
    """使用多模态模型识别食材

    Args:
        image_path: 图片路径

    Returns:
        识别出的食材列表
    """
    import base64
    import requests

    print(f"\n   🔍 正在识别食材...")

    # 读取图片并转为 base64
    with open(image_path, 'rb') as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')

    # 获取 API 配置
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    model = "qwen3.7-plus"  # 使用指定的多模态模型

    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 判断图片类型
    image_type = "image/jpeg" if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg') else "image/png"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张图片中的食材。只列出食材名称，用逗号分隔，不要有其他描述。例如：番茄,鸡蛋,洋葱,土豆"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_type};base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 解析食材列表
            ingredients = [i.strip() for i in content.replace('，', ',').split(',') if i.strip()]

            print(f"   ✅ 识别成功: {len(ingredients)} 种食材")
            for ing in ingredients:
                print(f"      - {ing}")

            return ingredients
        else:
            print(f"   ❌ API 错误: {response.status_code}")
            return []

    except Exception as e:
        print(f"   ❌ 识别失败: {e}")
        return []


# ============================================
# 食谱生成 (LLM)
# ============================================

def generate_recipe(ingredients: list[str], user_preferences: dict = None, memory_store: ChefMemoryStore = None, user_id: str = "default") -> dict:
    """根据食材生成食谱

    Args:
        ingredients: 食材列表
        user_preferences: 用户偏好
        memory_store: 记忆存储
        user_id: 用户ID

    Returns:
        食谱信息
    """
    import requests

    print(f"\n   🍳 正在生成食谱...")

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    model = "qwen3.7-plus"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 构建用户偏好信息
    preference_info = ""
    if user_preferences:
        if user_preferences.get("dietary_restrictions"):
            preference_info += f"\n饮食限制: {user_preferences['dietary_restrictions']}"
        if user_preferences.get("cuisine_preferences"):
            preference_info += f"\n口味偏好: {user_preferences['cuisine_preferences']}"
        if user_preferences.get("spice_level"):
            preference_info += f"\n辣度偏好: {user_preferences['spice_level']}"

    # 获取历史喜爱食材
    favorite_ingredients = []
    if memory_store:
        favorites = memory_store.get_preference(user_id, "favorite_ingredients")
        if favorites:
            favorite_ingredients = favorites
            preference_info += f"\n喜爱食材: {', '.join(favorites)}"

    prompt = f"""你是一位专业的私厨，请根据以下食材设计一道美味的菜肴。

食材列表: {', '.join(ingredients)}
{preference_info}

请提供:
1. 食谱名称
2. 需要的额外食材（如果有）
3. 详细的烹饪步骤（分步骤说明）
4. 预计烹饪时间
5. 难度等级
6. 烹饪小贴士

请用 JSON 格式输出:
{
    "name": "食谱名称",
    "ingredients": ["完整食材列表"],
    "steps": ["步骤1", "步骤2", ...],
    "cooking_time": "预计时间",
    "difficulty": "简单/中等/困难",
    "tips": ["小贴士1", "小贴士2", ...]
}"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的私厨，擅长根据食材设计美味菜肴。请总是用 JSON 格式输出食谱。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 解析 JSON
            try:
                # 提取 JSON 部分
                if '{' in content and '}' in content:
                    json_start = content.index('{')
                    json_end = content.rindex('}') + 1
                    json_str = content[json_start:json_end]
                    recipe = json.loads(json_str)
                else:
                    recipe = {"name": "未知食谱", "steps": [content]}

                print(f"   ✅ 食谱生成成功: {recipe.get('name', '未知')}")

                # 保存到记忆
                if memory_store:
                    memory_store.save_recipe_history(user_id, recipe.get('name', '未知'), ingredients)

                return recipe

            except json.JSONDecodeError:
                print(f"   ⚠️ JSON 解析失败，返回原始内容")
                return {"name": "推荐菜肴", "steps": [content]}

        else:
            print(f"   ❌ API 错误: {response.status_code}")
            return {"error": f"API 错误: {response.status_code}"}

    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        return {"error": str(e)}


# ============================================
# Gradio Web 界面
# ============================================

def create_web_interface():
    """创建 Gradio Web 界面"""

    import gradio as gr

    # 初始化记忆存储
    memory_store = ChefMemoryStore("chef_memory.db")

    # 当前用户（默认）
    current_user = "web_user_001"

    def process_image(image, user_id, dietary_preference, spice_level):
        """处理上传的图片"""
        if image is None:
            return "请先上传食材图片！", "", ""

        # 保存图片临时文件
        temp_path = f"temp_ingredient_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Gradio 返回的是 numpy 数组或文件路径
        if isinstance(image, str):
            temp_path = image
        else:
            import cv2
            cv2.imwrite(temp_path, image)

        # 识别食材
        ingredients = identify_ingredients_from_image(temp_path)

        if not ingredients:
            return "未能识别食材，请上传清晰的食材图片！", "", ""

        # 保存识别记录
        memory_store.save_ingredient_detection(user_id, ingredients, temp_path)

        # 获取用户偏好
        user_prefs = {
            "dietary_restrictions": dietary_preference,
            "spice_level": spice_level
        }

        # 生成食谱
        recipe = generate_recipe(ingredients, user_prefs, memory_store, user_id)

        if "error" in recipe:
            return f"生成失败: {recipe['error']}", "", ""

        # 格式化输出
        ingredient_text = "识别的食材:\n" + "\n".join([f"• {i}" for i in ingredients])

        recipe_text = f"""# {recipe.get('name', '推荐菜肴')}

**烹饪时间**: {recipe.get('cooking_time', '未知')}
**难度**: {recipe.get('difficulty', '未知')}

## 所需食材
{chr(10).join([f'- {i}' for i in recipe.get('ingredients', ingredients)])}

## 烹饪步骤
{chr(10).join([f'{i+1}. {step}' for i, step in enumerate(recipe.get('steps', []))])}

## 小贴士
{chr(10).join([f'💡 {tip}' for tip in recipe.get('tips', [])])}
"""

        # 获取记忆统计
        stats = memory_store.get_user_stats(user_id)
        stats_text = f"""📊 记忆统计:
- 喜爱食材: {stats['favorite_ingredients_count']}/{stats['max_favorite_ingredients']}
- 食谱历史: {stats['recipe_history_count']}/{stats['max_recipe_history']}
"""

        return ingredient_text, recipe_text, stats_text

    def add_favorite_ingredient(ingredient, user_id):
        """添加喜爱食材"""
        if not ingredient:
            return "请输入食材名称！"

        favorites = memory_store.get_preference(user_id, "favorite_ingredients") or []
        if ingredient not in favorites:
            favorites.append(ingredient)
            # 检查上限
            if len(favorites) > MEMORY_CONFIG["max_favorite_ingredients"]:
                favorites = favorites[-MEMORY_CONFIG["max_favorite_ingredients"]:]
            memory_store.save_preference(user_id, "favorite_ingredients", favorites)
            return f"✅ 已添加 {ingredient} 到喜爱食材！"
        return f"{ingredient} 已经在喜爱列表中了"

    def get_history(user_id):
        """获取历史食谱"""
        history = memory_store.get_recipe_history(user_id, limit=10)
        if not history:
            return "暂无历史食谱"

        text = "📜 历史食谱:\n\n"
        for i, (name, ingredients, rating, date) in enumerate(history, 1):
            text += f"{i}. **{name}** ({date[:10]})\n"
            if ingredients:
                ings = json.loads(ingredients) if isinstance(ingredients, str) else ingredients
                text += f"   食材: {', '.join(ings[:5])}...\n"
        return text

    # 创建界面 (Gradio 6.0 兼容)
    with gr.Blocks(title="AI 私厨") as demo:
        gr.Markdown("""
        # 🍳 AI 私厨智能体

        上传食材图片，智能识别食材并推荐合适的食谱！

        **功能**:
        - 🔍 食材图片识别
        - 🍲 智能食谱推荐
        - 📝 详细烹饪步骤
        - 💾 记忆用户偏好
        """)

        with gr.Row():
            with gr.Column(scale=2):
                # 图片上传
                image_input = gr.Image(
                    label="上传食材图片",
                    type="filepath"
                )

                # 用户设置
                user_id_input = gr.Textbox(
                    label="用户 ID",
                    value="web_user_001",
                    placeholder="输入你的用户ID"
                )

                with gr.Row():
                    dietary_input = gr.Dropdown(
                        label="饮食偏好",
                        choices=["无限制", "素食", "低糖", "低脂", "清真", "高蛋白"],
                        value="无限制"
                    )
                    spice_input = gr.Dropdown(
                        label="辣度偏好",
                        choices=["不辣", "微辣", "中辣", "特辣"],
                        value="中辣"
                    )

                # 操作按钮
                analyze_btn = gr.Button("🔍 分析食材并生成食谱", variant="primary", size="lg")

            with gr.Column(scale=3):
                # 输出区域
                ingredient_output = gr.Textbox(
                    label="识别的食材",
                    lines=5
                )
                recipe_output = gr.Markdown(
                    label="推荐食谱"
                )
                stats_output = gr.Textbox(
                    label="记忆统计",
                    lines=3
                )

        # 喜爱食材管理
        with gr.Row():
            favorite_input = gr.Textbox(
                label="添加喜爱食材",
                placeholder="例如：番茄、土豆..."
            )
            add_favorite_btn = gr.Button("❤️ 添加喜爱食材")
            favorite_output = gr.Textbox(label="结果")

        # 历史记录
        with gr.Row():
            history_btn = gr.Button("📜 查看历史食谱")
            history_output = gr.Textbox(
                label="历史食谱",
                lines=10
            )

        # 绑定事件
        analyze_btn.click(
            process_image,
            inputs=[image_input, user_id_input, dietary_input, spice_input],
            outputs=[ingredient_output, recipe_output, stats_output]
        )

        add_favorite_btn.click(
            add_favorite_ingredient,
            inputs=[favorite_input, user_id_input],
            outputs=[favorite_output]
        )

        history_btn.click(
            get_history,
            inputs=[user_id_input],
            outputs=[history_output]
        )

        gr.Markdown("""
        ---
        **使用说明**:
        1. 上传食材照片（建议清晰、光线充足）
        2. 设置用户 ID 和饮食偏好
        3. 点击"分析食材并生成食谱"
        4. 可以添加喜爱的食材，系统会记住你的偏好

        **记忆功能**:
        - 喜爱食材最多保存 20 种
        - 食谱历史最多保存 50 条
        - 数据保存到本地 SQLite 数据库
        """)

    return demo


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    # 设置输出编码
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("\n" + "=" * 60)
    print("AI 私厨智能体")
    print("   食材识别 + 食谱推荐 + Web 界面")
    print("=" * 60)

    print("\n配置:")
    print(f"   模型: qwen3.7-plus (多模态)")
    print(f"   API: {os.environ.get('ANTHROPIC_BASE_URL', '未设置')}")

    print("\n启动 Web 界面...")
    print("   地址: http://127.0.0.1:7860")
    print("   按 Ctrl+C 停止服务")

    # 创建并启动界面
    try:
        demo = create_web_interface()
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()