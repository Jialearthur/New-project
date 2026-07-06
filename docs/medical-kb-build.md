# 医疗知识库离线建库说明

本项目提供了一个离线建库脚本，用于批量扫描医疗文档目录，并直接写入当前系统使用的 SQLite 元数据和 LangChain FAISS 索引。

脚本位置：

- [backend/scripts/build_medical_kb.py](/C:/Users/lionlimark/Documents/New%20project/backend/scripts/build_medical_kb.py)

## 适用场景

- 你已经准备好一批医疗文档，希望一次性导入
- 你不想每次都通过前端手动上传
- 你希望答辩时展示“离线建库 + 在线问答”的完整流程

## 支持的文档格式

- `.md`
- `.txt`
- `.docx`
- `.pdf`
- `.html`

## 最常用命令

在 `backend` 目录执行：

```powershell
python .\scripts\build_medical_kb.py --source ..\sample_docs --clear
```

含义：

- `--source`：指定待导入的医疗文档目录
- `--clear`：导入前先清空现有文档和 chunks，再重建索引

如果你想直接导入更完整的分类资料目录，推荐使用：

```powershell
python .\scripts\build_medical_kb.py --source ..\medical_docs --clear --kb-name "综合医疗知识库"
```

## 自定义知识库名称

```powershell
python .\scripts\build_medical_kb.py --source ..\my_medical_docs --clear --kb-name "门诊医疗知识库"
```

## 构建完成后发生了什么

脚本会自动完成：

1. 扫描目录下所有支持格式的文件
2. 解析正文
3. 按标题和段落切块
4. 将文档和 chunk 写入 SQLite
5. 调用 LangChain FAISS 重建索引

最终结果会写入：

- `data/app.db`
- `data/index/langchain_faiss/`

## 与前端上传的关系

这个脚本和前端上传建库使用的是同一套后端解析/切块/索引逻辑，因此二者兼容：

- 你可以先离线批量建库
- 也可以后续继续通过前端补充上传单个文档

## 推荐目录结构

项目中已经补好了一套更适合答辩演示的分类资料目录：

- `medical_docs/慢病管理/`
- `medical_docs/门诊分诊/`
- `medical_docs/用药安全/`
- `medical_docs/护理流程/`
- `medical_docs/感染管理/`

你可以直接把自己的文档按这个结构继续往里补。

## 注意事项

- 若本机没有本地缓存的 `BAAI/bge-small-zh-v1.5`，系统会退回到内置哈希向量方案
- 若目录里有扫描版 PDF 或乱码文档，检索效果会明显下降
- 离线建库完成后，重新启动后端即可直接使用新的知识库
