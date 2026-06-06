from __future__ import annotations

import io
import re
import uuid
from typing import Any

import pypdf

_SECTION_RE = re.compile(
    r"^(Άρθρο|Article|Section|SECTION|ARTICLE)\s+[\dΑ-Ωα-ω]+",
    re.UNICODE,
)
_MIN_CHUNK_CHARS = 60


def parse_pdf_to_chunks(pdf_bytes: bytes, tender_id: str) -> list[dict[str, Any]]:
    """Extract text from a PDF and split into annotated chunks.

    Each chunk carries metadata: {tender_id, locator} where locator is a
    best-effort section/article heading or page number.
    """
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    chunks: list[dict[str, Any]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text: str = page.extract_text() or ""
        locator = f"p.{page_num}"

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for line in lines[:5]:
            if _SECTION_RE.match(line):
                locator = line[:60]
                break

        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        for i, para in enumerate(paragraphs):
            if len(para) < _MIN_CHUNK_CHARS:
                continue
            chunk_id = f"{tender_id}-p{page_num}-c{i}-{uuid.uuid4().hex[:8]}"
            chunks.append(
                {
                    "id": chunk_id,
                    "text": para,
                    "metadata": {
                        "tender_id": tender_id,
                        "locator": locator,
                    },
                }
            )

    return chunks
