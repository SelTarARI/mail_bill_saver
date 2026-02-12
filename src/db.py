from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Optional


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS emails (
            message_id TEXT PRIMARY KEY,
            from_addr TEXT,
            subject TEXT,
            date TEXT,
            is_bill INTEGER,
            processed_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attachments (
            file_hash TEXT PRIMARY KEY,
            message_id TEXT,
            filename TEXT,
            saved_path TEXT,
            saved_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(message_id) REFERENCES emails(message_id)
        )
        """
    )
    conn.commit()
    return conn


def email_already_processed(conn: sqlite3.Connection, message_id: str) -> bool:
    if not message_id:
        return False
    row = conn.execute(
        "SELECT 1 FROM emails WHERE message_id = ?", (message_id,)
    ).fetchone()
    return row is not None


def mark_email_processed(
    conn: sqlite3.Connection,
    message_id: str,
    from_addr: str,
    subject: str,
    date: str,
    is_bill: bool,
) -> None:
    if not message_id:
        return
    conn.execute(
        """
        INSERT OR REPLACE INTO emails(message_id, from_addr, subject, date, is_bill)
        VALUES (?, ?, ?, ?, ?)
        """,
        (message_id, from_addr, subject, date, 1 if is_bill else 0),
    )
    conn.commit()


def attachment_hash_exists(conn: sqlite3.Connection, file_hash: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM attachments WHERE file_hash = ?", (file_hash,)
    ).fetchone()
    return row is not None


def record_attachment(
    conn: sqlite3.Connection,
    file_hash: str,
    message_id: str,
    filename: str,
    saved_path: str,
) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO attachments(file_hash, message_id, filename, saved_path)
        VALUES (?, ?, ?, ?)
        """,
        (file_hash, message_id, filename, saved_path),
    )
    conn.commit()
