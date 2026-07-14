from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONTROL_DIR = SCRIPT_DIR.parent
WORKSPACE = CONTROL_DIR.parent
CONFIG_PATH = CONTROL_DIR / "config.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def workspace_path(relative: str) -> Path:
    return WORKSPACE / Path(relative)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_file_id(relative_path: str) -> str:
    normalised = relative_path.replace("\\", "/").casefold().encode("utf-8")
    return "f_" + hashlib.sha256(normalised).hexdigest()[:20]


def is_reparse_point(path: Path) -> bool:
    try:
        attrs = os.lstat(path).st_file_attributes
        return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return path.is_symlink()


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"
