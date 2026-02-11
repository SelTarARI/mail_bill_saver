from __future__ import annotations

from email.header import decode_header
from typing import Optional


def decode_mime_header(value: Optional[str]) -> str:
    """Decode headers like Subject that may contain MIME encoded-words."""
    if not value:
        return ""
    parts = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()
