# Project A 智能问答系统

面向大学期末课设的轻量版本地 RAG 演示系统。项目聚焦医疗资料问答，保留文档上传、向量检索、答案生成、引用展示、基础登录和问答日志，主动删除生产级复杂度。当前后端 RAG 主链路基于 LangChain 组织。

## 项目结构

```text
backend/   FastAPI 后端，负责认证、文档处理、LangChain 检索、问答和日志
frontend/  React + Vite 前端，包含登录页、问答页和管理页
data/      本地数据目录，保存上传文件、索引和 SQLite 数据库
docs/      系统设计说明与答辩演示资料
```

## 已实现功能

- 预置 `admin/admin123`、`user/user123` 两个演示账号
- 支持上传 `PDF / DOCX / TXT / MD / HTML`
- 自动解析文本、按标题和段落分块、建立向量索引
- 基于 `LangChain + FAISS + Ollama` 的 `Top 5` 医疗证据片段问答
- 返回答案、引用来源、响应时间和问答日志
- 单知识库名称可编辑

## 后端启动

1. 确认使用的是真实 Python 解释器，不要是 `C:\Windows\System32\python` 这种 Windows 占位入口。推荐先检查：

```powershell
where.exe python
where.exe py
```

如果 `py` 可用，优先用它创建虚拟环境：

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 `py` 不可用，就用你真实安装的 `python.exe` 绝对路径执行：

```powershell
& "C:\你的Python路径\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 启动本地 Ollama，并准备模型：

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama serve
```

3. 在 `backend` 目录内启动后端：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

说明：

- 如果本机没有下载 `BAAI/bge-small-zh-v1.5`，系统会直接退回到内置哈希向量方案，仍可用于课程演示；当前实现默认只读取本地缓存，不会在启动时强制联网下载模型。
- 如果未启动 Ollama，系统会返回基于检索结果的摘要性兜底回答，但正式演示建议开启 Ollama。
- LangChain 相关包首次安装会比原先更慢，这是正常现象。
- 后端启动时会尝试根据 SQLite 中已有的 chunks 自动恢复 FAISS 索引，避免重启后必须手动重建。

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

默认访问地址：`http://localhost:5173`

前端默认请求：`http://127.0.0.1:8000`

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

- 先以管理员身份登录，展示知识库名称设置和医疗文档上传
- 再切到问答页，演示 3 到 5 个标准医疗问题
- 最后展示引用来源和后台问答日志，强调“答案可追溯”

配套资料见：

- [系统设计说明](./docs/system-design.md)
- [演示问题模板](./docs/demo-questions.md)
- [演示样例文档](./sample_docs/)
- [分类医疗文档目录](./medical_docs/)
- [离线建库说明](./docs/medical-kb-build.md)
