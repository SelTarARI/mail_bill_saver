from __future__ import annotations

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
from .logger_setup import setup_logging


def main() -> int:
    cfg = load_config("config.toml")

    # Prepare storage + DB + logging
    ensure_base_folder(cfg.storage.base_folder)

    db_path = cfg.storage.base_folder / "processed.sqlite"
    conn_db = init_db(db_path)

    log_path = cfg.storage.base_folder / "run.log"
    logger = setup_logging(log_path)

    logger.info(
        f"Config: save_all_attachments_if_bill={cfg.storage.save_all_attachments_if_bill}, "
        f"allowed_extensions={list(cfg.storage.allowed_extensions)}"
    )

    logger.info(f"DB: {db_path}")

    # Counters for a clean summary
    scanned = 0
    bills = 0
    saved_files = 0
    skipped_dupe = 0
    skipped_processed = 0
    errors = 0

    # Connect IMAP
    conn = connect_imap(
        host=cfg.imap.host,
        port=cfg.imap.port,
        username=cfg.imap.username,
        password=cfg.imap.password,
    )

    try:
        select_mailbox(conn, cfg.imap.mailbox)
        ids = search_unseen(conn)

        ids_to_process = list(reversed(ids))[: cfg.run.max_emails]
        logger.info(
            f"Found {len(ids)} unseen; processing newest {len(ids_to_process)} "
            f"(max_emails={cfg.run.max_emails})"
        )

        if not ids_to_process:
            logger.info("No emails to process.")
            return 0

        for i, msg_id in enumerate(ids_to_process, start=1):
            try:
                scanned += 1

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

                # Do NOT log or store NOT_BILL emails
                if not cl.is_bill:
                    continue

                bills += 1

                logger.info("-" * 70)
                logger.info(f"[{i}/{len(ids_to_process)}] BILL email")
                logger.info(f"IMAP ID: {msg_id.decode(errors='ignore')}")
                logger.info(f"FROM: {pe.from_}")
                logger.info(f"SUBJECT: {pe.subject}")
                logger.info(f"DATE: {pe.date}")
                logger.info(
                    f"SCORE: {cl.score}  REASONS: {', '.join(cl.reasons) if cl.reasons else '(none)'}"
                )

                # Skip if already processed (Message-ID based)
                if pe.message_id and email_already_processed(conn_db, pe.message_id):
                    skipped_processed += 1
                    logger.info("SKIP: already processed (message-id)")
                    continue

                sender_domain = extract_domain(pe.from_)
                ym = year_month_from_date_header(pe.date)
                folder = build_target_folder(cfg.storage.base_folder, sender_domain, ym)

                saved_any = False

                for a in pe.attachments:
                    if not a.payload:
                        continue

                    # Only filter by extension if "save_all_attachments_if_bill" is False
                    if not cfg.storage.save_all_attachments_if_bill:
                        name_lower = a.filename.lower()
                        ext = name_lower.rsplit(".", 1)[-1] if "." in name_lower else ""
                        if ext not in cfg.storage.allowed_extensions:
                            logger.info(f"SKIP attachment (ext not allowed): {a.filename}")
                            continue

                    h = sha256_bytes(a.payload)

                    if attachment_hash_exists(conn_db, h):
                        skipped_dupe += 1
                        logger.info(f"SKIP attachment (duplicate hash): {a.filename}")
                        continue

                    out_path = save_attachment(folder, a.filename, a.payload)
                    record_attachment(conn_db, h, pe.message_id or "", a.filename, str(out_path))
                    saved_files += 1
                    logger.info(f"SAVED: {out_path}")
                    saved_any = True


                # Mark BILL emails processed (so we don't re-handle next run)
                mark_email_processed(
                    conn_db, pe.message_id or "", pe.from_, pe.subject, pe.date, True
                )

                if not saved_any:
                    logger.info(
                        "NOTE: classified as BILL but nothing new was saved (all duplicates or empty)."
                    )

            except Exception as e:
                errors += 1
                logger.exception(f"ERROR processing IMAP ID {msg_id!r}: {e}")
                continue

        logger.info(
            f"SUMMARY: scanned={scanned}, bills={bills}, saved_files={saved_files}, "
            f"skipped_processed={skipped_processed}, skipped_dupe={skipped_dupe}, errors={errors}"
        )
        return 0

    finally:
        try:
            conn_db.close()
        except Exception:
            pass
        logout(conn)


if __name__ == "__main__":
    raise SystemExit(main())
