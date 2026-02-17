from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class StorageConfig:
    base_folder: Path
    save_all_attachments_if_bill: bool = False
    allowed_extensions: tuple[str, ...] = ("pdf", "csv", "xml", "xlsx")


@dataclass(frozen=True)
class ImapConfig:
    host: str
    port: int
    username: str
    password: str
    mailbox: str = "INBOX"


@dataclass(frozen=True)
class RunConfig:
    max_emails: int = 10
    days_back: int = 7


@dataclass(frozen=True)
class AppConfig:
    imap: ImapConfig
    run: RunConfig
    storage: StorageConfig


def load_config(config_path: str | Path = "config.toml") -> AppConfig:
    p = Path(config_path)
    if not p.exists():
        raise FileNotFoundError(
            f"Missing {p}. Create it by copying config.example.toml -> config.toml"
        )

    data = tomllib.loads(p.read_text(encoding="utf-8"))

    im = data.get("imap", {})
    rn = data.get("run", {})

    imap_cfg = ImapConfig(
        host=str(im["host"]),
        port=int(im.get("port", 993)),
        username=str(im["username"]),
        password=str(im["password"]),
        mailbox=str(im.get("mailbox", "INBOX")),
    )
    run_cfg = RunConfig(
        max_emails=int(rn.get("max_emails", 10)),
        days_back=int(rn.get("days_back", 7)),
    )

    st = data.get("storage", {})

    allowed = st.get("allowed_extensions", ["pdf", "csv", "xml", "xlsx"])
    allowed = tuple(str(x).lower().lstrip(".") for x in allowed)

    storage_cfg = StorageConfig(
        base_folder=Path(st.get("base_folder", "Bills")).expanduser().resolve(),
        save_all_attachments_if_bill=bool(
            st.get("save_all_attachments_if_bill", False)
        ),
        allowed_extensions=allowed,
    )

    return AppConfig(imap=imap_cfg, run=run_cfg, storage=storage_cfg)
