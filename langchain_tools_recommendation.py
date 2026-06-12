"""
LangChain 常用工具推荐大全

LangChain 提供了丰富的预定义工具和工具包 (Toolkit)
这个文档整理了最常用和最有价值的工具
"""

import sys
import io
from pathlib import Path

# 设置 UTF-8 编码
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except:
    pass

print("\n" + "=" * 70)
print("🛠️ LangChain 常用工具推荐大全")
print("=" * 70)

# ============================================
# 工具分类
# ============================================

print("""
LangChain 工具分为两大类:

1. 单个工具 (Tool) - 单一功能
2. 工具包 (Toolkit) - 一组相关工具的集合

按功能分类:

┌─────────────────────────────────────────────────────────────────┐
│  🔍 搜索类        │  Wikipedia, DuckDuckGo, Tavily, Arxiv       │
│  📊 数据类        │  SQL Database, Yahoo Finance, Polygon      │
│  🛠️ 开发类        │  Python REPL, Shell, File Management       │
│  🌐 API类         │  Requests, GitHub, Jira, Slack             │
│  📝 文档类        │  PDF, CSV, JSON, Markdown                  │
│  🔬 研究类        │  Arxiv, PubMed, Wolfram Alpha             │
│  🗣️ 多模态类      │  Image, Audio, Video, Speech              │
└─────────────────────────────────────────────────────────────────┘
""")

# ============================================
# 🔍 搜索类工具 (推荐度最高)
# ============================================

print("\n" + "-" * 70)
print("🔍 搜索类工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  Tavily Search       │  AI专用搜索引擎     │   ⭐⭐⭐⭐⭐ 最佳   │
│  DuckDuckGo Search   │  免费搜索引擎       │   ⭐⭐⭐⭐ 推荐     │
│  Wikipedia           │  Wikipedia百科      │   ⭐⭐⭐⭐ 推荐     │
│  Arxiv               │  学术论文搜索       │   ⭐⭐⭐⭐ 推荐     │
│  Google Search       │  Google搜索         │   ⭐⭐⭐⭐ 推荐     │
│  Bing Search         │  Bing搜索           │   ⭐⭐⭐ 一般       │
│  Serper              │  Google API搜索     │   ⭐⭐⭐⭐ 推荐     │
│  You.com             │  AI搜索引擎         │   ⭐⭐⭐⭐ 推荐     │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. Tavily Search ⭐⭐⭐⭐⭐ 最佳选择

   ✅ 专为 AI/RAG 设计
   ✅ 返回结构化 JSON
   ✅ 原始网页内容
   ✅ 域名过滤
   ✅ 新闻/金融搜索

   from langchain_tavily import TavilySearch

   tavily = TavilySearch(max_results=5)
   agent = create_agent(model=model, tools=[tavily])

   💰 需要 API Key (有免费额度)
""")

print("""
📌 2. DuckDuckGo Search ⭐⭐⭐⭐ 免费选择

   ✅ 完全免费
   ✅ 无需 API Key
   ✅ 开箱即用

   from langchain_community.tools import DuckDuckGoSearchRun

   search = DuckDuckGoSearchRun()
   agent = create_agent(model=model, tools=[search])

   💰 免费
""")

print("""
📌 3. Wikipedia ⭐⭐⭐⭐ 知识查询

   ✅ 查询 Wikipedia 百科
   ✅ 结构化信息
   ✅ 适合知识问答

   from langchain_community.tools import WikipediaQueryRun
   from langchain_community.utilities import WikipediaAPIWrapper

   wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
   agent = create_agent(model=model, tools=[wikipedia])

   💰 免费
""")

print("""
📌 4. Arxiv ⭐⭐⭐⭐ 学术论文

   ✅ 搜索学术论文
   ✅ 获取论文摘要
   ✅ 适合研究型 Agent

   from langchain_community.tools import ArxivQueryRun

   arxiv = ArxivQueryRun()
   agent = create_agent(model=model, tools=[arxiv])

   💰 免费
""")

# ============================================
# 📊 数据类工具
# ============================================

print("\n" + "-" * 70)
print("📊 数据类工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  SQL Database        │  数据库查询         │   ⭐⭐⭐⭐⭐ 最佳   │
│  Yahoo Finance       │  金融数据           │   ⭐⭐⭐⭐ 推荐     │
│  Polygon             │  股票数据           │   ⭐⭐⭐⭐ 推荐     │
│  Golden              │  公司数据           │   ⭐⭐⭐ 一般       │
│  OpenWeatherMap      │  天气数据           │   ⭐⭐⭐⭐ 推荐     │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. SQL Database Toolkit ⭐⭐⭐⭐⭐ 数据库交互

   ✅ 自动生成 SQL 查询
   ✅ 查询数据库表结构
   ✅ 执行 SQL 语句
   ✅ 数据分析

   from langchain_community.agent_toolkits import SQLDatabaseToolkit
   from langchain_community.utilities import SQLDatabase

   db = SQLDatabase.from_uri("sqlite:///Chinook.db")
   toolkit = SQLDatabaseToolkit(db=db, llm=model)
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   # Agent 可以:
   # - 列出数据库表
   # - 查看表结构
   # - 执行 SQL 查询
   # - 分析数据

   💰 免费 (本地数据库)
""")

