# WorkMate 商家运营助手

一个面向商家运营人员的 AI 应用练习项目，整合了 FastAPI、RAG、Agent、MCP、异步调用和自动化测试。

项目帮助运营人员完成两类任务：

- **规则问答**：依据商家规则知识库回答退货、发货、库存与客服答复边界等问题，并展示来源。
- **运营分析**：由 Agent 判断是否需要调用 MCP 商家数据工具，查询库存或商品经营指标后生成运营建议。

> 本项目使用虚构商家规则和模拟商品数据，仅用于学习与作品展示，不代表真实平台政策、经营建议或法律意见。

## 核心能力

| 能力            | 说明                                                             |
| --------------- | ---------------------------------------------------------------- |
| FastAPI API     | 提供 RAG、Agent、任务管理、多轮对话与健康检查接口                |
| RAG 知识库问答  | 文档切分、Embedding、余弦相似度检索、Top-K 与阈值过滤、来源返回  |
| 幻觉控制        | 无相关知识片段时明确拒答，不要求模型根据常识编造规则             |
| Agent 工具调用  | 模型根据问题决定调用任务、知识库、低库存或商品指标工具           |
| MCP 集成        | 商家工具通过 stdio MCP Server 暴露，由异步 MCP Client 适配层调用 |
| Pydantic Schema | 用 `ProductMetrics` 明确 MCP 商品指标工具的结构化输出契约        |
| 异步链路        | `/agent/chat` → `run_agent()` → `execute_tool()` → MCP Client    |
| 原生前端        | 两个 Tab、独立聊天记录、加载状态、错误提示、RAG 来源展示         |
| 自动化测试      | RAG、业务工具、Agent 工具、MCP 适配层、FastAPI 异步路由等测试    |

## 产品边界

```text
规则问答
  使用者：客服 / 商家运营人员
  目标：辅助核对规则并回复买家
  数据范围：商家规则知识库
  接口：POST /ask

运营分析
  使用者：商家运营人员
  目标：查询内部经营数据并辅助补货决策
  数据范围：库存、浏览、订单、支付订单、营收、转化率
  接口：POST /agent/chat
```

当前前端以功能分区区分外部答复辅助与内部经营数据。生产环境还应补充登录、角色权限和数据隔离，避免内部指标暴露给未授权用户。

## 架构

```text
浏览器页面
  ├─ 规则问答
  │    ↓ POST /ask
  │    ↓ RAG：Embedding → 检索 → LLM
  │    ↓ 回答 + 来源
  │
  └─ 运营分析
       ↓ POST /agent/chat
       ↓ async run_agent()
       ↓ Agent 决定工具与参数
       ↓ async execute_tool()
       ↓ mcp_tool_client.py
       ↓ stdio
       ↓ mcp_server.py
       ↓ business_tools.py
       ↓ mock_products.json
       ↓ MCP 结构化结果
       ↓ LLM 生成运营建议
```

商家工具采用分层设计：

```text
business_tools.py
  真实业务逻辑：低库存筛选、商品指标计算
       ↑
mcp_server.py
  MCP Server：暴露 get_low_stock_items、get_product_metrics
       ↑
mcp_tool_client.py
  MCP Client Adapter：连接、调用、统一成功/失败结果
       ↑
tool_practice.py
  Agent：工具选择、参数校验、消息循环
```

## 功能与接口

| 方法                    | 路径                 | 说明                                     |
| ----------------------- | -------------------- | ---------------------------------------- |
| `GET`                   | `/`                  | API 元信息                               |
| `GET`                   | `/health`            | 健康检查                                 |
| `POST`                  | `/ask`               | RAG 规则问答，返回 `answer` 与 `sources` |
| `POST`                  | `/agent/chat`        | Agent 运营分析，最多三轮工具调用         |
| `POST`                  | `/chat`              | 按 `conversation_id` 保存的多轮对话      |
| `POST/GET/PATCH/DELETE` | `/tasks`             | SQLite 任务管理                          |
| `GET`                   | `/static/index.html` | WorkMate 前端页面                        |

## 目录结构

```text
workmate/
├── app/api/                   # 健康检查、任务、元信息路由
├── data/mock_products.json    # 模拟商家商品数据
├── docs/evaluation_cases.md   # AI 效果评估记录
├── static/
│   ├── index.html             # 页面结构
│   ├── styles.css             # 页面样式
│   └── app.js                 # Tab、聊天记录、API 调用
├── tests/                     # pytest 测试
├── main.py                    # FastAPI 入口、lifespan、接口
├── schemas.py                 # Pydantic 请求/响应模型
├── store.py                   # SQLite 数据访问
├── rag_practice.py            # RAG 检索与知识库问答
├── document_practice.py       # 文档读取、切分与哈希
├── business_tools.py          # 商品低库存与经营指标业务逻辑
├── mcp_server.py              # MCP 商家工具 Server
├── mcp_tool_client.py         # 异步 MCP Client 适配层
├── tool_practice.py           # Agent 工具 Schema、校验与调用循环
├── knowledge.txt              # 虚构商家规则知识库
├── requirements.txt           # 依赖清单
└── .env.example               # 环境变量模板
```

