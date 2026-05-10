import subprocess

MAX_LINES = 300
_NOISE = ("index ", "old mode", "new mode", "similarity index",
          "rename from", "rename to", "Binary files")


def handle(args: dict) -> str:
    cwd = args.get("path", ".")
    staged = args.get("staged", False)
    file_ = args.get("file", "")

    cmd = ["git", "diff", "--ignore-all-space"]
    if staged:
        cmd.append("--staged")
    if file_:
        cmd += ["--", file_]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
    except subprocess.TimeoutExpired:
        return "✗ diff timeout"
    except FileNotFoundError:
        return "✗ git not found"

    if r.returncode != 0:
        return f"✗ git error: {r.stderr.strip()}"

    if not r.stdout.strip():
        return "∅ no changes"

    compact = []
    for line in r.stdout.splitlines():
        if any(line.startswith(n) for n in _NOISE):
            continue
        if (line.startswith("diff --git") or line.startswith("@@") or
                line.startswith("+") or line.startswith("-") or
                line.startswith("--- ") or line.startswith("+++ ")):
            compact.append(line)

    if len(compact) > MAX_LINES:
        compact = compact[:MAX_LINES]
        compact.append(f"... [truncated at {MAX_LINES} lines]")

    return "\n".join(compact)
