from __future__ import annotations

from pathlib import Path
import shutil

from ..config import INDEX_DIR
from .embeddings import get_embedding_service

try:
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
except Exception:  # pragma: no cover - optional dependency
    FAISS = None
    Document = None  # type: ignore


class VectorStore:
    def __init__(self) -> None:
        self.store_dir = Path(INDEX_DIR / "langchain_faiss")
        self.index_file = self.store_dir / "index.faiss"

    def rebuild(self, rows: list[dict]) -> None:
        if FAISS is None or Document is None:
            raise RuntimeError("LangChain FAISS 组件未安装")
        if not rows:
            self.clear()
            return

        self.clear()
        self.store_dir.mkdir(parents=True, exist_ok=True)
        documents = [
            Document(
                page_content=row["content"],
                metadata={
                    "chunk_id": row["id"],
                    "document_id": row["document_id"],
                    "filename": row["filename"],
                    "page_no": row["page_no"],
                    "section_path": row["section_path"] or "",
                    "chunk_index": row["chunk_index"],
                },
            )
            for row in rows
        ]
        vector_store = FAISS.from_documents(documents, get_embedding_service())
        vector_store.save_local(str(self.store_dir))

    def clear(self) -> None:
        if self.store_dir.exists():
            shutil.rmtree(self.store_dir)

    def search(self, question: str, top_k: int) -> list[tuple[Document, float]]:
        if FAISS is None or Document is None:
            raise RuntimeError("LangChain FAISS 组件未安装")
        if not self.index_file.exists():
            return []
        vector_store = FAISS.load_local(
            str(self.store_dir),
            get_embedding_service(),
            allow_dangerous_deserialization=True,
        )
        return vector_store.similarity_search_with_score(question, k=top_k)
