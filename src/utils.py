from __future__ import annotations

from email.header import decode_header
from typing import Optional
import hashlib
import re


def decode_mime_header(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


_WINDOWS_FORBIDDEN = r'<>:"/\|?*'
_WINDOWS_FORBIDDEN_RE = re.compile(rf"[{re.escape(_WINDOWS_FORBIDDEN)}]")


def sanitize_windows_name(name: str, fallback: str = "unknown") -> str:
    name = (name or "").strip()
    if not name:
        return fallback
    name = _WINDOWS_FORBIDDEN_RE.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip()
    # Windows also hates trailing dots/spaces
    name = name.rstrip(" .")
    return name or fallback


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_domain(addr: str) -> str:
    a = (addr or "").lower()
    if "@" not in a:
        return ""
    # handles "Name <x@y.com>"
    domain = a.split("@")[-1]
    domain = domain.strip().strip(">").strip()
    # remove extra junk after domain
    domain = domain.split()[0]
    return domain
