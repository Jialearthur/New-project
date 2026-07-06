# Project A 系统设计说明

## 1. 项目定位

Project A 是一个面向大学课程设计的轻量版特定领域智能问答系统。系统围绕医疗资料文档构建本地知识库，使用基于 LangChain 的检索增强生成思路回答问题，并提供引用来源用于回溯。

本项目强调：

- 本地可运行
- 结构完整
- 便于演示
- 复杂度可控

## 2. 总体架构

```text
浏览器前端
   ↓
React + Vite
   ↓ HTTP
FastAPI 后端
   ├─ 登录认证
   ├─ 文档上传与解析
   ├─ 文本分块
   ├─ LangChain 向量检索
   ├─ LangChain RAG 问答
   └─ 日志记录
        ↓
SQLite + 本地文件 + FAISS
        ↓
LangChain + Ollama 本地模型
```

## 3. 模块设计

### 3.1 前端模块

- 登录页：输入账号密码，进入系统
- 问答页：提交单个问题，展示对应单次答案和引用
- 管理页：修改知识库名称、上传文档、重建索引、删除文档、查看问答日志

### 3.2 后端模块

- 认证模块：校验用户名密码，发放会话 token
- 文档模块：保存文件、解析文本、记录文档状态
- 分块模块：按标题和段落切分，控制块长和重叠
- 向量模块：通过 LangChain Embeddings 为文本块生成向量并写入 FAISS
- 问答模块：通过 LangChain Prompt 和 ChatOllama 检索 Top 5 医疗证据片段并生成答案
- 日志模块：记录问题、答案、引用、耗时、用户和时间

## 4. 数据设计

### 4.1 SQLite 表

- `users`：用户信息
- `sessions`：登录会话
- `settings`：单知识库名称
- `documents`：文档元数据与状态
- `chunks`：文档切块内容与来源信息
- `qa_logs`：问答日志

### 4.2 本地文件

- `data/uploads/`：原始上传文件
- `data/index/langchain_faiss/`：LangChain FAISS 索引目录
- `data/app.db`：SQLite 数据库

## 5. 核心流程

### 5.1 文档建库流程

1. 管理员上传文档
2. 后端根据文件类型解析正文
3. 依据标题和段落切分为多个 chunk
4. 生成向量并写入向量索引
5. 保存 chunk 元数据到 SQLite

### 5.2 问答流程

1. 用户输入问题
2. 后端将问题转成向量
3. 从 FAISS 中召回最相关的 Top 5 文本块
4. 拼接 Prompt，请求 Ollama 生成回答
5. 返回答案、引用和耗时
6. 记录日志

## 6. 技术选型原因

- FastAPI：接口开发快，适合课程项目
- LangChain：方便统一组织 Embeddings、Vector Store、Prompt 和 LLM 调用
- SQLite：部署轻量，不依赖独立数据库服务
- FAISS：可本地完成向量检索
- Ollama：便于本地运行开源模型
- React + Vite：前端开发简单，演示效果直观

## 7. 已做的简化

为控制课设体量，以下内容不纳入本期：

- 多知识库隔离
- 多轮对话记忆
- 流式输出
- OCR 与复杂表格抽取
- Docker 与生产部署
- 监控告警
- 高并发与高可用

## 8. 可扩展方向

若后续继续完善，可增加：

- 多知识库与角色权限
- 引用编号插入到答案正文
- 重排序模型优化召回
- OCR 支持扫描 PDF
- Docker 化部署
- Prometheus + Grafana 监控
