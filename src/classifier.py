from __future__ import annotations

from dataclasses import dataclass
from typing import List

INVOICE_KEYWORDS = [
    # English
    "invoice",
    "bill",
    "statement",
    "payment due",
    "amount due",
    "due date",
    # German
    "rechnung",
    "kundennummer",
    "betrag",
    "zahlbar",
    "fällig",
    # Turkish
    "fatura",
    "ödeme",
    "son ödeme",
    "tutar",
    # Common variants
    "e-invoice",
    "einvoice",
    "e fatura",
    "e-fatura",
]

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "gmx.com",
    "yandex.com",
    "mail.com",
}

BILL_ATTACHMENT_EXTS = {".pdf", ".csv", ".xml", ".xlsx"}


@dataclass(frozen=True)
class Classification:
    is_bill: bool
    score: int
    reasons: List[str]


def _contains_keyword(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in INVOICE_KEYWORDS)


def classify_email(
    subject: str,
    body_text: str,
    attachment_filenames: List[str],
    sender: str,
    threshold: int = 5,
) -> Classification:
    score = 0
    reasons: List[str] = []

    subj_hit = _contains_keyword(subject)
    body_hit = _contains_keyword(body_text)

    if subj_hit:
        score += 3
        reasons.append("keyword_in_subject(+3)")
    if body_hit:
        score += 2
        reasons.append("keyword_in_body(+2)")

    exts = {
        ("." + fn.lower().rsplit(".", 1)[-1]) if "." in fn else ""
        for fn in attachment_filenames
    }
    bill_ext_hits = sorted([e for e in exts if e in BILL_ATTACHMENT_EXTS])

    if bill_ext_hits:
        score += 3
        reasons.append(f"bill_like_attachment_exts(+3:{','.join(bill_ext_hits)})")

    # extract domain from sender
    sender_lower = sender.lower()

    domain = ""
    if "@" in sender_lower:
        domain = sender_lower.split("@")[-1].strip("> ")

    if domain and domain not in PERSONAL_EMAIL_DOMAINS:
        score += 1
        reasons.append(f"corporate_domain(+1:{domain})")

    is_bill = score >= threshold
    return Classification(is_bill=is_bill, score=score, reasons=reasons)
