"""
Tavily Search - AI 专用搜索引擎工具

对比:
- DuckDuckGo Search (预定义工具)
- Tavily Search (AI 专用搜索引擎)
- 自定义搜索工具 (@tool)

Tavily 优势:
- 专为 AI 和 RAG 应用设计
- 返回结构化搜索结果
- 支持多种搜索深度
- 可获取原始网页内容
- 支持域名过滤
- 比普通搜索引擎更适合 AI Agent
"""

import sys
import io
import os
from pathlib import Path

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except:
    pass

# 加载环境变量
ENV_PATH = r"C:\Users\92099\.claude\.env"
if Path(ENV_PATH).exists():
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

print("\n" + "=" * 70)
print("🔍 Tavily Search - AI 专用搜索引擎")
print("=" * 70)

# ============================================
# Tavily Search 简介
# ============================================

print("""
📌 什么是 Tavily?

   Tavily 是专为 AI 应用和 RAG (检索增强生成) 设计的搜索引擎 API

   ✅ 核心特点:
   - 专为 AI Agent 优化的搜索结果
   - 返回结构化 JSON 数据 (而非原始 HTML)
   - 支持多种搜索深度 (basic/advanced)
   - 可获取原始网页内容 (markdown/text)
   - 支持域名过滤 (只搜索特定网站)
   - 支持新闻/金融/通用搜索
   - 自动清理和优化搜索结果
""")

# ============================================
# LangChain 预定义搜索工具对比
# ============================================

print("\n" + "-" * 70)
print("📊 LangChain 搜索工具对比")
print("-" * 70)

print("""
┌────────────────────┬─────────────────────┬─────────────────────┐
│      工具          │   DuckDuckGo        │      Tavily         │
├────────────────────┼─────────────────────┼─────────────────────┤
│ 目标用户           │   通用用户          │     AI/RAG 应用     │
│ 返回格式           │   文本摘要          │    结构化 JSON      │
│ 搜索深度           │   固定              │    basic/advanced   │
│ 原始内容           │   ❌ 不支持         │    ✅ markdown/text │
│ 域名过滤           │   ❌ 不支持         │    ✅ includeDomains│
│ 新闻搜索           │   ❌ 不支持         │    ✅ topic="news"  │
│ RAG 优化           │   ❌ 不优化         │    ✅ 专为 RAG 设计 │
│ API Key            │   ❌ 免费           │    ✅ 需要付费      │
│ 搜索质量           │   ⭐⭐ 一般         │    ⭐⭐⭐⭐ 高      │
│ AI 适用性          │   ⭐⭐ 基础         │    ⭐⭐⭐⭐⭐ 最佳  │
└────────────────────┴─────────────────────┴─────────────────────┘
""")

# ============================================
# Tavily Search 使用方式
# ============================================

print("\n" + "-" * 70)
print("🔧 LangChain 集成 Tavily Search")
print("-" * 70)

print("""
📝 方式1: 直接使用 Tavily API

    from tavily import TavilyClient

    # 初始化客户端
    client = TavilyClient(api_key="tvly-YOUR_API_KEY")

    # 基础搜索
    response = client.search("Who is Leo Messi?")
    print(response)

    # 高级搜索 (获取原始内容)
    response = client.search(
        query="your research query",
        search_depth="advanced",  # basic 或 advanced
        include_raw_content=True,  # 获取原始网页
        max_results=5
    )

    # RAG 优化搜索 (返回适合 LLM 的字符串)
    context = client.get_search_context(
        query="What happened during the Burning Man floods?"
    )
    # context 是一个字符串,可直接输入 LLM
""")

print("""
📝 方式2: LangChain 预定义工具 (Python)

    from langchain_tavily import TavilySearch
    from langchain.agents import create_agent

    # 创建 Tavily 搜索工具
    tavily_search = TavilySearch(
        max_results=5,
        topic="general",  # general, news, finance
        include_raw_content=False,
        include_domains=[]  # 可选: 只搜索特定域名
    )

    # 在 Agent 中使用
    agent = create_agent(
        model=model,
        tools=[tavily_search]
    )

    # 调用 Agent
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Euro 2024 在哪个国家举办?"}]
    })
""")

