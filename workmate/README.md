# WorkMate API

一个用于练习 **FastAPI + LLM 应用开发** 的学习项目。以「任务管理 + 知识库问答」为场景，逐步练习了 SQLite 存储、RAG 检索、多轮对话、Agent 工具调用等常见后端能力。

> ⚠️ 本项目是个人学习练习，**不适合直接用于生产环境**。详见文末「限制」。

## 功能

| 能力 | 说明 | 主要端点 |
| --- | --- | --- |
| 任务管理 | 任务的增删改查，支持按状态筛选 | `POST/GET/PATCH/DELETE /tasks` |
| 知识库问答（RAG） | 检索 `knowledge.txt` 中最相关的片段，交给 LLM 生成回答并标注来源 | `POST /ask` |
| 多轮对话 | 按 `conversation_id` 保存历史，携带上下文继续对话 | `POST /chat` |
| Agent 工具调用 | 模型自主决定调用工具（查未完成任务 / 查知识库） | `POST /agent/chat` |
| 健康检查 | 进程存活探测 | `GET /health` |

### 主要端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 返回 `{"status":"ok"}` |
| `POST` | `/tasks` | 创建任务（`title`/`description`/`status`） |
| `GET` | `/tasks` | 列出任务，可用 `?status=todo/in_progress/done` 筛选 |
| `GET` | `/tasks/{id}` | 查询单个任务，不存在返回 404 |
| `PATCH` | `/tasks/{id}` | 部分更新任务，空更新 400，`null` 字段 422 |
| `DELETE` | `/tasks/{id}` | 删除任务，成功 204 |
| `POST` | `/ask` | 知识库问答，返回 `{answer, sources}` |
| `POST` | `/chat` | 多轮对话，返回 `{conversation_id, answer}` |
| `POST` | `/agent/chat` | Agent 问答，最多 3 轮工具调用 |

## 目录结构

```
workmate/
├── main.py               # FastAPI 应用与路由
├── schemas.py            # Pydantic 请求/响应模型
├── store.py              # SQLite 数据访问层（tasks / messages）
├── llm_practice.py       # DeepSeek 聊天模型封装
├── rag_practice.py       # 向量检索 + 知识库问答（依赖智谱 embedding）
├── document_practice.py  # 文档读取、切分、哈希
├── tool_practice.py      # Agent 工具定义与执行循环
├── chat_service.py       # 多轮对话组装
├── sqlite_practice.py    # SQLite 基础练习脚本（非运行时依赖）
├── knowledge.txt         # 知识库原始文档（虚构的 StudyMate 使用说明）
├── requirements.txt      # 依赖清单
├── .env.example          # 环境变量模板（无真实密钥）
└── tests/                # pytest 测试
```

## 运行方式

### 1. 准备环境

```bash
# 建议使用 Python 3.10+
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置密钥

本项目依赖两个外部模型服务，需先在本地配置 API Key：

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

然后编辑 `.env`，填入你自己的密钥：

```ini
DEEPSEEK_API_KEY=你的 DeepSeek 密钥
ZHIPU_API_KEY=你的智谱 embedding 密钥
```

| 变量 | 用途 | 服务 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 聊天 / 生成回答 | https://api.deepseek.com |
| `ZHIPU_API_KEY` | 生成文本向量（embedding） | https://open.bigmodel.cn |

> 注意：`.env` 含真实密钥，已被 `.gitignore` 忽略，**切勿提交**。

### 3. 启动服务

```bash
uvicorn main:app --reload
```

- 交互式 API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

首次启动时，`lifespan` 会加载 `knowledge.txt` 并构建向量库，缓存写入 `knowledge_vectors.json`（该文件会被 git 忽略）。

## 运行测试

```bash
pytest
```

## 限制

- **无鉴权 / 无多用户**：所有端点开放访问，没有登录、权限或租户隔离。
- **本地 SQLite**：单机文件存储（`practice.db`），不适合并发写入或分布式部署。
- **依赖外部付费 API**：问答、对话、检索都需联网并消耗第三方额度，网络异常会返回 502/504。
- **阻塞式调用**：模型调用使用同步 `httpx`，由 FastAPI 线程池承载，高并发下吞吐有限。
- **知识库静态**：只读取单个 `knowledge.txt`，变更文档后需重启（或触发重建）才生效。
- **Agent 简单**：仅两个工具、最多 3 轮，无记忆、无流式输出。
- **接口简化**：任务无分页，无速率限制，无统一的异常/日志体系。

## 测试现状

当前共有 4 个测试文件，覆盖情况如下：

| 文件 | 覆盖内容 | 是否依赖真实 API |
| --- | --- | --- |
| `tests/test_basic.py` | 演示 `pytest` 基本断言 | 否 |
| `tests/test_health.py` | `GET /health` 返回 200 | 否（`TestClient` 触发 lifespan，需先构建知识库） |
| `tests/test_tasks.py` | 任务 CRUD 全流程，含 400/422/404 边界与空更新校验 | 否（用 `tmp_path` + `monkeypatch` 隔离临时数据库） |
| `tests/test_messages.py` | 多轮对话历史保存 | **是**（会真实调用 DeepSeek，需有效 Key，且断言含中文标点差异风险） |

**尚未覆盖**：`/ask` 与 `/agent/chat` 端点、向量检索与相似度阈值、502/504 等模型服务异常分支、`/chat` 端点本身。

> 说明：`tests/test_messages.py` 不是纯单元测试——它发起真实模型请求，依赖网络和密钥，建议后续用 mock 替换 `ask_messages`。
