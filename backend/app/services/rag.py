from __future__ import annotations

import json
import uuid
from time import perf_counter

from ..config import MIN_RETRIEVAL_SCORE, TOP_K
from ..db import connection_scope, utcnow
from .documents import fetch_all_chunks, fetch_chunks_by_ids
from .embeddings import get_embedding_service
from .ollama_client import generate_answer
from .vector_store import VectorStore


def build_citations(chunk_rows: list[dict], scores: dict[str, float]) -> list[dict]:
    citations = []
    for row in chunk_rows:
        citations.append(
            {
                "filename": row["filename"],
                "pageNo": row["page_no"],
                "sectionPath": row["section_path"] or "",
                "snippet": row["content"][:180] + ("..." if len(row["content"]) > 180 else ""),
                "score": round(scores.get(row["id"], 0.0), 4),
            }
        )
    return citations


def build_prompt(question: str, chunk_rows: list[dict]) -> str:
    evidence_blocks = []
    for index, row in enumerate(chunk_rows, start=1):
        label = f"[{index}] {row['filename']}"
        if row["page_no"]:
            label += f" 第{row['page_no']}页"
        if row["section_path"]:
            label += f" / {row['section_path']}"
        evidence_blocks.append(f"{label}\n{row['content']}")

    evidence_text = "\n\n".join(evidence_blocks)
    return (
        "你是一个企业制度问答助手。请严格依据给定资料回答，不要使用资料外知识。\n"
        "如果资料不足，请直接回答：依据现有资料无法给出确切答案。\n"
        "回答要求简洁准确，适合课程演示；不要编造条款、页码或制度名称。\n\n"
        f"问题：{question}\n\n"
        f"资料：\n{evidence_text}\n\n"
        "请给出最终回答："
    )


def fallback_answer(question: str, chunk_rows: list[dict]) -> str:
    if not chunk_rows:
        return "依据现有资料无法给出确切答案。"
    best = chunk_rows[0]["content"][:220]
    return f"未连接到本地模型，以下为最相关资料摘要：{best}"


def answer_question(question: str, username: str) -> dict:
    started = perf_counter()
    embedder = get_embedding_service()
    vector_store = VectorStore()
    query_embedding = embedder.embed_query(question)
    retrieval_results = vector_store.search(query_embedding, TOP_K)

    scores = {chunk_id: score for chunk_id, score in retrieval_results}
    chunk_ids = [chunk_id for chunk_id, score in retrieval_results if score >= MIN_RETRIEVAL_SCORE]
    chunk_rows = fetch_chunks_by_ids(chunk_ids)
    grounded = bool(chunk_rows)

    if grounded:
        prompt = build_prompt(question, chunk_rows)
        try:
            answer = generate_answer(prompt)
        except RuntimeError:
            answer = fallback_answer(question, chunk_rows)
    else:
        answer = "依据现有资料无法给出确切答案。"

    citations = build_citations(chunk_rows, scores)
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
    embedder = get_embedding_service()
    vector_store = VectorStore()
    rows = fetch_all_chunks()
    if not rows:
        vector_store.clear()
        return 0

    embeddings = embedder.embed_texts(row["content"] for row in rows)
    vector_store.save([row["id"] for row in rows], embeddings)
    return len(rows)
