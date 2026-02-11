from __future__ import annotations

from .settings import load_config
from .imap_client import connect_imap, select_mailbox, search_unseen, fetch_rfc822_peek, logout
from .email_parser import parse_email


def main() -> int:
    cfg = load_config("config.toml")

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

        # Fetch newest first (often highest ID is newest)
        ids_to_process = list(reversed(ids))[: cfg.run.max_emails]

        for i, msg_id in enumerate(ids_to_process, start=1):
            raw = fetch_rfc822_peek(conn, msg_id)
            pe = parse_email(raw)

            print("\n" + "-" * 70)
            print(f"[{i}/{len(ids_to_process)}] IMAP ID: {msg_id.decode(errors='ignore')}")
            print(f"FROM:    {pe.from_}")
            print(f"SUBJECT: {pe.subject}")
            print(f"DATE:    {pe.date}")

            if pe.attachments:
                print("ATTACHMENTS:")
                for a in pe.attachments:
                    kb = a.size_bytes / 1024.0
                    print(f"  - {a.filename} ({a.content_type}, {kb:.1f} KB)")
            else:
                print("ATTACHMENTS: none")

        return 0
    finally:
        logout(conn)


if __name__ == "__main__":
    raise SystemExit(main())
