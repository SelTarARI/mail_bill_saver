from __future__ import annotations
from .storage import ensure_base_folder
from .settings import load_config
from .imap_client import (
    connect_imap,
    select_mailbox,
    search_unseen,
    fetch_rfc822_peek,
    logout,
)
from .email_parser import parse_email
from .classifier import classify_email
from pathlib import Path
from .db import (
    init_db,
    email_already_processed,
    mark_email_processed,
    attachment_hash_exists,
    record_attachment,
)
from .storage import (
    ensure_base_folder,
    year_month_from_date_header,
    build_target_folder,
    save_attachment,
)
from .utils import extract_domain, sha256_bytes


def main() -> int:
    cfg = load_config("config.toml")

    ensure_base_folder(cfg.storage.base_folder)
    db_path = cfg.storage.base_folder / "processed.sqlite"
    conn_db = init_db(db_path)
    print(f"Storage folder: {cfg.storage.base_folder}")
    print(f"DB: {db_path}")

    conn = connect_imap(
        host=cfg.imap.host,
        port=cfg.imap.port,
        username=cfg.imap.username,
        password=cfg.imap.password,
    )

    try:
        select_mailbox(conn, cfg.imap.mailbox)
        ids = search_unseen(conn)

        print(f"Found {len(ids)} unseen emails in {cfg.imap.mailbox!r}")
        if not ids:
            return 0

        ids_to_process = list(reversed(ids))[: cfg.run.max_emails]

        for i, msg_id in enumerate(ids_to_process, start=1):
            raw = fetch_rfc822_peek(conn, msg_id)
            pe = parse_email(raw)

            attachment_names = [a.filename for a in pe.attachments]
            cl = classify_email(
                subject=pe.subject,
                body_text=pe.body_text,
                attachment_filenames=attachment_names,
                sender=pe.from_,
                threshold=5,
            )

            # Skip if already processed (Message-ID based)
            if pe.message_id and email_already_processed(conn_db, pe.message_id):
                print("SKIP: already processed (message-id)")
                continue

            if cl.is_bill:
                sender_domain = extract_domain(pe.from_)
                ym = year_month_from_date_header(pe.date)
                folder = build_target_folder(cfg.storage.base_folder, sender_domain, ym)

                saved_any = False
                for a in pe.attachments:
                    if not a.payload:
                        continue
                    name_lower = a.filename.lower()
                    if not (
                        name_lower.endswith(".pdf")
                        or name_lower.endswith(".csv")
                        or name_lower.endswith(".xml")
                        or name_lower.endswith(".xlsx")
                    ):
                        print(f"SKIP attachment (not invoice type): {a.filename}")
                        continue

                    h = sha256_bytes(a.payload)
                    if attachment_hash_exists(conn_db, h):
                        print(f"SKIP attachment (duplicate hash): {a.filename}")
                        continue

                    out_path = save_attachment(folder, a.filename, a.payload)
                    record_attachment(
                        conn_db, h, pe.message_id or "", a.filename, str(out_path)
                    )
                    print(f"SAVED: {out_path}")
                    saved_any = True

                mark_email_processed(
                    conn_db, pe.message_id or "", pe.from_, pe.subject, pe.date, True
                )

                if not saved_any:
                    print(
                        "NOTE: classified as BILL but nothing new was saved (all duplicates or empty)."
                    )
            """                    
            else:
                #still record that we saw it (optional). You can comment this out if you prefer.
                mark_email_processed(
                    conn_db, pe.message_id or "", pe.from_, pe.subject, pe.date, False
                )
            """

            print("\n" + "-" * 70)
            print(
                f"[{i}/{len(ids_to_process)}] IMAP ID: {msg_id.decode(errors='ignore')}"
            )
            print(f"FROM:    {pe.from_}")
            print(f"SUBJECT: {pe.subject}")
            print(f"DATE:    {pe.date}")

            # show a small body snippet (helps debugging keywords)
            snippet = (pe.body_text or "").strip().replace("\r", " ").replace("\n", " ")
            if len(snippet) > 160:
                snippet = snippet[:160] + "..."
            print(f"BODY:    {snippet}")

            print(
                f"CLASSIFICATION: {'BILL' if cl.is_bill else 'NOT_BILL'} (score={cl.score})"
            )
            print(f"REASONS: {', '.join(cl.reasons) if cl.reasons else '(none)'}")

            if pe.attachments:
                print("ATTACHMENTS:")
                for a in pe.attachments:
                    kb = len(a.payload) / 1024.0
                    print(f"  - {a.filename} ({a.content_type}, {kb:.1f} KB)")

            else:
                print("ATTACHMENTS: none")

        return 0
    finally:
        logout(conn)


if __name__ == "__main__":
    raise SystemExit(main())