## 运行方式

### 1. 安装依赖

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

若尚未创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. 配置 API Key

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```ini
DEEPSEEK_API_KEY=你的 DeepSeek API Key
ZHIPU_API_KEY=你的智谱 Embedding API Key
```

| 环境变量           | 用途                             |
| ------------------ | -------------------------------- |
| `DEEPSEEK_API_KEY` | RAG 回答、Agent 推理与最终回答   |
| `ZHIPU_API_KEY`    | 知识库文档与用户问题的 Embedding |

> `.env` 含真实密钥，已被 `.gitignore` 忽略，禁止提交到 Git 仓库。

### 3. 启动服务

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

访问：

- API 文档：http://127.0.0.1:8000/docs
- 前端页面：http://127.0.0.1:8000/static/index.html
- 健康检查：http://127.0.0.1:8000/health

首次启动或 `knowledge.txt` 内容变更后，应用会根据文档哈希重新构建向量缓存。缓存文件不会提交到 Git。

## 使用示例

### 规则问答

```text
商品支持七天无理由退货吗？
```

预期：基于规则知识库回答七天无理由退货条件，并显示来源。

### 运营分析

```text
SKU-1001 的经营情况怎么样，是否需要补货？
```

预期：Agent 调用 MCP 商品指标工具，根据真实库存、浏览、订单和转化率生成建议。

### 低库存查询

```text
哪些商品库存不足，需要优先补货？
```

预期：Agent 调用 MCP 低库存工具，返回低库存商品并建议补货优先级。

## 测试

运行完整测试集：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

测试覆盖：

| 测试方向         | 示例                             |
| ---------------- | -------------------------------- |
| FastAPI 基础路由 | 元信息、健康检查、任务接口       |
| RAG 检索         | 无关片段过滤、阈值与 Top-K 行为  |
| 业务工具         | 低库存排序、未知 SKU             |
| Agent 工具层     | 白名单、参数校验、MCP 工具委托   |
| MCP 适配层       | 成功结果、业务错误、结构化输出   |
| 异步 API 路由    | `/agent/chat` 正确等待异步 Agent |

AI 效果评估记录见：[docs/evaluation_cases.md](docs/evaluation_cases.md)。

## 技术取舍

- **RAG 使用文件缓存向量**：项目规模小，便于理解文档哈希、切分策略和向量缓存；生产环境可替换为向量数据库。
- **商家工具使用 MCP**：业务逻辑与 Agent 框架解耦，未来可被其他 MCP Client 复用。
- **Agent 与 MCP 分层**：Agent 决定调用什么工具；MCP Client 负责通信；MCP Server 负责暴露工具；业务层负责真实数据查询。
- **保留 Agent 层参数校验**：在启动 MCP Server 前拒绝明显非法参数，同时由 MCP Server 再次校验，形成双层保护。
- **Pydantic 输出 Schema**：避免客户端猜测文本格式，确保商品指标以结构化数据返回。
- **前端使用原生 HTML/CSS/JS**：在一周项目范围内优先交付可用产品，而非引入额外框架复杂度。

## 已知限制与后续优化

- 无登录、角色权限或租户隔离；
- 商家数据为本地模拟 JSON，非真实数据库；
- MCP Client 当前每次工具调用都会建立本地 stdio 连接，可优化为单次 Agent 请求复用连接；
- 模型请求仍通过 `asyncio.to_thread()` 桥接同步 HTTP 调用，可进一步改为 `httpx.AsyncClient`；
- 前端仅保留显示层多轮记录，不会自动把历史消息发送给 RAG 或 Agent；
- RAG 仅加载单个本地知识文档，生产环境应支持多文档上传、权限过滤和向量数据库；
- 缺少统一日志、链路追踪、限流、鉴权、流式响应与生产级部署配置。

## 总结

> 我完成了一个面向商家运营人员的 AI 助手。规则问答模块通过 RAG 检索商家规则知识库，并在没有依据时拒绝编造；运营分析模块采用 Agent + MCP 架构，模型负责工具选择，MCP Server 暴露库存和商品指标能力，业务逻辑与协议层解耦。项目使用 Pydantic Schema 约束结构化工具输出，并区分可恢复的 ToolError 与通信错误。最终通过单元测试、MCP 集成测试、FastAPI 异步路由测试、前端交互与真实端到端调用完成验证。