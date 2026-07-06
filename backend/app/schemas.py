from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    role: str
    displayName: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunkCount: int
    uploadedAt: str
    updatedAt: str


class CitationResponse(BaseModel):
    filename: str
    pageNo: Optional[int] = None
    sectionPath: str = ""
    snippet: str
    score: float = Field(default=0.0)


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class AskResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    grounded: bool
    latencyMs: int


class LogRecordResponse(BaseModel):
    question: str
    answer: str
    citations: List[CitationResponse]
    grounded: bool
    latencyMs: int
    createdAt: str
    username: str


class SettingsResponse(BaseModel):
    kbName: str


class SettingsUpdateRequest(BaseModel):
    kbName: str = Field(min_length=1, max_length=100)