print("""
📌 2. Yahoo Finance News ⭐⭐⭐⭐ 金融新闻

   ✅ 获取金融新闻
   ✅ 市场信息

   from langchain_community.tools import YahooFinanceNewsTool

   finance_news = YahooFinanceNewsTool()
   agent = create_agent(model=model, tools=[finance_news])

   💰 免费
""")

print("""
📌 3. OpenWeatherMap ⭐⭐⭐⭐ 专业天气

   ✅ 专业天气 API
   ✅ 更详细的数据
   ✅ 比 wttr.in 更专业

   from langchain_community.utilities import OpenWeatherMapAPIWrapper
   from langchain_community.tools import OpenWeatherMapQueryRun

   weather = OpenWeatherMapQueryRun(
       api_wrapper=OpenWeatherMapAPIWrapper(openweathermap_api_key="your-key")
   )

   💰 需要 API Key (有免费额度)
""")

# ============================================
# 🛠️ 开发类工具
# ============================================

print("\n" + "-" * 70)
print("🛠️ 开发类工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  Python REPL         │  执行 Python代码    │   ⭐⭐⭐⭐⭐ 最佳   │
│  Shell Tool          │  执行 Shell命令     │   ⭐⭐⭐⭐ 推荐     │
│  File Management     │  文件操作           │   ⭐⭐⭐⭐ 推荐     │
│  Terminal            │  终端交互           │   ⭐⭐⭐ 一般       │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. Python REPL ⭐⭐⭐⭐⭐ 代码执行

   ✅ 执行 Python 代码
   ✅ 数学计算
   ✅ 数据处理
   ✅ 适合编程 Agent

   from langchain_experimental.tools import PythonAstREPLTool

   python_repl = PythonAstREPLTool()
   agent = create_agent(model=model, tools=[python_repl])

   # Agent 可以:
   # - 执行 Python 代码
   # - 数学计算: "计算 123 * 456"
   # - 数据处理: "分析这个 CSV 文件"
   # - 绘图: "生成一个图表"

   ⚠️ 安全警告: 使用时需要限制权限

   💰 免费
""")

print("""
📌 2. Shell Tool ⭐⭐⭐⭐ Shell 命令

   ✅ 执行 Shell 命令
   ✅ 系统操作

   from langchain_community.tools import ShellTool

   shell = ShellTool()
   agent = create_agent(model=model, tools=[shell])

   ⚠️ 安全警告: 仅在安全环境中使用

   💰 免费
""")

print("""
📌 3. File Management Toolkit ⭐⭐⭐⭐ 文件操作

   ✅ 读取文件
   ✅ 写入文件
   ✅ 列出目录
   ✅ 搜索文件

   from langchain_community.agent_toolkits import FileManagementToolkit

   toolkit = FileManagementToolkit(
       root_dir="./workspace",
       selected_tools=["read_file", "write_file", "list_directory"]
   )
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   # Agent 可以:
   # - 读取文件内容
   # - 写入新文件
   # - 列出目录内容

   💰 免费
""")

# ============================================
# 🌐 API类工具
# ============================================

print("\n" + "-" * 70)
print("🌐 API 和集成工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  Requests            │  HTTP请求           │   ⭐⭐⭐⭐ 推荐     │
│  GitHub              │  GitHub操作         │   ⭐⭐⭐⭐ 推荐     │
│  Jira                │  项目管理           │   ⭐⭐⭐⭐ 推荐     │
│  Slack               │  Slack消息          │   ⭐⭐⭐⭐ 推荐     │
│  Gmail               │  Gmail邮件          │   ⭐⭐⭐⭐ 推荐     │
│  Zapier              │  自动化集成         │   ⭐⭐⭐⭐⭐ 最佳   │
│  Teams               │  Microsoft Teams   │   ⭐⭐⭐ 一般       │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. GitHub Toolkit ⭐⭐⭐⭐ GitHub 操作

   ✅ 创建 Issue
   ✅ 创建 Pull Request
   ✅ 搜索代码
   ✅ 评论 Issue

   from langchain_community.agent_toolkits import GitHubToolkit

   toolkit = GitHubToolkit(github_token="your-token")
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   # Agent 可以:
   # - 创建 GitHub Issue
   # - 创建 Pull Request
   # - 搜索代码库
   # - 评论 Issue/PR

   💰 需要 GitHub Token
""")

