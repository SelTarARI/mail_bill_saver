from __future__ import annotations

import imaplib
from dataclasses import dataclass
from typing import List


@dataclass
class ImapConnection:
    client: imaplib.IMAP4_SSL


def connect_imap(host: str, port: int, username: str, password: str) -> ImapConnection:
    c = imaplib.IMAP4_SSL(host, port)
    c.login(username, password)
    return ImapConnection(client=c)


def select_mailbox(conn: ImapConnection, mailbox: str) -> None:
    # readonly=True so we don’t accidentally mark emails as read while testing
    status, _ = conn.client.select(mailbox, readonly=True)
    if status != "OK":
        raise RuntimeError(f"Failed to select mailbox: {mailbox}")


def search_unseen(conn: ImapConnection) -> List[bytes]:
    status, data = conn.client.search(None, "UNSEEN")
    if status != "OK":
        raise RuntimeError("IMAP search failed")
    # data is [b'1 2 3']
    ids = data[0].split() if data and data[0] else []
    return ids


def fetch_rfc822_peek(conn: ImapConnection, msg_id: bytes) -> bytes:
    # BODY.PEEK[] fetches the full message without setting \Seen on most servers
    msg_id_str = msg_id.decode("ascii")
    status, data = conn.client.fetch(msg_id_str, "(BODY.PEEK[])")

    if status != "OK" or not data:
        raise RuntimeError(f"Failed to fetch message id {msg_id!r}")

    # data looks like: [(b'1 (BODY[] {bytes}', raw_bytes), b')']
    for item in data:
        if isinstance(item, tuple) and isinstance(item[1], (bytes, bytearray)):
            return bytes(item[1])

    raise RuntimeError(f"Unexpected fetch response for {msg_id!r}")


def logout(conn: ImapConnection) -> None:
    try:
        conn.client.logout()
    except Exception:
        pass
