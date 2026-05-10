import fnmatch
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", ".cache", "__pycache__",
             ".git", "coverage", ".next", "target", "venv", ".venv"}
MAX_RESULTS = 100


def handle(args: dict) -> str:
    pattern = args["pattern"]
    root = Path(args.get("path", ".")).expanduser()
    ftype = args.get("type", "f")

    if not root.exists():
        return f"✗ path not found: {root}"

    results = []
    for item in root.rglob("*"):
        if any(p in SKIP_DIRS for p in item.parts):
            continue
        if ftype == "f" and not item.is_file():
            continue
        if ftype == "d" and not item.is_dir():
            continue
        if fnmatch.fnmatch(item.name, pattern):
            results.append(str(item))
            if len(results) >= MAX_RESULTS:
                results.append(f"... [capped at {MAX_RESULTS}]")
                break

    if not results:
        return f"∅ not found: {pattern!r} in {root}"
    return "\n".join(results)
