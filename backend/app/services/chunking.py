from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from ..config import CHUNK_MAX_CHARS, CHUNK_MIN_CHARS, CHUNK_OVERLAP


HEADING_PATTERN = re.compile(r"^(第[一二三四五六七八九十百零\d]+[章节条]|[一二三四五六七八九十]+、|\d+(\.\d+){0,3})")


@dataclass
class Segment:
    text: str
    section_path: str = ""
    page_no: int | None = None


@dataclass
class Chunk:
    content: str
    section_path: str = ""
    page_no: int | None = None


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_heading(line: str) -> bool:
    return bool(HEADING_PATTERN.match(line.strip())) or line.strip().startswith("#")


def split_large_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> List[str]:
    sentences = re.split(r"(?<=[。！？；;])", text)
    pieces: List[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(buffer) + len(sentence) <= max_chars:
            buffer += sentence
            continue
        if buffer:
            pieces.append(buffer)
            buffer = ""
        while len(sentence) > max_chars:
            pieces.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        buffer = sentence
    if buffer:
        pieces.append(buffer)
    return pieces or [text[:max_chars]]


def build_segments_from_lines(lines: Iterable[str]) -> List[Segment]:
    segments: List[Segment] = []
    heading_stack: List[str] = []
    for raw_line in lines:
        line = normalize_text(raw_line)
        if not line:
            continue
        if detect_heading(line):
            heading_stack = heading_stack[:2]
            heading_stack.append(line.lstrip("# ").strip())
            continue
        segments.append(Segment(text=line, section_path=" / ".join(heading_stack)))
    return segments


def chunk_segments(segments: List[Segment]) -> List[Chunk]:
    if not segments:
        return []

    chunks: List[Chunk] = []
    current_parts: List[str] = []
    current_section = segments[0].section_path
    current_page = segments[0].page_no

    def flush() -> None:
        nonlocal current_parts
        if not current_parts:
            return
        text = normalize_text(" ".join(current_parts))
        if text:
            chunks.append(Chunk(content=text, section_path=current_section, page_no=current_page))
        current_parts = []

    for segment in segments:
        parts = split_large_text(segment.text) if len(segment.text) > CHUNK_MAX_CHARS else [segment.text]
        for part in parts:
            candidate = normalize_text(" ".join(current_parts + [part]))
            if current_parts and (len(candidate) > CHUNK_MAX_CHARS or segment.section_path != current_section):
                overlap_seed = normalize_text(" ".join(current_parts))[-CHUNK_OVERLAP:]
                flush()
                current_parts = [overlap_seed] if overlap_seed else []
                current_section = segment.section_path
                current_page = segment.page_no
            if not current_parts:
                current_section = segment.section_path
                current_page = segment.page_no
            current_parts.append(part)
            if len(normalize_text(" ".join(current_parts))) >= CHUNK_MIN_CHARS:
                flush()
    flush()
    return chunks