print("""
📌 2. Jira Toolkit ⭐⭐⭐⭐ 项目管理

   ✅ 创建 Jira Issue
   ✅ 搜索 Issue
   ✅ 更新 Issue

   from langchain_community.agent_toolkits import JiraToolkit

   toolkit = JiraToolkit(jira_api_token="your-token")
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   💰 需要 Jira API Token
""")

print("""
📌 3. Slack Toolkit ⭐⭐⭐⭐ 消息发送

   ✅ 发送 Slack 消息
   ✅ 读取消息

   from langchain_community.agent_toolkits import SlackToolkit

   toolkit = SlackToolkit(slack_token="your-token")
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   💰 需要 Slack Token
""")

print("""
📌 4. Gmail Toolkit ⭐⭐⭐⭐ 邮件操作

   ✅ 发送邮件
   ✅ 读取邮件
   ✅ 搜索邮件

   from langchain_community.agent_toolkits import GmailToolkit

   toolkit = GmailToolkit()
   tools = toolkit.get_tools()

   agent = create_agent(model=model, tools=tools)

   💰 需要 Google OAuth
""")

print("""
📌 5. Zapier Natural Language Actions ⭐⭐⭐⭐⭐ 最佳集成

   ✅ 自然语言控制 5000+ 应用
   ✅ 自动化工作流
   ✅ 最强大的集成工具

   from langchain_community.tools import ZapierNLATool

   zapier = ZapierNLATool(zapier_nla_api_key="your-key")

   # Agent 可以:
   # - "发送 Slack 消息"
   # - "创建 Google Calendar 事件"
   # - "添加 Trello 卡片"
   # - "发送 Gmail 邮件"
   # - 5000+ 其他应用!

   💰 需要 Zapier API Key (付费)
""")

# ============================================
# 🔬 研究类工具
# ============================================