print("""
📝 方式3: LangChain 预定义工具 (JavaScript)

    import { TavilySearch } from "@langchain/tavily";
    import { createAgent } from "langchain";

    // 创建 Tavily 搜索工具
    const tavilySearchTool = new TavilySearch({
        maxResults: 5,
        topic: "general",
    });

    const agent = createAgent({
        model: llm,
        tools: [tavilySearchTool],
    });

    // 动态设置搜索参数
    const userInput = "What nation hosted Euro 2024? Include only wikipedia sources.";

    // Agent 会自动设置 includeDomains=['wikipedia.org']
    const events = await agent.stream(
        { messages: [["human", userInput]] },
        { streamMode: "values" },
    );
""")

# ============================================
# Tavily Search 返回结构
# ============================================

print("\n" + "-" * 70)
print("📋 Tavily Search 返回结构")
print("-" * 70)

print("""
Tavily 搜索返回结构化的 JSON 数据:

    {
        "query": "Who is Leo Messi?",
        "follow_up_questions": [
            "What are the latest updates on Messi's career?",
            "How many goals has Messi scored in his career?"
        ],
        "answer": "Lionel Messi is an Argentine professional footballer...",
        "images": [
            {
                "url": "https://example.com/messi.jpg",
                "description": "Lionel Messi celebrating"
            }
        ],
        "results": [
            {
                "title": "Lionel Messi - Wikipedia",
                "url": "https://en.wikipedia.org/wiki/Lionel_Messi",
                "content": "Lionel Andrés Messi is an Argentine...",
                "score": 0.95,  # 相关性评分
                "raw_content": null  # 原始网页内容 (可选)
            },
            {
                "title": "Messi Stats",
                "url": "https://example.com/stats",
                "content": "Messi has scored 800+ goals...",
                "score": 0.88,
                "raw_content": "# Messi Career Stats\\n\\n..."
            }
        ]
    }

✅ 关键字段:
   - query: 搜索查询
   - answer: AI 生成的摘要答案
   - results: 搜索结果列表 (结构化!)
   - score: 相关性评分 (0-1)
   - raw_content: 原始网页内容 (可选)
   - images: 相关图片 (可选)
   - follow_up_questions: 建议的后续问题
""")

# ============================================
# Tavily Search 参数详解
# ============================================

print("\n" + "-" * 70)
print("⚙️ Tavily Search 参数详解")
print("-" * 70)

print("""
核心参数:

┌────────────────────┬─────────────────────────────────────────────┐
│      参数          │                说明                          │
├────────────────────┼─────────────────────────────────────────────┤
│ query              │ 搜索查询字符串                               │
│ search_depth       │ "basic" 或 "advanced"                        │
│                    │  - basic: 快速搜索,返回摘要                  │
│                    │  - advanced: 深度搜索,获取原始内容           │
│ max_results        │ 返回结果数量 (默认 5)                        │
│ include_domains    │ 只搜索特定域名 ["wikipedia.org"]             │
│ exclude_domains    │ 排除特定域名 ["example.com"]                 │
│ include_raw_content│ 是否获取原始网页内容                         │
│                    │  - False: 不获取                             │
│                    │  - True/markdown/text: 获取并格式化          │
│ topic              │ 搜索主题                                     │
│                    │  - "general": 通用搜索                       │
│                    │  - "news": 新闻搜索                          │
│                    │  - "finance": 金融搜索                       │
│ time_range         │ 时间范围 (用于新闻搜索)                      │
│                    │  - "day", "week", "month", "year"           │
└────────────────────┴─────────────────────────────────────────────┘
""")

# ============================================
# 实际应用示例
# ============================================

print("\n" + "-" * 70)
print("💡 实际应用示例")
print("-" * 70)

