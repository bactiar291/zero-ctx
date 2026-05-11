"""zc_stat: File/dir metadata without reading content."""
import os
from pathlib import Path
from datetime import datetime


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()

    if not path.exists():
        return f"✗ not found: {path}"

    st = path.stat()
    size = st.st_size
    modified = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    if path.is_file():
        try:
            with open(path, "rb") as f:
                lines = sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1024 * 1024), b""))
        except Exception:
            lines = -1
        size_str = _fmt_size(size)
        return f"file  {path}\nsize  {size_str}\nlines ~{lines}\nmtime {modified}"

    if path.is_dir():
        try:
            entries = list(path.iterdir())
            files = sum(1 for e in entries if e.is_file())
            dirs = sum(1 for e in entries if e.is_dir())
        except Exception:
            files = dirs = -1
        return f"dir   {path}\nfiles {files}\ndirs  {dirs}\nmtime {modified}"

    return f"✗ unknown type: {path}"


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"