print("\n" + "-" * 70)
print("🔬 研究类工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  Arxiv               │  学术论文           │   ⭐⭐⭐⭐ 推荐     │
│  PubMed              │  医学文献           │   ⭐⭐⭐⭐ 推荐     │
│  Wolfram Alpha       │  数学计算           │   ⭐⭐⭐⭐⭐ 最佳   │
│  Human               │  人工反馈           │   ⭐⭐⭐⭐ 推荐     │
│  SceneXplain         │  图像理解           │   ⭐⭐⭐⭐ 推荐     │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. Arxiv ⭐⭐⭐⭐ 学术论文

   ✅ 搜索学术论文
   ✅ 获取论文摘要和链接

   from langchain_community.tools import ArxivQueryRun

   arxiv = ArxivQueryRun()
   agent = create_agent(model=model, tools=[arxiv])

   # Agent 可以:
   # - "搜索关于机器学习的最新论文"
   # - "找 Claude 相关的论文"

   💰 免费
""")

print("""
📌 2. PubMed ⭐⭐⭐⭐ 医学文献

   ✅ 搜索医学文献
   ✅ 适合医疗/健康 Agent

   from langchain_community.tools import PubMedQueryRun

   pubmed = PubMedQueryRun()
   agent = create_agent(model=model, tools=[pubmed])

   💰 免费
""")

print("""
📌 3. Wolfram Alpha ⭐⭐⭐⭐⭐ 数学计算

   ✅ 专业数学计算
   ✅ 科学计算
   ✅ 比 Python REPL 更专业

   from langchain_community.utilities import WolframAlphaAPIWrapper
   from langchain_community.tools import WolframAlphaQueryRun

   wolfram = WolframAlphaQueryRun(
       api_wrapper=WolframAlphaAPIWrapper()
   )

   agent = create_agent(model=model, tools=[wolfram])

   # Agent 可以:
   # - "计算复杂积分"
   # - "解方程 x^2 + 5x + 6 = 0"
   # - "化学方程式计算"

   💰 需要 API Key (有免费额度)
""")

# ============================================
# 📝 文档类工具
# ============================================

print("\n" + "-" * 70)
print("📝 文档处理工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  PDF                 │  PDF读取            │   ⭐⭐⭐⭐ 推荐     │
│  CSV                 │  CSV处理            │   ⭐⭐⭐⭐ 推荐     │
│  JSON                │  JSON处理           │   ⭐⭐⭐⭐ 推荐     │
│  Markdown            │  Markdown处理       │   ⭐⭐⭐⭐ 推荐     │
│  Docx                │  Word文档           │   ⭐⭐⭐⭐ 推荐     │
│  Pandas DataFrame    │  数据分析           │   ⭐⭐⭐⭐⭐ 最佳   │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. Pandas DataFrame Toolkit ⭐⭐⭐⭐⭐ 数据分析

   ✅ 分析 Pandas DataFrame
   ✅ 数据可视化
   ✅ 统计分析

   from langchain_experimental.tools import PandasDataFrameTool

   import pandas as pd
   df = pd.read_csv("data.csv")

   pandas_tool = PandasDataFrameTool(df=df)
   agent = create_agent(model=model, tools=[pandas_tool])

   # Agent 可以:
   # - "分析这个数据的统计信息"
   # - "找出异常值"
   # - "绘制分布图"

   💰 免费
""")

# ============================================
# 🗣️ 多模态工具
# ============================================

print("\n" + "-" * 70)
print("🗣️ 多模态工具")
print("-" * 70)

print("""
┌──────────────────────┬─────────────────────┬─────────────────────┐
│      工具名称        │      功能           │     推荐度          │
├──────────────────────┼─────────────────────┼─────────────────────┤
│  SceneXplain         │  图像理解           │   ⭐⭐⭐⭐ 推荐     │
│  Azure Speech        │  语音识别           │   ⭐⭐⭐⭐ 推荐     │
│  ElevenLabs          │  文字转语音         │   ⭐⭐⭐⭐ 推荐     │
│  DALL-E              │  图像生成           │   ⭐⭐⭐⭐⭐ 最佳   │
│  Stable Diffusion    │  图像生成           │   ⭐⭐⭐⭐ 推荐     │
└──────────────────────┴─────────────────────┴─────────────────────┘
""")

print("""
📌 1. SceneXplain ⭐⭐⭐⭐ 图像理解

   ✅ 分析图像内容
   ✅ 生成图像描述

   from langchain_community.tools import SceneXplainTool

   scene_tool = SceneXplainTool()
   agent = create_agent(model=model, tools=[scene_tool])

   💰 需要 API Key
""")

