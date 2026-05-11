import fnmatch
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", ".cache", "__pycache__",
             ".git", "coverage", ".next", "target", "venv", ".venv",
             ".mypy_cache", ".pytest_cache", ".npm", ".pnpm-store",
             ".cargo", ".rustup", ".local"}
SKIP_GLOBS = {".codex*", "*.egg-info"}
MAX_ENTRIES = 200


def handle(args: dict) -> str:
    root = Path(args.get("path", ".")).expanduser()
    max_depth = args.get("depth", 3)
    show_hidden = args.get("show_hidden", False)

    if not root.exists():
        return f"✗ not found: {root}"

    lines = [str(root) + "/"]
    counter = [0]

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth or counter[0] >= MAX_ENTRIES:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return

        entries = [e for e in entries if show_hidden or not e.name.startswith(".")]
        entries = [e for e in entries if not _skip_entry(e.name)]

        for i, entry in enumerate(entries):
            if counter[0] >= MAX_ENTRIES:
                lines.append(prefix + "... [truncated]")
                return
            connector = "└── " if i == len(entries) - 1 else "├── "
            label = entry.name + ("/" if entry.is_dir() else "")
            lines.append(prefix + connector + label)
            counter[0] += 1
            if entry.is_dir():
                ext = "    " if i == len(entries) - 1 else "│   "
                _walk(entry, prefix + ext, depth + 1)

    _walk(root, "", 1)

    if counter[0] >= MAX_ENTRIES:
        lines.append(f"[capped at {MAX_ENTRIES} entries]")

    return "\n".join(lines)


def _skip_entry(name: str) -> bool:
    return name in SKIP_DIRS or any(fnmatch.fnmatch(name, pat) for pat in SKIP_GLOBS)
