# 企业级多智能体客服系统

基于多智能体协作架构的企业级智能客服平台，支持自动问答、工单处理、多轮对话和知识库检索增强生成（RAG）。

## 功能特性

- 🤖 **多智能体协作**：多个专业 Agent（问答、工单、质检等）协同工作
- 🔍 **RAG 增强检索**：结合向量数据库和重排序模型，提升回答准确性
- 💬 **多轮对话**：支持上下文记忆（Zep / 文件存储）
- 📊 **可视化分析**：前端管理面板，实时查看客服数据
- ⚙️ **模块化设计**：易于扩展和定制

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| 前端框架 | Vue 3 + Vite + TailwindCSS |
| AI 模型 | DeepSeek Chat / Zhipu Embedding |
| 向量数据库 | ChromaDB |
| 缓存 / 会话 | Redis |
| 记忆存储 | Zep / 文件存储 |
| 容器化 | Docker + Docker Compose |

## 快速开始

### 1. 克隆代码

```bash
git clone git@github.com:AAADD-Ops/ai-agent.git
cd ai-agent
```

### 2. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 3. 配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填入以下必要配置：

```env
# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 智谱 Embedding API（必需）
ZHIPU_API_KEY=sk-your-zhipu-key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
EMBEDDING_MODEL=embedding-3

# Redis 连接（可选）
REDIS_URL=redis://redis:6379/0
```

### 4. 启动服务

你的redis地址/redis-server.exe

cd D:\企业级多智能体客服系统\backend
python -c "import asyncio; from app.mcp.server import main; asyncio.run(main())"

cd D:\企业级多智能体客服系统\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd D:\企业级多智能体客服系统\frontend
npm run dev

### 5. 访问服务

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 前端页面 | http://localhost:5173 |

## 项目结构

```
├── backend/                # 后端服务
│   ├── app/
│   │   ├── agents/         # 多智能体实现
│   │   ├── api/            # API 路由
│   │   ├── rag/            # RAG 检索增强模块
│   │   ├── memory/         # 对话记忆
│   │   └── models/         # 数据模型
│   ├── data/               # 数据目录（向量库、法律文本等）
│   └── requirements.txt
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── views/          # 页面视图
│   │   └── stores/         # Pinia 状态管理
│   └── package.json
├── docker/                 # Docker 配置文件
├── docker-compose.yml      # 容器编排
└── .env.example            # 环境变量模板
```

## 许可证

MIT
