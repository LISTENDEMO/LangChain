"""
AI 私厨 - 使用 LangChain 调用 API
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from langchain_anthropic import ChatAnthropic

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

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
    print("✅ 环境变量已加载")

# 创建 LangChain 模型
llm = ChatAnthropic(
    model="glm-5",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=120  # 增加到 120 秒
)

# 数据库存储
class Store:
    def __init__(self, path="chef.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS data(k TEXT PRIMARY KEY, v TEXT)")
        self.conn.commit()

    def get(self, k):
        r = self.conn.execute("SELECT v FROM data WHERE k=?", (k,)).fetchone()
        return json.loads(r[0]) if r else None

    def set(self, k, v):
        self.conn.execute("INSERT OR REPLACE INTO data(k,v) VALUES(?,?)", (k, json.dumps(v, ensure_ascii=False)))
        self.conn.commit()

store = Store()

# AI 调用
def call_ai(prompt, max_retries=3):
    import time
    for attempt in range(max_retries):
        try:
            print(f"[AI调用] 尝试 {attempt+1}/{max_retries}...")
            result = llm.invoke(prompt)
            # 处理返回格式
            content = result.content
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'text':
                        text = item.get('text', '')
                        print(f"[AI调用] 成功，返回 {len(text)} 字")
                        return text
            print(f"[AI调用] 成功，返回字符串")
            return str(content)
        except Exception as e:
            print(f"[AI错误] 尝试 {attempt+1} 失败: {e}")
            if attempt < max_retries - 1:
                print(f"[AI调用] 等待 5 秒后重试...")
                time.sleep(5)
            else:
                return f"AI调用失败，请稍后重试: {str(e)[:50]}"

def identify_image(image_base64):
    """识别图片中的食材 - 使用 LangChain qwen3.7-plus"""
    from langchain_core.messages import HumanMessage

    print("[图片识别] 调用 qwen3.7-plus 模型...")
    sys.stdout.flush()

    # 创建专门用于图片识别的模型
    vl_model = ChatAnthropic(
        model="qwen3.7-plus",
        anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
        api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
        timeout=120
    )

    try:
        # 构建多模态消息
        message = HumanMessage(
            content=[
                {"type": "text", "text": "识别图片中的食材，只列出名称用逗号分隔，如：番茄,鸡蛋"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )

        result = vl_model.invoke([message])

        # 处理返回格式
        content = result.content
        if isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    print(f"[图片识别] 成功: {text[:50]}...")
                    sys.stdout.flush()
                    return text

        print(f"[图片识别] 成功")
        sys.stdout.flush()
        return str(content)

    except Exception as e:
        print(f"[图片识别] 异常: {e}")
        sys.stdout.flush()
        return ""

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI 私厨</title>
<style>
body{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
.box{width:100%;max-width:600px;height:85vh;background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.2);display:flex;flex-direction:column}
.hd{background:linear-gradient(135deg,#f093fb,#f5576c);padding:15px 20px;color:#fff;border-radius:16px 16px 0 0}
.hd h1{font-size:18px;margin:0}
.hd p{font-size:12px;opacity:.8;margin:4px 0 0}
.chat{flex:1;overflow-y:auto;padding:15px;background:#f5f7fb}
.msg{margin:8px 0;display:flex}
.msg.me{justify-content:flex-end}
.bubble{max-width:80%;padding:10px 14px;border-radius:14px;line-height:1.4;font-size:14px}
.msg.me .bubble{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.msg.ai .bubble{background:#fff;box-shadow:0 2px 6px rgba(0,0,0,.1)}
.bubble img{max-width:120px;border-radius:8px;margin:4px 0;display:block}
.time{font-size:10px;opacity:.5;margin-top:4px}
.input{padding:15px;background:#fff;border-top:1px solid #eee}
.upload{border:2px dashed #ccc;border-radius:10px;padding:12px;text-align:center;margin-bottom:10px;background:#fafafa;cursor:pointer;position:relative}
.upload:hover{border-color:#667eea;background:#f0f4ff}
.upload.drag{border-color:#667eea;background:#e8f0ff}
.upload input{position:absolute;width:100%;height:100%;opacity:0;cursor:pointer;top:0;left:0}
.upload span{color:#888;font-size:13px}
.preview{display:none;align-items:center;gap:8px;padding:8px;background:#f8f9fa;border-radius:8px;margin-bottom:10px}
.preview.show{display:flex}
.preview img{width:50px;height:50px;object-fit:cover;border-radius:6px;border:2px solid #667eea}
.preview .name{font-size:12px;color:#333;flex:1}
.preview .del{width:24px;height:24px;background:#f5576c;color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:14px}
.row{display:flex;gap:8px}
.row textarea{flex:1;padding:10px;border:2px solid #eee;border-radius:10px;font-size:14px;resize:none;min-height:40px}
.row textarea:focus{border-color:#667eea;outline:none}
.row button{width:40px;height:40px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:10px;cursor:pointer;font-size:16px}
.row button:hover{transform:scale(1.05)}
.row button:disabled{opacity:.5}
.typing{display:flex;gap:4px;padding:10px}
.dot{width:6px;height:6px;background:#667eea;border-radius:50%;animation:b 1s infinite}
.dot:nth-child(2){animation-delay:.2s}
.dot:nth-child(3){animation-delay:.4s}
@keyframes b{0%,100%{opacity:.3}50%{opacity:1}}
</style>
</head>
<body>
<div class="box">
<div class="hd"><h1>🍳 AI 私厨</h1><p>上传食材图片，智能推荐食谱</p></div>
<div class="chat" id="chat">
<div class="msg ai"><div class="bubble">👋 嗨！我是AI私厨！<br><br>📷 点击下方区域或拖拽图片上传<br>💬 输入烹饪问题<br>❤️ 发送"添加喜爱食材：番茄"保存偏好</div></div>
</div>
<div class="input">
<div class="upload" id="up"><input type="file" accept="image/*" id="file"><span>📷 点击或拖拽图片到这里</span></div>
<div class="preview" id="prev"><img id="pimg"><div class="name" id="pname">图片</div><button class="del" id="delBtn">✕</button></div>
<div class="row"><textarea id="txt" placeholder="输入消息..." rows="1"></textarea><button id="sendBtn">➤</button></div>
</div>
</div>

<script>
let imgData=null,busy=false;
const up=document.getElementById('up');
const file=document.getElementById('file');
const prev=document.getElementById('prev');
const pimg=document.getElementById('pimg');
const pname=document.getElementById('pname');
const delBtn=document.getElementById('delBtn');
const txt=document.getElementById('txt');
const sendBtn=document.getElementById('sendBtn');
const chat=document.getElementById('chat');

// 文件选择
file.addEventListener('change', function(){
    if(this.files[0]) read(this.files[0]);
});

// 拖拽
up.addEventListener('dragover', function(e){
    e.preventDefault();
    this.classList.add('drag');
});
up.addEventListener('dragleave', function(){
    this.classList.remove('drag');
});
up.addEventListener('drop', function(e){
    e.preventDefault();
    this.classList.remove('drag');
    if(e.dataTransfer.files[0]) read(e.dataTransfer.files[0]);
});

// 读取文件
function read(f){
    const r=new FileReader();
    r.onload=function(e){
        imgData=e.target.result.split(',')[1];
        pimg.src=e.target.result;
        pname.textContent=f.name;
        prev.classList.add('show');
        up.style.display='none';
    };
    r.readAsDataURL(f);
}

// 删除图片
delBtn.addEventListener('click', function(){
    imgData=null;
    prev.classList.remove('show');
    up.style.display='block';
    file.value='';
});

// 发送
sendBtn.addEventListener('click', send);
txt.addEventListener('keydown', function(e){
    if(e.key==='Enter'&&!e.shiftKey){
        e.preventDefault();
        send();
    }
});

function send(){
    if(busy)return;
    const m=txt.value.trim();
    if(!m&&!imgData)return;

    // 保存图片数据，防止被清空
    const savedImgData=imgData;
    addMsg('me',m,savedImgData);
    txt.value='';

    busy=true;
    sendBtn.disabled=true;
    addTyping();

    fetch('/api',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({msg:m,img:savedImgData})
    })
    .then(r=>r.json())
    .then(d=>{
        rmTyping();
        addMsg('ai',d.r);
        busy=false;
        sendBtn.disabled=false;
        // 清空图片（在请求完成后）
        delBtn.click();
    })
    .catch(e=>{
        rmTyping();
        addMsg('ai','出错:'+e);
        busy=false;
        sendBtn.disabled=false;
    });
}

function addMsg(t,m,i){
    const d=document.createElement('div');
    d.className='msg '+t;
    let h='<div class="bubble">';
    if(i&&t==='me')h+='<img src="data:image/jpeg;base64,'+i+'">';
    if(m)h+=m.replace(/\\n/g,'<br>');
    h+='<div class="time">'+new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})+'</div></div>';
    d.innerHTML=h;
    chat.appendChild(d);
    chat.scrollTop=chat.scrollHeight;
}

function addTyping(){
    const d=document.createElement('div');
    d.className='msg ai';
    d.id='typ';
    d.innerHTML='<div class="bubble typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
    chat.appendChild(d);
    chat.scrollTop=chat.scrollHeight;
}

function rmTyping(){
    const t=document.getElementById('typ');
    if(t)t.remove();
}
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api', methods=['POST'])
def api():
    d = request.json
    msg = d.get('msg', '')
    img = d.get('img')
    uid = 'user1'

    print(f"[API] 收到请求: msg={msg[:20] if msg else 'empty'}, img={img is not None}")
    sys.stdout.flush()

    if img:
        # 识别食材
        print("[API] 处理图片...")
        sys.stdout.flush()
        ingredients = identify_image(img)
        if ingredients:
            recipe = call_ai(f"你是专业私厨。根据食材 {ingredients} 推荐一道菜，包括：名称、食材、步骤、时间、贴士。用热情友好的语气回复。")
            return jsonify({'r': f"📷 识别食材: {ingredients}\n\n{recipe}"})
        return jsonify({'r': "未能识别食材，请上传清晰的食材图片"})

    if '喜爱食材' in msg:
        fav = store.get(f'{uid}_fav') or []
        return jsonify({'r': f"❤️ 喜爱食材: {', '.join(fav)}" if fav else "暂无喜爱食材，发送 添加喜爱食材：番茄"})

    if '添加喜爱' in msg:
        ing = msg.split('：')[-1].split(':')[-1].strip()
        if ing:
            fav = store.get(f'{uid}_fav') or []
            fav.append(ing)
            store.set(f'{uid}_fav', fav)
            return jsonify({'r': f"✅ 已添加 {ing}！"})
        return jsonify({'r': "格式：添加喜爱食材：番茄"})

    if '历史' in msg:
        h = store.get(f'{uid}_hist') or []
        return jsonify({'r': f"📜 历史食谱: {', '.join(h[-5:])}" if h else "暂无历史食谱"})

    # 普通对话
    print("[API] 调用 call_ai...")
    sys.stdout.flush()
    r = call_ai(f"你是热情友好的AI私厨，擅长推荐食谱和烹饪建议。用户问：{msg}")
    print(f"[API] call_ai 返回: {r[:50]}...")
    sys.stdout.flush()
    h = store.get(f'{uid}_hist') or []
    h.append(msg[:20])
    store.set(f'{uid}_hist', h)
    return jsonify({'r': r})

if __name__ == "__main__":
    print("\n" + "="*50)
    print("AI 私厨已启动")
    print("地址: http://127.0.0.1:5000")
    print("="*50)
    app.run(host='127.0.0.1', port=5000)