print("""
📌 场景1: 基础 AI 搜索

    from langchain_tavily import TavilySearch

    tavily = TavilySearch(max_results=5, topic="general")

    # Agent 自动决定何时搜索
    agent = create_agent(model=model, tools=[tavily])

    # 用户提问,Agent 自动搜索
    result = agent.invoke({
        "messages": [{"role": "user", "content": "2024年奥运会在哪里举办?"}]
    })
""")

print("""
📌 场景2: RAG 应用 (获取网页内容)

    from tavily import TavilyClient

    client = TavilyClient(api_key="tvly-xxx")

    # 获取适合 RAG 的上下文字符串
    context = client.get_search_context(
        query="What happened during the Burning Man floods?",
        search_depth="advanced"
    )

    # context 是一个字符串,可直接输入 LLM
    prompt = f"Based on this context: {context}, answer the question..."

    # 或使用 include_raw_content 获取原始网页
    response = client.search(
        query="LangChain tutorial",
        include_raw_content="markdown"  # 获取 markdown 格式
    )

    for result in response['results']:
        print(result['raw_content'])  # 原始网页内容
""")

print("""
📌 场景3: 域名过滤搜索 (只搜索 Wikipedia)

    from langchain_tavily import TavilySearch

    tavily = TavilySearch(
        max_results=5,
        include_domains=["wikipedia.org"]  # 只搜索 Wikipedia
    )

    # 用户请求 "只从 Wikipedia 搜索"
    # Agent 会自动应用域名过滤
    agent = create_agent(model=model, tools=[tavily])
""")

print("""
📌 场景4: 新闻搜索

    from langchain_tavily import TavilySearch

    tavily = TavilySearch(
        max_results=10,
        topic="news",  # 新闻搜索
        time_range="day"  # 最近一天的新闻
    )

    agent = create_agent(model=model, tools=[tavily])

    # 搜索最新新闻
    result = agent.invoke({
        "messages": [{"role": "user", "content": "今天的科技新闻"}]
    })
""")

print("""
📌 场景5: 金融搜索

    from langchain_tavily import TavilySearch

    tavily = TavilySearch(
        topic="finance"  # 金融搜索
    )

    # 搜索金融信息
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Apple 最新股价"}]
    })
""")

# ============================================
# 与 DuckDuckGo 的关键区别
# ============================================

print("\n" + "-" * 70)
print("🔥 Tavily vs DuckDuckGo 关键区别")
print("-" * 70)

print("""
┌────────────────────────────────────────────────────────────────────┐
│                    DuckDuckGo Search                               │
├────────────────────────────────────────────────────────────────────┤
│ ✅ 优点:                                                            │
│    - 免费使用,无需 API Key                                          │
│    - 开箱即用,配置简单                                              │
│    - 适合基础搜索需求                                               │
│                                                                    │
│ ❌ 缺点:                                                            │
│    - 返回文本摘要,不是结构化数据                                    │
│    - 不支持搜索深度控制                                             │
│    - 不支持域名过滤                                                 │
│    - 不支持新闻/金融搜索                                            │
│    - 不适合 RAG 应用                                                │
│    - 搜索质量一般                                                   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                        Tavily Search                               │
├────────────────────────────────────────────────────────────────────┤
│ ✅ 优点:                                                            │
│    - 专为 AI/RAG 应用设计                                           │
│    - 返回结构化 JSON 数据                                           │
│    - 支持搜索深度控制 (basic/advanced)                              │
│    - 可获取原始网页内容 (markdown/text)                             │
│    - 支持域名过滤                                                   │
│    - 支持新闻/金融搜索                                              │
│    - 自动生成摘要答案                                               │
│    - 相关性评分 (score: 0-1)                                        │
│    - AI 自动优化搜索结果                                            │
│    - 提供 RAG 优化函数                                              │
│    - 搜索质量高                                                     │
│                                                                    │
│ ❌ 缺点:                                                            │
│    - 需要 API Key (付费服务)                                        │
│    - 每月有限额使用                                                 │
│    - 需要安装 langchain-tavily 包                                  │
└────────────────────────────────────────────────────────────────────┘
""")

