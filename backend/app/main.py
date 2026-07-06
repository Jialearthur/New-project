from __future__ import annotations

import json

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import create_session, require_admin, require_user
from .config import APP_NAME, CORS_ORIGINS
from .db import connection_scope, init_db
from .schemas import (
    AskRequest,
    AskResponse,
    DocumentResponse,
    LogRecordResponse,
    LoginRequest,
    LoginResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    UserResponse,
)
from .services.documents import (
    create_document_record,
    delete_document_record,
    get_document,
    list_documents,
    parse_document_to_chunks,
    remove_file,
    replace_document_chunks,
    set_document_status,
    store_uploaded_file,
)
from .services.rag import answer_question, rebuild_index


app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    try:
        rebuild_index()
    except Exception:
        # Allow the API to start even if LangChain/Ollama dependencies are not ready yet.
        pass


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> dict:
    session = create_session(payload.username, payload.password)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return session


@app.get("/api/me", response_model=UserResponse)
def me(user: dict = Depends(require_user)) -> dict:
    return user


@app.get("/api/settings", response_model=SettingsResponse)
def get_settings(user: dict = Depends(require_user)) -> dict:
    with connection_scope() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'kb_name'").fetchone()
    return {"kbName": row["value"] if row else ""}


@app.put("/api/settings", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdateRequest, user: dict = Depends(require_admin)) -> dict:
    with connection_scope() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('kb_name', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (payload.kbName,),
        )
    return {"kbName": payload.kbName}


@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), user: dict = Depends(require_admin)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    if file.filename.rsplit(".", 1)[-1].lower() not in {"pdf", "docx", "txt", "md", "html"}:
        raise HTTPException(status_code=400, detail="仅支持 PDF、DOCX、TXT、MD、HTML")

    file_bytes = await file.read()
    document_id, stored_path = store_uploaded_file(file_bytes, file.filename)
    create_document_record(document_id, file.filename, stored_path)

    try:
        chunks = parse_document_to_chunks(document_id, str(stored_path))
        replace_document_chunks(document_id, chunks)
        rebuild_index()
    except Exception as exc:
        delete_document_record(document_id)
        remove_file(str(stored_path))
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document = get_document(document_id)
    return {
        "id": document["id"],
        "filename": document["filename"],
        "status": document["status"],
        "chunkCount": document["chunk_count"],
        "uploadedAt": document["uploaded_at"],
        "updatedAt": document["updated_at"],
    }


@app.get("/api/documents", response_model=list[DocumentResponse])
def documents(user: dict = Depends(require_user)) -> list[dict]:
    return list_documents()


@app.post("/api/documents/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(document_id: str, user: dict = Depends(require_admin)) -> dict:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    try:
        chunks = parse_document_to_chunks(document_id, document["stored_path"])
        replace_document_chunks(document_id, chunks)
        rebuild_index()
    except Exception as exc:
        set_document_status(document_id, "failed", 0)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document = get_document(document_id)
    return {
        "id": document["id"],
        "filename": document["filename"],
        "status": document["status"],
        "chunkCount": document["chunk_count"],
        "uploadedAt": document["uploaded_at"],
        "updatedAt": document["updated_at"],
    }


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str, user: dict = Depends(require_admin)) -> dict:
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    delete_document_record(document_id)
    remove_file(document["stored_path"])
    rebuild_index()
    return {"ok": True}


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, user: dict = Depends(require_user)) -> dict:
    try:
        return answer_question(payload.question, user["username"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/logs", response_model=list[LogRecordResponse])
def logs(user: dict = Depends(require_admin)) -> list[dict]:
    with connection_scope() as conn:
        rows = conn.execute(
            "SELECT question, answer, citations_json, grounded, latency_ms, created_at, username FROM qa_logs ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "question": row["question"],
            "answer": row["answer"],
            "citations": json.loads(row["citations_json"]),
            "grounded": bool(row["grounded"]),
            "latencyMs": row["latency_ms"],
            "createdAt": row["created_at"],
            "username": row["username"],
        }
        for row in rows
    ]


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}
