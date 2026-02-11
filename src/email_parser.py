from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from typing import List, Optional, Tuple

from .utils import decode_mime_header


@dataclass(frozen=True)
class AttachmentInfo:
    filename: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class ParsedEmail:
    from_: str
    subject: str
    date: str
    attachments: List[AttachmentInfo]


def parse_email(raw_bytes: bytes) -> ParsedEmail:
    msg: EmailMessage = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    from_ = decode_mime_header(msg.get("From"))
    subject = decode_mime_header(msg.get("Subject"))
    date = msg.get("Date", "")

    attachments: List[AttachmentInfo] = []
    for part in msg.walk():
        # Skip container parts
        if part.is_multipart():
            continue

        disp = part.get_content_disposition()  # 'attachment', 'inline', or None
        filename = part.get_filename()
        if disp == "attachment" or (filename is not None):
            filename = decode_mime_header(filename) if filename else "attachment.bin"
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                AttachmentInfo(
                    filename=filename,
                    content_type=part.get_content_type(),
                    size_bytes=len(payload),
                )
            )

    return ParsedEmail(from_=from_, subject=subject, date=date, attachments=attachments)