print("""
📌 2. DALL-E ⭐⭐⭐⭐⭐ 图像生成

   ✅ 生成高质量图像
   ✅ 文字转图像

   # 通过 OpenAI API

   💰 需要 OpenAI API Key
""")

# ============================================
# 📊 推荐度排序
# ============================================

print("\n" + "-" * 70)
print("📊 工具推荐度排序 (Top 15)")
print("-" * 70)

print("""
⭐⭐⭐⭐⭐ 最强烈推荐 (必备):

   1. Tavily Search     - AI专用搜索 (RAG最佳)
   2. SQL Database      - 数据库交互
   3. Python REPL       - 代码执行
   4. Wolfram Alpha     - 数学计算
   5. Zapier NLA        - 自动化集成 (5000+应用)
   6. Pandas DataFrame  - 数据分析

⭐⭐⭐⭐ 强烈推荐:

   7. DuckDuckGo       - 免费搜索
   8. Wikipedia        - 知识查询
   9. Arxiv            - 学术论文
   10. GitHub          - 代码管理
   11. File Management - 文件操作
   12. Yahoo Finance   - 金融数据
   13. Jira            - 项目管理
   14. Slack           - 消息发送
   15. Gmail           - 邮件操作
""")

# ============================================
# 按应用场景推荐
# ============================================

print("\n" + "-" * 70)
print("🎯 按应用场景推荐")
print("-" * 70)

print("""
📌 场景1: AI Research Agent (研究型 Agent)

   推荐:
   - Tavily Search ⭐⭐⭐⭐⭐
   - Arxiv ⭐⭐⭐⭐
   - Wikipedia ⭐⭐⭐⭐
   - Wolfram Alpha ⭐⭐⭐⭐⭐

   from langchain_tavily import TavilySearch
   from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun

   tools = [
       TavilySearch(max_results=5),
       ArxivQueryRun(),
       WikipediaQueryRun()
   ]

   agent = create_agent(
       model=model,
       tools=tools,
       system_prompt="你是一个研究助手,可以搜索学术论文和百科"
   )
""")

print("""
📌 场景2: Data Analysis Agent (数据分析)

   推荐:
   - SQL Database ⭐⭐⭐⭐⭐
   - Pandas DataFrame ⭐⭐⭐⭐⭐
   - Python REPL ⭐⭐⭐⭐⭐

   from langchain_community.agent_toolkits import SQLDatabaseToolkit
   from langchain_experimental.tools import PandasDataFrameTool, PythonAstREPLTool

   db_toolkit = SQLDatabaseToolkit(db=db, llm=model)
   tools = db_toolkit.get_tools() + [PandasDataFrameTool(df=df)]

   agent = create_agent(
       model=model,
       tools=tools,
       system_prompt="你是一个数据分析专家"
   )
""")

print("""
📌 场景3: Coding Agent (编程 Agent)

   推荐:
   - GitHub ⭐⭐⭐⭐
   - Python REPL ⭐⭐⭐⭐⭐
   - File Management ⭐⭐⭐⭐

   from langchain_community.agent_toolkits import GitHubToolkit
   from langchain_community.agent_toolkits import FileManagementToolkit

   github_toolkit = GitHubToolkit(github_token="xxx")
   file_toolkit = FileManagementToolkit(root_dir="./")

   tools = github_toolkit.get_tools() + file_toolkit.get_tools()

   agent = create_agent(
       model=model,
       tools=tools,
       system_prompt="你是一个编程助手"
   )
""")

