"""Server-seitige Backup-Dateien (Archiv unter BACKUP_ARCHIVE_DIR)."""
from __future__ import annotations

import gzip
import re
from pathlib import Path
from typing import Any

from django.conf import settings


def backup_archive_dir() -> Path:
    d = getattr(settings, "BACKUP_ARCHIVE_DIR", None)
    if d is None:
        d = Path(settings.BASE_DIR) / "data" / "backups"
    else:
        d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_safe_backup_filename(name: str) -> bool:
    if not name or len(name) > 200:
        return False
    if ".." in name or "/" in name or "\\" in name or name.strip() != name:
        return False
    if name.endswith(".json.gz"):
        base = name[:-9]
    elif name.endswith(".json"):
        base = name[:-5]
    else:
        return False
    if not base or not re.match(r"^[a-zA-Z0-9_.-]+$", base):
        return False
    return True


def resolve_backup_file(name: str) -> Path | None:
    if not is_safe_backup_filename(name):
        return None
    root = backup_archive_dir().resolve()
    p = (root / name).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    if not p.is_file():
        return None
    return p


def backup_kind_from_name(name: str) -> str:
    if name.startswith("sicherheit_vor_restore_"):
        return "sicherheit"
    if name.startswith("megacnc_backup_"):
        return "manuell"
    return "archiv"


def list_archive_entries() -> list[dict[str, Any]]:
    root = backup_archive_dir()
    out: list[dict[str, Any]] = []
    if not root.is_dir():
        return out
    for p in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        if not is_safe_backup_filename(p.name):
            continue
        st = p.stat()
        out.append(
            {
                "name": p.name,
                "size": st.st_size,
                "modified": int(st.st_mtime),
                "kind": backup_kind_from_name(p.name),
            }
        )
    return out


def gzip_write_file(path: Path, utf8_data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as gz:
        gz.write(utf8_data.encode("utf-8"))
