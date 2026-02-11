from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


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


@dataclass(frozen=True)
class AppConfig:
    imap: ImapConfig
    run: RunConfig


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
    run_cfg = RunConfig(max_emails=int(rn.get("max_emails", 10)))

    return AppConfig(imap=imap_cfg, run=run_cfg)
