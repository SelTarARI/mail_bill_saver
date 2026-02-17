# Mail Bill Saver

A Python-based automation tool that:

- Connects to an IMAP mailbox (Gmail, Outlook, or any IMAP server)
- Detects bill/invoice emails using rule-based classification
- Saves invoice attachments locally
- Avoids duplicates using SQLite (message-id + file hash)
- Logs all actions to a `run.log` file

---

## ✨ Features

- IMAP over SSL
- Config-driven behavior (no hardcoded paths)
- Adjustable invoice detection rules
- Configurable attachment filtering
- Optional: save all attachments for detected bills
- Deduplication via SQLite
- Safe per-email error isolation
- Configurable `days_back` filter
- Batch safety limit via `max_emails`

---

## 📁 Project Structure

    src/
      main.py
      settings.py
      imap_client.py
      email_parser.py
      classifier.py
      storage.py
      db.py
      utils.py
      logger_setup.py

    config.example.toml

---

## ⚙️ Configuration

Copy:

    config.example.toml

to:

    config.toml

### Example Configuration

```toml
[imap]
host = "imap.gmail.com"
port = 993
username = "your@email.com"
password = "APP_PASSWORD"
mailbox = "INBOX"

[run]
max_emails = 10
days_back = 7

[storage]
base_folder = "bills"
save_all_attachments_if_bill = true
allowed_extensions = ["pdf", "csv", "xml", "xlsx", "zip", "html"]
```

---

## 🔎 How It Works

1. Connects to IMAP.
2. Searches for:

    UNSEEN SINCE <today - days_back>

3. Classifies each email using:
   - Subject keywords
   - Body keywords
   - Attachment extensions
   - Sender domain heuristics

4. If classified as BILL:
   - Saves attachments
   - Uses SHA256 hash to avoid duplicates
   - Records processing in SQLite database

---

## ▶ Running the Program

From project root:

    py -m src.main

---

## ⏱ Scheduling (Optional)

You may choose to:

- Run manually when needed
- Schedule execution every 10–30 minutes using Windows Task Scheduler
- Use any system scheduler (cron, etc.)

The program is idempotent:

- Duplicate attachments are not saved
- Already processed emails are skipped
- Errors in one email do not stop the run

---

## 📝 Logs

Logs are written to:

    <base_folder>/run.log

Each run produces:

- Config summary
- Processing summary
- Bill details
- Error logs (if any)

---

## 🗄 Database

SQLite file:

    <base_folder>/processed.sqlite

Tracks:

- Processed emails (by Message-ID)
- Saved attachments (by SHA256 hash)

---

## 🧠 Customizing Invoice Detection

Detection logic lives in:

    src/classifier.py

You can:

- Add/remove keywords
- Adjust scoring
- Modify domain logic

---

## ✅ Recommended Settings

For stable operation:

- days_back = 7
- max_emails = 25
- Schedule every 15 minutes (optional)

---

## ⚠ Notes

- Gmail requires App Password + IMAP enabled.
- Windows paths should use forward slashes:
  "C:/Bills"
- The program is safe to run repeatedly.

---

## 🚀 Future Improvements (Optional)

- Mark processed bills as \Seen
- Move classifier rules fully to config
- Add automated tests using sample `.eml` files
- Add CLI arguments for dry-run mode
