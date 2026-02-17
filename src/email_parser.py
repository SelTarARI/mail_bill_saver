from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import List
import re
from .utils import decode_mime_header


@dataclass(frozen=True)
class AttachmentInfo:
    filename: str
    content_type: str
    payload: bytes  # <-- actual bytes


@dataclass(frozen=True)
class ParsedEmail:
    message_id: str
    from_: str
    subject: str
    date: str
    body_text: str
    attachments: List[AttachmentInfo]


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def _extract_body_text(msg: EmailMessage) -> str:
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    content = body.get_content()
    if body.get_content_type() == "text/html":
        return _html_to_text(content)
    return content.strip()


def parse_email(raw_bytes: bytes) -> ParsedEmail:
    msg: EmailMessage = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    message_id = (msg.get("Message-ID") or "").strip()
    from_ = decode_mime_header(msg.get("From"))
    subject = decode_mime_header(msg.get("Subject"))
    date = msg.get("Date", "")

    body_text = _extract_body_text(msg)

    attachments: List[AttachmentInfo] = []
    for part in msg.walk():
        if part.is_multipart():
            continue

        disp = part.get_content_disposition()
        filename = part.get_filename()
        if disp == "attachment" or (filename is not None):
            filename = decode_mime_header(filename) if filename else "attachment.bin"

            raw_payload = part.get_payload(decode=True)
            payload = (
                raw_payload if isinstance(raw_payload, (bytes, bytearray)) else b""
            )
            payload = bytes(payload)

            attachments.append(
                AttachmentInfo(
                    filename=filename,
                    content_type=part.get_content_type(),
                    payload=payload,
                )
            )

    return ParsedEmail(
        message_id=message_id,
        from_=from_,
        subject=subject,
        date=date,
        body_text=body_text,
        attachments=attachments,
    )
