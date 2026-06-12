"""
AI 私厨智能体 - Flask + 精美 HTML 对话界面

特点:
- 类似聊天应用的对话界面
- 支持图片上传和拖拽
- LangChain 后端
- 记忆功能
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

from flask import Flask, request, jsonify, render_template_string

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
    env_file = Path(env_path)
    if not env_file.exists():
        return False
    print(f"✅ 加载配置: {env_path}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip().strip('"').strip("'")
    return True

load_env_file(ENV_PATH)


# ============================================
# 配置
# ============================================

MEMORY_CONFIG = {
    "max_favorite_ingredients": 20,
    "max_recipe_history": 50,
}

MODEL_NAME = "qwen3.7-plus"


# ============================================
# SQLite 记忆存储
# ============================================

class ChefMemoryStore:
    def __init__(self, db_path: str = "chef_memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup()

    def _setup(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (namespace, key)
            )
        """)
        self.conn.commit()

    def put(self, namespace: str, key: str, value: dict):
        value_json = json.dumps(value, ensure_ascii=False)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO store (namespace, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (namespace, key, value_json))
        self.conn.commit()

    def get(self, namespace: str, key: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM store WHERE namespace = ? AND key = ?", (namespace, key))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None


# ============================================
# 食材识别
# ============================================

def identify_ingredients_from_base64(image_base64: str, image_type: str = "image/jpeg") -> list:
    import requests
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "识别图片中的食材，只列出名称，逗号分隔，如：番茄,鸡蛋,洋葱"},
                {"type": "image_url", "image_url": {"url": f"data:{image_type};base64,{image_base64}"}}
            ]
        }],
        "max_tokens": 200
    }

    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return [i.strip() for i in content.replace('，', ',').split(',') if i.strip()]
    except Exception as e:
        print(f"识别错误: {e}")
    return []


# ============================================
# 食谱生成
# ============================================

def generate_recipe(ingredients: list, user_prefs: dict, user_id: str, store: ChefMemoryStore) -> str:
    import requests
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    favorites = store.get("favorite_ingredients", user_id) or []
    pref_info = ""
    if favorites: pref_info += f"\n喜爱食材: {', '.join(favorites)}"
    if user_prefs.get("dietary"): pref_info += f"\n饮食偏好: {user_prefs['dietary']}"
    if user_prefs.get("spice"): pref_info += f"\n辣度: {user_prefs['spice']}"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    prompt = f"""你是专业私厨，根据食材推荐菜肴。

食材: {', '.join(ingredients)}
{pref_info}

请提供:
1. 食谱名称
2. 所需食材
3. 烹饪步骤（分步骤）
4. 烹饪时间
5. 小贴士

用热情语气，Markdown格式。"""

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800
    }

    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # 保存历史
            history = store.get("recipe_history", user_id) or []
            history.append({"name": ingredients[0] if ingredients else "未知", "ingredients": ingredients, "timestamp": datetime.now().isoformat()})
            if len(history) > MEMORY_CONFIG["max_recipe_history"]:
                history = history[-MEMORY_CONFIG["max_recipe_history"]:]
            store.put("recipe_history", user_id, history)
            return content
    except Exception as e:
        return f"生成失败: {e}"
    return "生成失败"


# ============================================
# 对话处理
# ============================================

def chat(message: str, user_id: str, store: ChefMemoryStore) -> str:
    import requests
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    favorites = store.get("favorite_ingredients", user_id) or []
    context = f"喜爱食材: {', '.join(favorites)}" if favorites else ""

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"你是热情的AI私厨。{context}"},
            {"role": "user", "content": message}
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"回复失败: {e}"
    return "回复失败"


# ============================================
# Flask 应用
# ============================================

app = Flask(__name__)
store = ChefMemoryStore("chef_memory.db")


HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 私厨</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: #fff;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px 25px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-avatar {
            width: 45px; height: 45px;
            background: #fff;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
        }
        .header-info h1 { color: #fff; font-size: 18px; }
        .header-info p { color: rgba(255,255,255,0.8); font-size: 12px; }

        .settings {
            background: #f8f9fa;
            padding: 12px 25px;
            display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
        }
        .settings input, .settings select {
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 13px;
        }

        .quick-actions {
            display: flex; gap: 8px;
            padding: 8px 25px;
            background: #fff;
        }
        .quick-btn {
            padding: 6px 14px;
            background: #f0f0f0;
            border: none;
            border-radius: 18px;
            font-size: 12px;
            cursor: pointer;
        }
        .quick-btn:hover { background: #667eea; color: #fff; }

        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 15px 25px;
            background: #f5f7fb;
        }
        .message { display: flex; margin-bottom: 12px; }
        .message.user { justify-content: flex-end; }
        .message-content {
            max-width: 75%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.5;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }
        .message.ai .message-content {
            background: #fff;
            color: #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .message-content img { max-width: 150px; border-radius: 8px; margin: 5px 0; }
        .message-time { font-size: 10px; opacity: 0.6; margin-top: 4px; }

        .input-area {
            padding: 15px 25px;
            background: #fff;
            border-top: 1px solid #eee;
        }

        /* 拖拽区域 */
        .drop-zone {
            border: 2px dashed #ddd;
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 10px;
            text-align: center;
            transition: all 0.2s;
            background: #fafafa;
            cursor: pointer;
        }
        .drop-zone:hover { border-color: #667eea; background: #f0f4ff; }
        .drop-zone.drag-over { border-color: #667eea; background: #e8f0ff; }
        .drop-zone-text { font-size: 13px; color: #888; }
        .drop-zone-text span { color: #667eea; }

        /* 图片预览 */
        .preview-box {
            display: none;
            align-items: center;
            gap: 10px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .preview-box.show { display: flex; }
        .preview-img { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 2px solid #667eea; }
        .preview-name { font-size: 13px; color: #333; flex: 1; }
        .remove-btn {
            width: 28px; height: 28px;
            background: #f5576c;
            border: none;
            border-radius: 50%;
            color: #fff;
            font-size: 16px;
            cursor: pointer;
        }
        .remove-btn:hover { background: #e94560; }

        .input-row { display: flex; gap: 10px; align-items: flex-end; }
        .text-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #eee;
            border-radius: 12px;
            font-size: 14px;
            resize: none;
            min-height: 44px;
            max-height: 100px;
        }
        .text-input:focus { outline: none; border-color: #667eea; }
        .send-btn {
            width: 44px; height: 44px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 18px;
            cursor: pointer;
        }
        .send-btn:hover { transform: scale(1.05); }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .typing { display: flex; gap: 4px; padding: 12px; }
        .typing-dot { width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: bounce 1.4s infinite; }
        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

        @media (max-width: 600px) {
            .container { height: 100vh; border-radius: 0; }
            .settings { flex-direction: column; }
            .message-content { max-width: 85%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-avatar">🍳</div>
            <div class="header-info">
                <h1>AI 私厨</h1>
                <p>上传食材图片，智能推荐食谱</p>
            </div>
        </div>

        <div class="settings">
            <label>👤 <input type="text" id="userId" value="user_001" style="width:80px"></label>
            <label>🥗 <select id="dietary"><option value="">无限制</option><option value="素食">素食</option><option value="低脂">低脂</option></select></label>
            <label>🌶️ <select id="spice"><option value="不辣">不辣</option><option value="微辣">微辣</option><option value="中辣">中辣</option></select></label>
        </div>

        <div class="quick-actions">
            <button class="quick-btn" onclick="quickSend('查看喜爱食材')">❤️ 喜爱食材</button>
            <button class="quick-btn" onclick="quickSend('查看历史食谱')">📜 历史食谱</button>
            <button class="quick-btn" onclick="quickSend('推荐家常菜')">💡 推荐</button>
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message ai">
                <div class="message-content">
                    👋 嗨！我是 AI 私厨！<br><br>
                    📸 点击或拖拽图片到下方区域<br>
                    💬 输入烹饪问题<br>
                    ❤️ 保存喜爱食材<br><br>
                    快来试试吧！
                </div>
            </div>
        </div>

        <div class="input-area">
            <!-- 拖拽区域 -->
            <div class="drop-zone" id="dropZone">
                <div class="drop-zone-text">📷 点击选择图片 或 <span>拖拽图片到这里</span></div>
                <input type="file" id="fileInput" accept="image/*" style="display:none">
            </div>

            <!-- 图片预览 -->
            <div class="preview-box" id="previewBox">
                <img class="preview-img" id="previewImg">
                <div class="preview-name" id="previewName">图片已选择</div>
                <button class="remove-btn" onclick="removeImage()">✕</button>
            </div>

            <!-- 输入行 -->
            <div class="input-row">
                <textarea class="text-input" id="textInput" placeholder="输入消息..."></textarea>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>

    <script>
        let imageData = null;
        let isTyping = false;

        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const previewBox = document.getElementById('previewBox');
        const previewImg = document.getElementById('previewImg');
        const previewName = document.getElementById('previewName');

        // 点击选择
        dropZone.onclick = () => fileInput.click();

        // 文件选择
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) handleFile(file);
        };

        // 拖拽事件
        dropZone.ondragover = (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        };
        dropZone.ondragleave = () => dropZone.classList.remove('drag-over');
        dropZone.ondrop = (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) handleFile(file);
        };

        // 处理文件
        function handleFile(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imageData = e.target.result;
                previewImg.src = imageData;
                previewName.textContent = file.name;
                previewBox.classList.add('show');
                dropZone.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }

        // 删除图片
        function removeImage() {
            imageData = null;
            previewBox.classList.remove('show');
            dropZone.style.display = 'block';
            fileInput.value = '';
        }

        // 快捷发送
        function quickSend(text) {
            document.getElementById('textInput').value = text;
            sendMessage();
        }

        // 发送消息
        async function sendMessage() {
            if (isTyping) return;

            const text = document.getElementById('textInput').value.trim();
            if (!text && !imageData) return;

            const userId = document.getElementById('userId').value;
            const dietary = document.getElementById('dietary').value;
            const spice = document.getElementById('spice').value;

            // 显示用户消息
            addMessage('user', text, imageData);

            // 清空
            document.getElementById('textInput').value = '';
            removeImage();

            // 加载动画
            isTyping = true;
            document.getElementById('sendBtn').disabled = true;
            showTyping();

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, image: imageData, userId, dietary, spice})
                });
                const data = await res.json();

                hideTyping();
                addMessage('ai', data.response);
            } catch (err) {
                hideTyping();
                addMessage('ai', '抱歉，出错了：' + err.message);
            }

            isTyping = false;
            document.getElementById('sendBtn').disabled = false;
        }

        // 添加消息
        function addMessage(type, text, img) {
            const chat = document.getElementById('chatArea');
            const time = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});

            let html = `<div class="message ${type}"><div class="message-content">`;
            if (img && type === 'user') html += `<img src="${img}">`;
            if (text) html += formatText(text);
            html += `<div class="message-time">${time}</div></div></div>`;

            chat.innerHTML += html;
            chat.scrollTop = chat.scrollHeight;
        }

        // 格式化文本
        function formatText(text) {
            text = text.replace(/\n/g, '<br>');
            text = text.replace(/### (.*)/g, '<b style="color:#f5576c">$1</b>');
            text = text.replace(/## (.*)/g, '<b style="color:#f5576c">$1</b>');
            text = text.replace(/^\\* (.*)/gm, '• $1');
            text = text.replace(/^- (.*)/gm, '• $1');
            return text;
        }

        // 加载动画
        function showTyping() {
            const chat = document.getElementById('chatArea');
            chat.innerHTML += `<div class="message ai" id="typing"><div class="message-content typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>`;
            chat.scrollTop = chat.scrollHeight;
        }
        function hideTyping() {
            const t = document.getElementById('typing');
            if (t) t.remove();
        }

        // 回车发送
        document.getElementById('textInput').onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        };
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/chat', methods=['POST'])
def chat_api():
    data = request.json
    message = data.get('message', '')
    image = data.get('image')
    user_id = data.get('userId', 'user_001')
    dietary = data.get('dietary', '')
    spice = data.get('spice', '')
    user_prefs = {'dietary': dietary, 'spice': spice}

    # 图片识别
    if image:
        img_type = 'image/jpeg' if 'jpeg' in image else 'image/png'
        img_base64 = image.split(',')[1] if ',' in image else image
        ingredients = identify_ingredients_from_base64(img_base64, img_type)

        if ingredients:
            recipe = generate_recipe(ingredients, user_prefs, user_id, store)
            return jsonify({'response': f"📷 识别食材: {', '.join(ingredients)}\n\n{recipe}"})
        return jsonify({'response': "未能识别食材，请上传清晰图片"})

    # 特殊命令
    if '喜爱食材' in message:
        favorites = store.get("favorite_ingredients", user_id) or []
        if favorites:
            return jsonify({'response': f"❤️ 喜爱食材: {', '.join(favorites)}"})
        return jsonify({'response': "暂无喜爱食材，发送 \"添加喜爱食材：番茄\" 来保存"})

    if '添加喜爱' in message:
        ingredient = message.replace('添加喜爱食材', '').replace('：', '').replace(':', '').strip()
        if ingredient:
            favorites = store.get("favorite_ingredients", user_id) or []
            favorites.append(ingredient)
            if len(favorites) > MEMORY_CONFIG['max_favorite_ingredients']:
                favorites = favorites[-MEMORY_CONFIG['max_favorite_ingredients']:]
            store.put("favorite_ingredients", user_id, favorites)
            return jsonify({'response': f"✅ 已添加 {ingredient}！"})
        return jsonify({'response': "格式：添加喜爱食材：番茄"})

    if '历史食谱' in message:
        history = store.get("recipe_history", user_id) or []
        if history:
            text = "📜 历史食谱:\n"
            for i, h in enumerate(history[-5:], 1):
                text += f"{i}. {h['name']} ({h['timestamp'][:10]})\n"
            return jsonify({'response': text})
        return jsonify({'response': "暂无历史记录"})

    # 普通对话
    response = chat(message, user_id, store)
    return jsonify({'response': response})


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("AI 私厨 - 精美对话界面")
    print("=" * 50)
    print(f"\n模型: {MODEL_NAME}")
    print("启动地址: http://127.0.0.1:5000")
    print("=" * 50)

    app.run(host='127.0.0.1', port=5000, debug=False)