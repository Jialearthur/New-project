# Project A 智能问答系统

面向大学期末课设的轻量版本地 RAG 演示系统。项目聚焦企业制度文档问答，保留文档上传、向量检索、答案生成、引用展示、基础登录和问答日志，主动删除生产级复杂度。

## 项目结构

```text
backend/   FastAPI 后端，负责认证、文档处理、索引、问答和日志
frontend/  React + Vite 前端，包含登录页、问答页和管理页
data/      本地数据目录，保存上传文件、索引和 SQLite 数据库
docs/      系统设计说明与答辩演示资料
```

## 已实现功能

- 预置 `admin/admin123`、`user/user123` 两个演示账号
- 支持上传 `PDF / DOCX / TXT / MD / HTML`
- 自动解析文本、按标题和段落分块、建立向量索引
- 通过 `Top 5` 证据片段驱动本地问答
- 返回答案、引用来源、响应时间和问答日志
- 单知识库名称可编辑

## 后端启动

1. 创建 Python 虚拟环境并安装依赖：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. 启动本地 Ollama，并准备模型：

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama serve
```

3. 返回项目根目录，启动后端：

```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

说明：

- 如果本机没有下载 `BAAI/bge-small-zh-v1.5`，系统会退回到内置哈希向量方案，仍可用于课程演示。
- 如果未启动 Ollama，系统会返回基于检索结果的摘要性兜底回答，但正式演示建议开启 Ollama。

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

默认访问地址：`http://localhost:5173`

如果后端端口不是 `8000`，可在前端目录新增 `.env`：

```env
VITE_API_BASE=http://localhost:8000
```

## 默认接口

- `POST /api/login`
- `GET /api/me`
- `GET /api/settings`
- `PUT /api/settings`
- `POST /api/documents/upload`
- `GET /api/documents`
- `POST /api/documents/{id}/reindex`
- `DELETE /api/documents/{id}`
- `POST /api/ask`
- `GET /api/logs`

## 课程答辩建议

- 先以管理员身份登录，展示知识库名称设置和制度文档上传
- 再切到问答页，演示 3 到 5 个标准问题
- 最后展示引用来源和后台问答日志，强调“答案可追溯”

配套资料见：

- [系统设计说明](./docs/system-design.md)
- [演示问题模板](./docs/demo-questions.md)
