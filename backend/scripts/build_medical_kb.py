from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import asdict
from pathlib import Path


CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[1]
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import DB_PATH, DEFAULT_KB_NAME  # noqa: E402
from backend.app.db import connection_scope, init_db, utcnow  # noqa: E402
from backend.app.services.documents import ParsedChunk, parse_document_to_chunks  # noqa: E402
from backend.app.services.rag import rebuild_index  # noqa: E402


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="离线批量构建医疗知识库，并直接写入当前项目的 SQLite + LangChain FAISS 索引。"
    )
    parser.add_argument(
        "--source",
        default=str(PROJECT_ROOT / "sample_docs"),
        help="待导入文档目录，默认使用项目根目录下的 sample_docs",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="导入前清空现有 documents/chunks 记录，再重建索引",
    )
    parser.add_argument(
        "--kb-name",
        default=DEFAULT_KB_NAME,
        help="写入 settings.kb_name 的知识库名称，默认使用当前配置值",
    )
    return parser.parse_args()


def iter_files(source_dir: Path) -> list[Path]:
    files = [path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def clear_existing_data() -> None:
    with connection_scope() as conn:
        conn.execute("DELETE FROM qa_logs")
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")


def upsert_kb_name(kb_name: str) -> None:
    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('kb_name', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (kb_name,),
        )


def insert_document_and_chunks(document_id: str, file_path: Path, chunks: list[ParsedChunk]) -> None:
    now = utcnow()
    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, stored_path, extension, status, chunk_count, uploaded_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                file_path.name,
                str(file_path),
                file_path.suffix.lower(),
                "ready",
                len(chunks),
                now,
                now,
            ),
        )
        conn.executemany(
            """
            INSERT INTO chunks (id, document_id, chunk_index, section_path, page_no, content, created_at)
            VALUES (:id, :document_id, :chunk_index, :section_path, :page_no, :content, :created_at)
            """,
            [asdict(chunk) for chunk in chunks],
        )


def build_from_directory(source_dir: Path, clear_existing: bool, kb_name: str) -> None:
    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"目录不存在: {source_dir}")

    init_db()
    upsert_kb_name(kb_name)
    if clear_existing:
        clear_existing_data()

    files = iter_files(source_dir)
    if not files:
        raise FileNotFoundError(f"未在目录中找到支持的文档类型: {source_dir}")

    total_chunks = 0
    print(f"[KB] Source: {source_dir}")
    print(f"[KB] Files found: {len(files)}")
    print(f"[KB] Database: {DB_PATH}")

    for file_path in files:
        document_id = str(uuid.uuid4())
        chunks = parse_document_to_chunks(document_id, str(file_path))
        insert_document_and_chunks(document_id, file_path, chunks)
        total_chunks += len(chunks)
        print(f"[KB] Imported: {file_path.name} -> {len(chunks)} chunks")

    indexed_count = rebuild_index()
    print(f"[KB] Total chunks stored: {total_chunks}")
    print(f"[KB] FAISS chunks indexed: {indexed_count}")
    print("[KB] Done.")


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source).resolve()
    try:
        build_from_directory(source_dir, args.clear, args.kb_name)
    except Exception as exc:
        print(f"[KB] Failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
