"""测试 Flask -> LangChain 的延迟"""

import time
import os
import sys
from pathlib import Path

# UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout.reconfigure(encoding='utf-8')

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

from flask import Flask, Response, stream_with_context
from langchain_anthropic import ChatAnthropic

# 创建模型
llm = ChatAnthropic(
    model="qwen3.7-plus",
    anthropic_api_url=os.environ.get("ANTHROPIC_BASE_URL"),
    api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    timeout=30
)

app = Flask(__name__)

@app.route("/test1")
def test1():
    """直接返回字符串"""
    def gen():
        yield "hello"
    return Response(stream_with_context(gen()), mimetype="text/plain")

@app.route("/test2")
def test2():
    """调用 LangChain stream"""
    def gen():
        start = time.time()
        first_chunk_time = None
        for chunk in llm.stream("你好"):
            if first_chunk_time is None:
                first_chunk_time = time.time() - start
                print(f"[Flask内部] 第一字节: {first_chunk_time:.2f}s")
            content = chunk.content
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        yield item.get("text", "")
            elif isinstance(content, str):
                yield content
        total = time.time() - start
        print(f"[Flask内部] 总时间: {total:.2f}s")
    return Response(stream_with_context(gen()), mimetype="text/plain")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("延迟测试服务器")
    print("地址: http://127.0.0.1:5001")
    print("="*50)
    app.run(host="127.0.0.1", port=5001, threaded=True)