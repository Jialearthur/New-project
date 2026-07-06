from __future__ import annotations

import json
import uuid
from time import perf_counter

from ..config import MIN_RETRIEVAL_SCORE, OLLAMA_BASE_URL, OLLAMA_MODEL, TOP_K
from ..db import connection_scope, utcnow
from .documents import fetch_all_chunks
from .vector_store import VectorStore

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - optional dependency
    ChatPromptTemplate = None
    ChatOllama = None


SYSTEM_PROMPT = (
    "你是一个医疗知识库问答助手。"
    "你只能依据提供的资料回答，不要补充资料外知识。"
    "如果证据不足，必须明确回答：依据现有资料无法给出确切答案。"
    "不要把回答表述为最终诊断或处方结论。"
    "回答保持简洁、准确，适合课程项目演示。"
)


def score_to_relevance(raw_score: float) -> float:
    return 1.0 / (1.0 + max(raw_score, 0.0))


def build_citations(retrieved_docs: list[tuple[object, float]]) -> list[dict]:
    citations = []
    for doc, raw_score in retrieved_docs:
        metadata = getattr(doc, "metadata", {})
        snippet = getattr(doc, "page_content", "")
        citations.append(
            {
                "filename": metadata.get("filename", "未知文档"),
                "pageNo": metadata.get("page_no"),
                "sectionPath": metadata.get("section_path", ""),
                "snippet": snippet[:180] + ("..." if len(snippet) > 180 else ""),
                "score": round(score_to_relevance(raw_score), 4),
            }
        )
    return citations


def build_context(retrieved_docs: list[tuple[object, float]]) -> str:
    evidence_blocks = []
    for index, (doc, _) in enumerate(retrieved_docs, start=1):
        metadata = getattr(doc, "metadata", {})
        label = f"[{index}] {metadata.get('filename', '未知文档')}"
        if metadata.get("page_no"):
            label += f" 第{metadata['page_no']}页"
        if metadata.get("section_path"):
            label += f" / {metadata['section_path']}"
        evidence_blocks.append(f"{label}\n{getattr(doc, 'page_content', '')}")
    return "\n\n".join(evidence_blocks)


def fallback_answer(retrieved_docs: list[tuple[object, float]]) -> str:
    if not retrieved_docs:
        return "依据现有资料无法给出确切答案。"
    best_doc, _ = retrieved_docs[0]
    best = getattr(best_doc, "page_content", "")[:220]
    return f"未连接到本地 LangChain/Ollama 模型，以下为最相关资料摘要：{best}"


def generate_answer(question: str, context_text: str) -> str:
    if ChatPromptTemplate is None or ChatOllama is None:
        raise RuntimeError("LangChain Ollama 组件未安装")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "问题：{question}\n\n"
                "资料：\n{context}\n\n"
                "请仅依据资料回答；如果资料不足，明确拒答。",
            ),
        ]
    )
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    message = prompt.invoke({"question": question, "context": context_text})
    response = llm.invoke(message)
    content = getattr(response, "content", "")
    if isinstance(content, list):
        return "".join(str(item) for item in content).strip()
    return str(content).strip()


def answer_question(question: str, username: str) -> dict:
    started = perf_counter()
    vector_store = VectorStore()
    retrieval_results = vector_store.search(question, TOP_K)
    filtered_docs = [
        (doc, raw_score)
        for doc, raw_score in retrieval_results
        if score_to_relevance(raw_score) >= MIN_RETRIEVAL_SCORE
    ]
    grounded = bool(filtered_docs)

    if grounded:
        context_text = build_context(filtered_docs)
        try:
            answer = generate_answer(question, context_text)
        except RuntimeError:
            answer = fallback_answer(filtered_docs)
    else:
        answer = "依据现有资料无法给出确切答案。"

    citations = build_citations(filtered_docs)
    latency_ms = int((perf_counter() - started) * 1000)

    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO qa_logs (id, question, answer, citations_json, grounded, latency_ms, username, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                question,
                answer,
                json.dumps(citations, ensure_ascii=False),
                1 if grounded else 0,
                latency_ms,
                username,
                utcnow(),
            ),
        )

    return {
        "answer": answer,
        "citations": citations,
        "grounded": grounded,
        "latencyMs": latency_ms,
    }


def rebuild_index() -> int:
    vector_store = VectorStore()
    rows = fetch_all_chunks()
    if not rows:
        vector_store.clear()
        return 0

    vector_store.rebuild(rows)
    return len(rows)
