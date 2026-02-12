from __future__ import annotations

from pathlib import Path
from email.utils import parsedate_to_datetime
from typing import Tuple

from .utils import sanitize_windows_name


def ensure_base_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def year_month_from_date_header(date_header: str) -> str:
    # returns "YYYY-MM" or "unknown-date"
    try:
        dt = parsedate_to_datetime(date_header)
        return f"{dt.year:04d}-{dt.month:02d}"
    except Exception:
        return "unknown-date"


def build_target_folder(base: Path, sender_domain: str, year_month: str) -> Path:
    vendor = sanitize_windows_name(sender_domain or "unknown-sender")
    ym = sanitize_windows_name(year_month or "unknown-date")
    return base / vendor / ym


def save_attachment(target_folder: Path, filename: str, payload: bytes) -> Path:
    target_folder.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_windows_name(filename, fallback="attachment.bin")
    out_path = target_folder / safe_name

    # if file exists, add suffix
    if out_path.exists():
        stem = out_path.stem
        suffix = out_path.suffix
        n = 1
        while True:
            candidate = target_folder / f"{stem} ({n}){suffix}"
            if not candidate.exists():
                out_path = candidate
                break
            n += 1

    out_path.write_bytes(payload)
    return out_path
