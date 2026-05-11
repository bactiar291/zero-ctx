import os
import fnmatch
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", ".cache", "__pycache__",
             ".git", "coverage", ".next", "target", "venv", ".venv",
             ".mypy_cache", ".pytest_cache", ".npm", ".pnpm-store",
             ".cargo", ".rustup", ".local"}
SKIP_GLOBS = {".codex*", "*.egg-info"}
MAX_RESULTS = 100
MAX_SCANNED_DIRS = 20000


def handle(args: dict) -> str:
    pattern = args["pattern"]
    root = Path(args.get("path", ".")).expanduser()
    ftype = args.get("type", "f")

    if not root.exists():
        return f"✗ path not found: {root}"

    results = []
    scanned_dirs = 0

    for dirpath, dirnames, filenames in os.walk(root):
        scanned_dirs += 1
        if scanned_dirs > MAX_SCANNED_DIRS:
            results.append(f"... [scan capped at {MAX_SCANNED_DIRS} dirs]")
            break

        dirnames[:] = [
            d for d in dirnames
            if not _skip_dir(d)
        ]

        if ftype in ("d", "any"):
            for dirname in dirnames:
                if fnmatch.fnmatch(dirname, pattern):
                    results.append(str(Path(dirpath) / dirname))
                    if len(results) >= MAX_RESULTS:
                        results.append(f"... [capped at {MAX_RESULTS}]")
                        return "\n".join(results)

        if ftype in ("f", "any"):
            for filename in filenames:
                if fnmatch.fnmatch(filename, pattern):
                    results.append(str(Path(dirpath) / filename))
                    if len(results) >= MAX_RESULTS:
                        results.append(f"... [capped at {MAX_RESULTS}]")
                        return "\n".join(results)

    if not results:
        return f"∅ not found: {pattern!r} in {root}"
    return "\n".join(results)


def _skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or any(fnmatch.fnmatch(name, pat) for pat in SKIP_GLOBS)
