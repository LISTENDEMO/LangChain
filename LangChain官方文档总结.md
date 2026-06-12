# LangChain 官方文档学习总结

> 基于 https://docs.langchain.com/oss/python/langchain/overview 的核心内容整理

---

## 📚 目录

1. [LangChain 核心架构](#1-langchain-核心架构)
2. [七大组件系统](#2-七大组件系统)
3. [LangChain 表达式语言 (LCEL)](#3-langchain-表达式语言-lcel)
4. [Agent 智能体系统](#4-agent-智能体系统)
5. [Memory 记忆系统](#5-memory-记忆系统)
6. [RAG 检索增强生成](#6-rag-检索增强生成)
7. [Tools 工具系统](#7-tools-工具系统)
8. [快速入门示例](#8-快速入门示例)
9. [最佳实践总结](#9-最佳实践总结)

---

## 1. LangChain 核心架构

### 架构层次

LangChain 采用分层架构设计，从数据处理到最终输出：

```
┌─────────────────────────────────────────────┐
│          LangChain 应用架构                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  第5层: Orchestration (编排协调)     │   │
│  │  - Agents (智能体)                  │   │
│  │  - Memory (记忆系统)                │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  第4层: Generation (生成输出)        │   │
│  │  - Models (模型推理)                │   │
│  │  - Tools (工具调用)                 │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  第3层: Retrieval (信息检索)         │   │
│  │  - Retrievers (检索器)              │   │
│  │  - Vector Stores (向量存储)         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  第2层: Embedding & Storage          │   │
│  │  - 嵌入向量                         │   │
│  │  - 文档存储                         │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  第1层: Input Processing             │   │
│  │  - 文档加载                         │   │
│  │  - 文本分割                         │   │
│  └─────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│        LCEL 表达式语言 (统一接口)            │
└─────────────────────────────────────────────┘
```

### 核心设计理念

| 设计原则 | 说明 |
|----------|------|
| **模块化** | 每个组件独立，可灵活组合 |
| **统一接口** | 所有组件实现 Runnable 接口 |
| **声明式** | 使用 LCEL 管道操作符组合组件 |
| **可扩展** | 支持自定义组件和集成 |

---

## 2. 七大组件系统

LangChain 将组件分为七个主要类别：

### 组件分类表

| 类别 | 组件 | 功能 | 示例 |
|------|------|------|------|
| **Models** | Chat Models, LLMs, Embeddings | AI推理和生成 | ChatOpenAI, Anthropic |
| **Tools** | API工具, 数据库, 搜索 | 外部能力扩展 | 搜索、计算、数据库 |
| **Agents** | ReAct, Tool Calling | 编排和推理 | create_agent() |
| **Memory** | Message History, Store | 上下文保持 | InMemoryStore |
| **Retrievers** | Vector, Web, Hybrid | 信息检索 | vector_store.as_retriever() |
| **Document Processing** | Loaders, Splitters | 数据处理 | PDF加载器, 文本分割 |
| **Vector Stores** | Chroma, Pinecone, FAISS | 语义搜索 | 向量数据库 |

### 组件连接流程

```
输入数据
    ↓
文档加载器 (Loaders)
    ↓
文本分割器 (Splitters)
    ↓
嵌入模型 (Embeddings)
    ↓
向量存储 (Vector Stores)
    ↓
检索器 (Retrievers)
    ↓
模型 + 工具 (Models + Tools)
    ↓
智能体编排 (Agents)
    ↓
记忆系统 (Memory)
    ↓
最终输出
```

---

## 3. LangChain 表达式语言 (LCEL)

### 什么是 LCEL?

LCEL (LangChain Expression Language) 是 LangChain 的声明式语言，用于组合各种组件。

### 管道操作符 `|`

使用 `|` 符号连接组件，形成处理链：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 创建链
chain = prompt | model | parser

# 执行链
result = chain.invoke({"input": "你好"})
```

### LCEL 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| **统一接口** | 所有组件都支持 invoke, stream, batch | `chain.invoke()` |
| **流式输出** | 支持实时流式响应 | `for chunk in chain.stream()` |
| **异步支持** | 支持异步调用 | `await chain.ainvoke()` |
| **批量处理** | 批量调用多个输入 | `chain.batch([input1, input2])` |
| **自动追踪** | LangSmith 自动追踪 | 内置支持 |

### Runnable 接口方法

```python
# 所有 Runnable 组件支持以下方法:

# 1. 同步调用
result = component.invoke(input)

# 2. 异步调用
result = await component.ainvoke(input)

# 3. 流式输出
for chunk in component.stream(input):
    print(chunk)

# 4. 批量调用
results = component.batch([input1, input2, input3])

# 5. 异步流式
async for chunk in component.astream(input):
    print(chunk)
```

### RunnableParallel 并行执行

```python
from langchain_core.runnables import RunnableParallel

# 并行执行多个任务
chain = RunnableParallel({
    "joke": joke_prompt | model,
    "story": story_prompt | model,
})

# 返回多个结果
result = chain.invoke({"topic": "AI"})
# {"joke": "...", "story": "..."}
```

### RunnablePassthrough 数据传递

```python
from langchain_core.runnables import RunnablePassthrough

# 保留原始输入
chain = RunnableParallel({
    "original": RunnablePassthrough(),
    "processed": prompt | model,
})
```

### RunnableLambda 自定义函数

```python
from langchain_core.runnables import RunnableLambda

# 添加自定义处理逻辑
def format_output(output):
    return f"【回答】{output}"

chain = prompt | model | parser | RunnableLambda(format_output)
```

---

## 4. Agent 智能体系统

### Agent 定义

Agent 是能够自主决策、选择工具、执行任务的智能系统。

### 最简单的 Agent 创建

```python
from langchain.agents import create_agent

# 创建基础 Agent
agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[tool1, tool2],
    system_prompt="你是一个有帮助的助手"
)

# 执行
result = agent.invoke({
    "messages": [{"role": "user", "content": "查询北京天气"}]
})
```

### Agent 工作流程

```
用户输入
    ↓
Agent 分析意图
    ↓
决策: 需要调用工具吗?
    ↓ 是                    ↓ 否
选择合适的工具              直接生成回复
    ↓
执行工具
    ↓
观察结果
    ↓
继续决策或结束
    ↓
生成最终回复
```

### Agent 类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **ReAct Agent** | 推理+行动循环 | 复杂多步骤任务 |
| **Tool Calling Agent** | 直接调用工具 | 工具明确的任务 |
| **Structured Chat Agent** | 多工具对话 | 多工具协调 |

### Agent 配置选项

```python
agent = create_agent(
    model="openai:gpt-4o",           # 模型选择
    tools=[get_weather, search],     # 工具列表
    system_prompt="...",             # 系统提示
    context_schema=Context,          # 上下文结构
    store=InMemoryStore(),           # 存储系统
)
```

---

## 5. Memory 记忆系统

### Memory 分类

| 类型 | 说明 | 实现方式 |
|------|------|----------|
| **短期记忆** | 单次对话历史 | InMemoryChatMessageHistory |
| **长期记忆** | 跨会话持久化 | InMemoryStore, PostgresStore |
| **语义记忆** | 知识和事实 | 向量存储检索 |

### 短期记忆实现

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

# 创建对话历史
history = InMemoryChatMessageHistory()

# 添加消息
history.add_user_message("你好!")
history.add_ai_message("你好!有什么可以帮你的?")

# 查看历史
messages = history.messages
```

### 长期记忆实现

```python
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool, ToolRuntime

# 创建存储 (生产环境使用数据库)
store = InMemoryStore()

# 定义保存工具
@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime) -> str:
    """保存用户信息"""
    user_id = runtime.context.user_id
    store.put(("users",), user_id, dict(user_info))
    return "信息已保存"

# 定义读取工具
@tool
def get_user_info(runtime: ToolRuntime) -> str:
    """获取用户信息"""
    user_id = runtime.context.user_id
    info = store.get(("users",), user_id)
    return str(info.value) if info else "未找到"

# Agent 使用存储
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[save_user_info, get_user_info],
    store=store,
    context_schema=Context,
)
```

### 语义记忆检索

```python
# 使用语义相似度搜索记忆
async def search_memory(state: State, *, store: BaseStore):
    results = await store.asearch(
        namespace=("memory", "facts"),
        query="用户偏好",
        limit=3
    )
    return results
```

---

## 6. RAG 检索增强生成

### RAG 流程

```
用户问题
    ↓
向量化查询
    ↓
向量相似度检索
    ↓
获取相关文档
    ↓
组合上下文 + 问题
    ↓
LLM 生成回答
```

### 基础 RAG 实现

```python
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

# 1. 创建向量存储
embeddings = OpenAIEmbeddings()
vector_store = InMemoryVectorStore(embeddings)

# 2. 添加文档
vector_store.add_documents(documents)

# 3. 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 4. 构建 RAG 链
rag_chain = (
    RunnableParallel({
        "context": retriever,
        "question": RunnablePassthrough()
    })
    | ChatPromptTemplate.from_template(
        "基于上下文回答问题:\n{context}\n问题: {question}"
    )
    | model
    | StrOutputParser()
)

# 5. 执行
answer = rag_chain.invoke("什么是 LangChain?")
```

### 文档处理流程

```python
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档
loader = WebBaseLoader("https://example.com/article")
docs = loader.load()

# 2. 分割文档
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 每块大小
    chunk_overlap=200,    # 重叠部分
)

chunks = splitter.split_documents(docs)

# 3. 向量化并存储
vector_store.add_documents(chunks)
```

### RAG Agent

```python
from langchain.tools import tool

# 定义检索工具
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """检索相关文档"""
    docs = vector_store.similarity_search(query, k=3)
    context = "\n\n".join(
        f"来源: {doc.metadata['source']}\n内容: {doc.page_content}"
        for doc in docs
    )
    return context, docs

# 创建 RAG Agent
agent = create_agent(
    model="gpt-4o-mini",
    tools=[retrieve],
    system_prompt="""你有检索工具可以获取文档。
    使用工具帮助回答问题。
    如果检索结果不相关，请说明不知道。"""
)
```

---

## 7. Tools 工具系统

### 工具定义

使用 `@tool` 装饰器定义工具：

```python
from langchain.tools import tool

# 简单工具
@tool
def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 带参数工具
@tool
def search(query: str, max_results: int) -> str:
    """搜索信息"""
    return f"搜索 '{query}' 的结果..."

# 带返回内容的工具
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """检索文档"""
    docs = vector_store.similarity_search(query)
    return "检索结果...", docs
```

### TypeScript 工具定义

```typescript
import { tool } from "langchain";
import { z } from "zod";

const searchTool = tool(
    async ({ query, maxResults }) => {
        return `搜索结果...`;
    },
    {
        name: "search",
        description: "搜索信息",
        schema: z.object({
            query: z.string(),
            maxResults: z.number()
        })
    }
);
```

### 工具最佳实践

| 要点 | 说明 |
|------|------|
| **清晰的 docstring** | Agent 通过 docstring 理解工具用途 |
| **明确的参数类型** | 使用 TypedDict 或 Pydantic 定义结构 |
| **返回简洁信息** | 避免返回过多数据影响 Agent |
| **错误处理** | 添加 try-except 防止工具失败 |

---

## 8. 快速入门示例

### 示例 1: Hello World Agent

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

### 示例 2: 简单 Agent

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather, search],
    system_prompt="你是一个有帮助的助手"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "北京天气怎么样?"}]
})
```

### 示例 3: 天气查询 Agent

```python
from langchain.tools import tool
import requests

@tool
def get_weather(city: str) -> str:
    """获取天气信息"""
    url = f"https://wttr.in/{city}?format=v2"
    return requests.get(url).text

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    system_prompt="你是天气助手"
)

# Agent 会自动调用 get_weather 工具
```

### 示例 4: 带记忆的 Agent

```python
from dataclasses import dataclass
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

store = InMemoryStore()

@tool
def save_user_info(info: dict, runtime: ToolRuntime) -> str:
    """保存用户信息"""
    store.put(("users",), runtime.context.user_id, info)
    return "已保存"

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[save_user_info],
    store=store,
    context_schema=Context
)

# 执行并传入上下文
agent.invoke(
    {"messages": [{"role": "user", "content": "我叫张三"}]},
    context=Context(user_id="user_123")
)
```

---

## 9. 最佳实践总结

### ✅ 推荐做法

#### 1. 使用 LCEL 组合组件

```python
# ✅ 推荐: 使用管道操作符
chain = prompt | model | parser

# ❌ 避免: 传统链式调用
chain = LLMChain(llm=model, prompt=prompt)
```

#### 2. 清晰的工具定义

```python
# ✅ 好的工具定义
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。

    Args:
        city: 城市名称，如"北京"

    Returns:
        天气信息字符串
    """
    return weather_data.get(city)

# ❌ 避免模糊的描述
@tool
def get_weather(x) -> str:
    """获取天气"""  # Agent 无法理解
    return data
```

#### 3. 流式输出提升体验

```python
# ✅ 流式输出 (更好的用户体验)
for chunk in agent.stream(input):
    print(chunk, end="", flush=True)
```

#### 4. 结构化输出

```python
# ✅ 使用 Pydantic 定义输出结构
from pydantic import BaseModel

class Answer(BaseModel):
    content: str
    confidence: float

parser = PydanticOutputParser(pydantic_object=Answer)
chain = prompt | model | parser
```

#### 5. 错误处理

```python
# ✅ 完善的错误处理
@tool
def safe_tool(params):
    try:
        result = process(params)
        return result
    except Exception as e:
        return f"错误: {str(e)}"
```

### ❌ 避免的做法

| 避免 | 原因 |
|------|------|
| 硬编码提示词 | 无法复用，难以维护 |
| 忽略工具描述 | Agent 无法正确使用工具 |
| 不使用 LCEL | 代码复杂，缺少统一接口 |
| 过大的历史记录 | 超出模型上下文限制 |
| 无错误处理 | 工具失败影响整个系统 |

---

## 📊 学习路径建议

### 第1阶段: 基础概念 (1周)

- ✅ 理解 LangChain 架构
- ✅ 学习 LCEL 表达式语言
- ✅ 掌握 Models 和 Prompts
- ✅ 实现简单 Chain

### 第2阶段: 核心组件 (2周)

- ✅ Output Parsers 和结构化输出
- ✅ Memory 系统
- ✅ 自定义 Tools
- ✅ 流式输出和异步

### 第3阶段: 进阶应用 (3周)

- ✅ Agent 系统
- ✅ RAG 实现
- ✅ 多工具协调
- ✅ 生产部署

### 第4阶段: 实战项目 (持续)

- ✅ 完整项目开发
- ✅ 性能优化
- ✅ 监控和调试 (LangSmith)
- ✅ 持续迭代

---

## 🔗 相关资源

- 📖 **官方文档**: https://docs.langchain.com
- 🔧 **GitHub**: https://github.com/langchain-ai/langchain
- 📚 **LangSmith**: https://smith.langchain.com (监控平台)
- 🌐 **LangGraph**: https://langchain-ai.github.io/langgraph/ (Agent 框架)
- 💬 **社区**: LangChain Discord

---

## 🎯 核心要点回顾

### 1. LangChain 的本质

LangChain 是一个**组件化框架**，用于构建 LLM 应用：

- 模块化组件
- 统一接口 (Runnable)
- 声明式组合 (LCEL)
- 可扩展集成

### 2. 关键概念速记

| 概念 | 一句话说明 |
|------|-----------|
| **LCEL** | 管道操作符组合组件 |
| **Agent** | 自主决策调用工具的智能体 |
| **Memory** | 对话历史和长期记忆 |
| **RAG** | 检索+生成结合增强回答 |
| **Tool** | Agent 可调用的外部能力 |
| **Runnable** | 所有组件的统一接口 |

### 3. 最简代码模板

```python
# 1. 定义工具
@tool
def my_tool(input: str) -> str:
    """工具描述"""
    return result

# 2. 创建 Agent
agent = create_agent(
    model="gpt-4o-mini",
    tools=[my_tool],
    system_prompt="..."
)

# 3. 执行
result = agent.invoke({"messages": [{"role": "user", "content": question}]})
```

---

**总结完成！建议结合之前的 `LangChain全面学习指南.md` 和天气 Agent 实践继续深入学习。**