"""
AI 私厨 - 流式输出版本
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, request, Response, render_template_string, stream_with_context
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

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

# 创建 LangChain 模型（用于文本对话）
# 使用 qwen3.7-plus 模型，响应速度更快 (TTFB 约 0.8s)
llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=120,  # 增加超时时间
    temperature=0.7,
    max_retries=2  # 添加重试
)

# 创建视觉模型（用于图片识别）- 使用更长的超时
vl_model = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=180,  # 图片识别需要更长超时
    temperature=0.3,  # 图片识别用低温度更准确
    max_retries=2
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

# 流式 AI 调用
def stream_ai(prompt):
    """流式调用 AI，实时返回文本"""
    try:
        for chunk in llm.stream(prompt):
            content = chunk.content
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'text':
                        text = item.get('text', '')
                        # 只返回有内容的 chunk（过滤空 chunk）
                        if text:
                            yield text
            elif isinstance(content, str) and content:
                yield content
    except Exception as e:
        yield f"[错误: {e}]"

# 流式图片识别
def stream_identify_and_recipe(image_base64):
    """流式识别图片并生成食谱"""
    try:
        # 1. 先发送识别提示
        yield "📷 正在识别食材...\n\n"
        yield "⏳ 图片分析中，请耐心等待...\n\n"

        # 2. 识别图片（非流式）
        message = HumanMessage(
            content=[
                {"type": "text", "text": "识别图片中的食材，只列出名称用逗号分隔，简洁回答"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )

        try:
            result = vl_model.invoke([message])
        except Exception as api_error:
            # 处理 API 错误
            error_msg = str(api_error)
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                yield "⚠️ 图片识别超时，请尝试上传更小的图片或稍后重试\n\n"
                yield "💡 建议：图片大小建议不超过 500KB，格式为 JPG 或 PNG\n"
                return
            elif "connection" in error_msg.lower():
                yield "⚠️ 网络连接问题，请检查网络后重试\n"
                return
            else:
                yield f"⚠️ 图片识别出错: {error_msg[:100]}\n"
                return

        ingredients = ""
        content = result.content
        if isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    ingredients = item.get('text', '')
                    break
        elif isinstance(content, str):
            ingredients = content

        if not ingredients or "没有食材" in ingredients.lower() or "无法识别" in ingredients.lower():
            yield "⚠️ 未识别到食材，请上传包含清晰食材的图片\n\n"
            yield "💡 建议：确保图片中食材清晰可见，光线充足\n"
            return

        # 3. 马上显示识别结果和预设思考过程
        yield f"✅ 识别到食材: {ingredients}\n\n"
        yield "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        yield "🤔 **思考过程**\n\n"
        yield "⏳ 正在分析食材特点...\n"
        yield "⏳ 考虑适合的烹饪方法...\n"
        yield "⏳ 选择最佳菜谱方案...\n\n"
        yield "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        yield "📝 **食谱推荐**\n\n"

        # 4. 流式生成食谱（AI 详细输出）
        recipe_prompt = f"""你是专业私厨。根据食材 {ingredients} 推荐一道菜。

请按以下格式回复：

🍽️ **菜名**：xxx

📝 **所需食材**：
- xxx
- xxx

👨‍🍳 **制作步骤**：
1. xxx
2. xxx

⏱️ **烹饪时间**：xxx 分钟

💡 **小贴士**：xxx

