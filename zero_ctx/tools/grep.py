import re
import subprocess
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", ".cache", "__pycache__",
             ".git", "coverage", ".next", "target", "venv", ".venv"}
MAX_MATCHES = 50


def handle(args: dict) -> str:
    pattern = args["pattern"]
    path = args.get("path", ".")
    recursive = args.get("recursive", True)
    ctx = args.get("context", 1)

    cmd = ["grep", "-n", f"--context={ctx}", "-E"]
    if recursive:
        cmd += ["-r"]
        for d in SKIP_DIRS:
            cmd += [f"--exclude-dir={d}"]
    cmd += [pattern, path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out = result.stdout
    except subprocess.TimeoutExpired:
        return "✗ grep timeout (>15s)"
    except FileNotFoundError:
        return _python_grep(pattern, path, recursive, ctx)

    if not out.strip():
        return f"∅ no matches: {pattern!r}"

    lines = out.splitlines()
    cap = MAX_MATCHES * (ctx * 2 + 2)
    truncated = len(lines) > cap
    if truncated:
        lines = lines[:cap]

    result_str = "\n".join(lines)
    if truncated:
        result_str += f"\n... [capped at {MAX_MATCHES} matches]"
    return result_str


def _python_grep(pattern, path, recursive, ctx):
    regex = re.compile(pattern)
    matches = []
    root = Path(path)
    files = root.rglob("*") if recursive else root.glob("*")
    for f in files:
        if f.is_file() and not any(p in SKIP_DIRS for p in f.parts):
            try:
                lines = f.read_text(errors="replace").splitlines()
                for i, line in enumerate(lines):
                    if regex.search(line):
                        start = max(0, i - ctx)
                        end = min(len(lines), i + ctx + 1)
                        for j in range(start, end):
                            prefix = ">" if j == i else " "
                            matches.append(f"{f}:{j+1}{prefix} {lines[j]}")
                        matches.append("--")
                        if len(matches) > MAX_MATCHES * 5:
                            matches.append("... [capped]")
                            return "\n".join(matches)
            except Exception:
                continue
    return "\n".join(matches) if matches else f"∅ no matches: {pattern!r}"
