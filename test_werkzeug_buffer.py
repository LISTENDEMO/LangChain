"""测试 Werkzeug 缓冲"""

import time
import sys

if hasattr(sys.stdout, 'buffer'):
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, Response, stream_with_context

app = Flask(__name__)

@app.route("/test")
def test():
    """模拟 LangChain stream，每秒返回一个字符"""
    def gen():
        print("[Flask内部] 开始生成")
        start = time.time()
        for i in range(10):
            # 模拟延迟（每次 yield 前等待）
            time.sleep(1)
            char = f"第{i+1}秒\n"
            elapsed = time.time() - start
            print(f"[Flask内部] yield: {elapsed:.2f}s")
            yield char
        print(f"[Flask内部] 结束: {time.time() - start:.2f}s")
    return Response(stream_with_context(gen()), mimetype="text/plain")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Werkzeug 缓冲测试")
    print("地址: http://127.0.0.1:5002")
    print("="*50)
    app.run(host="127.0.0.1", port=5002, threaded=True)