用热情友好的语气，格式清晰易读，每行开头用 emoji。"""

        for chunk in llm.stream(recipe_prompt):
            content = chunk.content
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'text':
                        text = item.get('text', '')
                        if text:
                            yield text
            elif isinstance(content, str) and content:
                yield content

    except Exception as e:
        yield f"[错误: {e}]"

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
.bubble{max-width:80%;padding:10px 14px;border-radius:14px;line-height:1.5;font-size:14px;white-space:pre-wrap}
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
</style>
</head>
<body>
<div class="box">
<div class="hd"><h1>AI 私厨</h1><p>上传食材图片，智能推荐食谱（流式响应）</p></div>
<div class="chat" id="chat">
<div class="msg ai"><div class="bubble">👋 嗨！我是AI私厨！
📷 点击下方上传食材图片
💬 输入烹饪问题
❤️ 发送"添加喜爱食材：番茄"保存偏好</div></div>
</div>
<div class="input">
<div class="upload" id="up"><input type="file" accept="image/*" id="file"><span>📷 点击或拖拽图片</span></div>
<div class="preview" id="prev"><img id="pimg"><div class="name" id="pname">图片</div><button class="del" id="delBtn">X</button></div>
<div class="row"><textarea id="txt" placeholder="输入消息..." rows="1"></textarea><button id="sendBtn">></button></div>
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
file.addEventListener('change',function(){
    if(this.files[0]) read(this.files[0]);
});

// 拖拽
up.addEventListener('dragover',function(e){
    e.preventDefault();
    this.classList.add('drag');
});
up.addEventListener('dragleave',function(){
    this.classList.remove('drag');
});
up.addEventListener('drop',function(e){
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
delBtn.addEventListener('click',function(){
    imgData=null;
    prev.classList.remove('show');
    up.style.display='block';
    file.value='';
});

// 发送
sendBtn.addEventListener('click',send);
txt.addEventListener('keydown',function(e){
    if(e.key==='Enter'&&!e.shiftKey){
        e.preventDefault();
        send();
    }
});

function send(){
    if(busy)return;
    const m=txt.value.trim();
    if(!m&&!imgData)return;

    const savedImgData=imgData;
    addMsg('me',m,savedImgData);
    txt.value='';

    busy=true;
    sendBtn.disabled=true;

    // 创建 AI 消息气泡（用于流式填充）
    const aiMsg=addAiMsg('');

    // 使用流式请求
    fetch('/stream',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({msg:m,img:savedImgData})
    })
    .then(response=>{
        const reader=response.body.getReader();
        const decoder=new TextDecoder();

        function readChunk(){
            reader.read().then(({done,value})=>{
                if(done){
                    busy=false;
                    sendBtn.disabled=false;
                    addTime(aiMsg);
                    delBtn.click();
                    return;
                }
                const text=decoder.decode(value,{stream:true});
                appendText(aiMsg,text);
                chat.scrollTop=chat.scrollHeight;
                readChunk();
            });
        }
        readChunk();
    })
    .catch(e=>{
        appendText(aiMsg,'出错:'+e);
        busy=false;
        sendBtn.disabled=false;
    });
}

function addMsg(t,m,i){
    const d=document.createElement('div');
    d.className='msg '+t;
    let h='<div class="bubble">';
    if(i&&t==='me')h+='<img src="data:image/jpeg;base64,'+i+'">';
    if(m)h+=escapeHtml(m);
    h+='<div class="time">'+new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})+'</div></div>';
    d.innerHTML=h;
    chat.appendChild(d);
    chat.scrollTop=chat.scrollHeight;
    return d;
}

function addAiMsg(m){
    const d=document.createElement('div');
    d.className='msg ai';
    d.id='ai-'+Date.now();
    d.innerHTML='<div class="bubble">'+escapeHtml(m)+'</div>';
    chat.appendChild(d);
    chat.scrollTop=chat.scrollHeight;
    return d;
}

function appendText(el,text){
    const bubble=el.querySelector('.bubble');
    bubble.textContent+=text;
}

function addTime(el){
    const bubble=el.querySelector('.bubble');
    const time=document.createElement('div');
    time.className='time';
    time.textContent=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
    bubble.appendChild(time);
}

function escapeHtml(text){
    return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/stream', methods=['POST'])
def stream_api():
    """流式 API 端点"""
    d = request.json
    msg = d.get('msg', '')
    img = d.get('img')
    uid = 'user1'

    def generate():
        if img:
            # 图片识别 + 食谱生成（流式）
            for text in stream_identify_and_recipe(img):
                yield text
        elif '喜爱食材' in msg:
            fav = store.get(f'{uid}_fav') or []
            result = f"喜爱食材: {', '.join(fav)}" if fav else "暂无喜爱食材"
            yield result
        elif '添加喜爱' in msg:
            ing = msg.split('：')[-1].split(':')[-1].strip()
            if ing:
                fav = store.get(f'{uid}_fav') or []
                fav.append(ing)
                store.set(f'{uid}_fav', fav)
                yield f"已添加 {ing}"
            else:
                yield "格式：添加喜爱食材：番茄"
        elif '历史' in msg:
            h = store.get(f'{uid}_hist') or []
            result = f"历史食谱: {', '.join(h[-5:])}" if h else "暂无历史食谱"
            yield result
        else:
            # 普通对话（流式）
            prompt = f"你是热情友好的AI私厨，擅长推荐食谱和烹饪建议。用户问：{msg}"
            for text in stream_ai(prompt):
                yield text
            # 保存历史
            h = store.get(f'{uid}_hist') or []
            h.append(msg[:20])
            store.set(f'{uid}_hist', h)

    # 使用 stream_with_context 保持上下文
    # 添加 headers 禁用缓冲，确保真正的流式传输
    return Response(
        stream_with_context(generate()),
        mimetype='text/plain; charset=utf-8',
        headers={
            'X-Accel-Buffering': 'no',      # 禁用 nginx 缓冲
            'Cache-Control': 'no-cache',    # 禁用浏览器缓存
            'Connection': 'keep-alive'       # 保持连接
        }
    )

if __name__ == "__main__":
    print("\n" + "="*50)
    print("AI 私厨已启动（流式版本）")
    print("地址: http://127.0.0.1:5000")
    print("="*50)
    app.run(host='127.0.0.1', port=5000, threaded=True)