print("""
📌 场景4: Business Automation Agent (自动化)

   推荐:
   - Zapier NLA ⭐⭐⭐⭐⭐
   - Slack ⭐⭐⭐⭐
   - Gmail ⭐⭐⭐⭐
   - Jira ⭐⭐⭐⭐

   from langchain_community.tools import ZapierNLATool

   zapier = ZapierNLATool(zapier_nla_api_key="xxx")

   agent = create_agent(
       model=model,
       tools=[zapier],
       system_prompt="你是一个自动化助手"
   )

   # Agent 可以:
   # - "发送 Slack 消息给团队"
   # - "创建 Jira ticket"
   # - "发送邮件给客户"
   # - "添加日历事件"
""")

print("""
📌 场景5: Knowledge Q&A Agent (知识问答)

   推荐:
   - Wikipedia ⭐⭐⭐⭐
   - DuckDuckGo ⭐⭐⭐⭐
   - Tavily ⭐⭐⭐⭐⭐

   from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
   from langchain_tavily import TavilySearch

   tools = [
       WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
       DuckDuckGoSearchRun(),
       TavilySearch(max_results=5)
   ]

   agent = create_agent(
       model=model,
       tools=tools,
       system_prompt="你是一个知识问答助手"
   )
""")

print("""
📌 场景6: Weather Agent (天气查询) - 当前项目

   推荐:
   - OpenWeatherMap ⭐⭐⭐⭐ (专业)
   - wttr.in 自定义工具 ⭐⭐⭐⭐ (免费)

   方案A: 使用 OpenWeatherMap (专业)

   from langchain_community.tools import OpenWeatherMapQueryRun

   weather = OpenWeatherMapQueryRun(
       api_wrapper=OpenWeatherMapAPIWrapper(openweathermap_api_key="xxx")
   )

   方案B: 使用自定义 @tool (当前项目)

   @tool
   def get_real_weather(city: str) -> str:
       return requests.get(f"https://wttr.in/{city}").text

   💰 方案A 需要 API Key
   💰 方案B 免费
""")

# ============================================
# 安装指南
# ============================================

print("\n" + "-" * 70)
print("📦 安装指南")
print("-" * 70)

print("""
核心工具 (langchain-community):

    pip install langchain-community
    或
    uv add langchain-community

高级工具 (langchain-experimental):

    pip install langchain-experimental
    或
    uv add langchain-experimental

Tavily 搜索:

    pip install langchain-tavily
    或
    uv add langchain-tavily

特定集成:

    pip install langchain-github    # GitHub
    pip install langchain-slack     # Slack
    pip install langchain-jira      # Jira
    pip install langchain-zapier    # Zapier

一次性安装所有常用工具:

    pip install langchain langchain-community langchain-experimental langchain-tavily
    或
    uv add langchain langchain-community langchain-experimental langchain-tavily
""")

# ============================================
# 总结
# ============================================

print("\n" + "=" * 70)
print("✅ 总结")
print("=" * 70)

print("""
🎯 最推荐工具 Top 6:

   1. Tavily Search ⭐⭐⭐⭐⭐
      - AI专用搜索
      - RAG最佳选择

   2. SQL Database Toolkit ⭐⭐⭐⭐⭐
      - 数据库交互
      - 数据分析必备

   3. Python REPL ⭐⭐⭐⭐⭐
      - 代码执行
      - 计算能力

   4. Wolfram Alpha ⭐⭐⭐⭐⭐
      - 专业数学
      - 科学计算

   5. Zapier NLA ⭐⭐⭐⭐⭐
      - 自动化集成
      - 5000+ 应用

   6. Pandas DataFrame ⭐⭐⭐⭐⭐
      - 数据分析
      - 可视化

💡 选择建议:

   - 搜索需求       → Tavily (AI) 或 DuckDuckGo (免费)
   - 数据分析       → SQL Database + Pandas + Python REPL
   - 研究需求       → Arxiv + Wikipedia + Wolfram Alpha
   - 自动化需求     → Zapier NLA (最强)
   - 编程需求       → GitHub + File Management + Python REPL
   - 项目管理       → Jira + Slack + Gmail
   - 天气查询       → OpenWeatherMap 或自定义 @tool

📚 完整工具列表:
   https://python.langchain.com/docs/integrations/tools/
""")

print("\n" + "=" * 70)