# ============================================
# 选择建议
# ============================================

print("\n" + "-" * 70)
print("🎯 选择建议")
print("-" * 70)

print("""
根据需求选择:

┌─────────────────────────────────────────────────────────────────┐
│  ✅ 使用 DuckDuckGo Search:                                      │
│     - 免费搜索需求                                                │
│     - 基础信息查询                                                │
│     - 不需要结构化数据                                            │
│     - 不需要域名过滤                                              │
│     - 快速原型开发                                                │
│                                                                  │
│  ✅ 使用 Tavily Search ⭐⭐⭐⭐⭐ 推荐:                           │
│     - AI Agent 应用                                               │
│     - RAG 应用                                                    │
│     - 需要结构化数据                                              │
│     - 需要原始网页内容                                            │
│     - 需要域名过滤                                                │
│     - 新闻/金融搜索                                               │
│     - 高质量搜索结果                                              │
│     - 生产环境使用                                                │
│                                                                  │
│  ✅ 使用自定义搜索工具:                                           │
│     - 特定 API 搜索                                               │
│     - 企业内部搜索                                                │
│     - 特殊搜索需求                                                │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================
# 安装和配置
# ============================================

print("\n" + "-" * 70)
print("📦 安装和配置")
print("-" * 70)

print("""
安装 Tavily:

    # Python
    pip install langchain-tavily
    或
    uv add langchain-tavily

    # JavaScript
    npm install @langchain/tavily
    或
    yarn add @langchain/tavily

配置 API Key:

    1. 注册 Tavily: https://tavily.com
    2. 获取 API Key
    3. 设置环境变量:

       # .env 文件
       TAVILY_API_KEY=tvly-your-api-key

    4. 或直接传入:

       tavily = TavilySearch(
           tavily_api_key="tvly-xxx"
       )

免费额度:
   - 注册后获得免费额度
   - 每月可搜索一定次数
   - 适合测试和小型项目
""")

# ============================================
# 完整示例代码
# ============================================

print("\n" + "-" * 70)
print("📝 完整示例代码")
print("-" * 70)

print("""
# Python 示例

from langchain_tavily import TavilySearch
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

# 1. 创建模型
model = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key="your-api-key"
)

# 2. 创建 Tavily 搜索工具
tavily_search = TavilySearch(
    max_results=5,
    topic="general",
    include_raw_content=False
)

# 3. 创建 Agent
agent = create_agent(
    model=model,
    tools=[tavily_search],
    system_prompt="你是一个智能助手,可以搜索互联网回答问题"
)

# 4. 调用 Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "2024年诺贝尔物理学奖获得者是谁?"}]
})

print(result["messages"][-1].content)
""")

# ============================================
# 总结
# ============================================

print("\n" + "=" * 70)
print("✅ 总结")
print("=" * 70)

print("""
🎯 Tavily Search 核心优势:

1. 专为 AI/RAG 设计:
   - 返回结构化数据,不是原始文本
   - 自动生成摘要答案
   - 适合 Agent 和 RAG 应用

2. 高级搜索功能:
   - 搜索深度控制 (basic/advanced)
   - 原始网页内容获取
   - 域名过滤
   - 新闻/金融搜索

3. AI 优化:
   - 相关性评分 (score: 0-1)
   - 自动清理和优化结果
   - RAG 专用函数

4. LangChain 无缝集成:
   - 作为预定义工具使用
   - 与 DuckDuckGo 同样简单
   - 但功能强大得多

💡 建议:

   - AI Agent 应用    → 用 Tavily ⭐⭐⭐⭐⭐
   - RAG 应用         → 用 Tavily ⭐⭐⭐⭐⭐
   - 基础免费搜索     → 用 DuckDuckGo
   - 特殊搜索需求     → 自定义工具

📚 更多信息:
   - Tavily 官网: https://tavily.com
   - LangChain 文档: https://docs.langchain.com/tools/tavily_search
""")

print("\n" + "=" * 70)