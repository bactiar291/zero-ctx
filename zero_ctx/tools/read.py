from pathlib import Path

MAX_AUTO = 200


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    mode = args.get("mode", "auto")

    if not path.exists():
        return f"✗ not found: {path}"
    if not path.is_file():
        return f"✗ not a file: {path}"

    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception as e:
        return f"✗ read error: {e}"

    total = len(lines)

    if mode == "auto":
        if total <= MAX_AUTO:
            return _fmt(lines, 1, total, total, path)
        head = lines[:80]
        tail = lines[-40:]
        skipped = total - 120
        return (
            _fmt(head, 1, 80, total, path)
            + f"\n... [{skipped} lines skipped] ...\n"
            + _fmt(tail, total - 39, total, total, path)
        )

    if mode.startswith("lines:"):
        parts = mode[6:].split("-")
        start = max(1, int(parts[0]))
        end = min(total, int(parts[1])) if len(parts) > 1 else total
        return _fmt(lines[start - 1:end], start, end, total, path)

    if mode.startswith("head:"):
        n = int(mode[5:])
        return _fmt(lines[:n], 1, min(n, total), total, path)

    if mode.startswith("tail:"):
        n = int(mode[5:])
        start = max(1, total - n + 1)
        return _fmt(lines[total - n:], start, total, total, path)

    if mode.startswith("around:"):
        parts = mode[7:].split(":")
        center = int(parts[0])
        ctx = int(parts[1]) if len(parts) > 1 else 10
        start = max(1, center - ctx)
        end = min(total, center + ctx)
        return _fmt(lines[start - 1:end], start, end, total, path)

    return f"✗ unknown mode: {mode}"


def _fmt(lines, start, end, total, path) -> str:
    header = f"# {path} [{start}-{end}/{total}]\n"
    numbered = "\n".join(f"{start + i:4d}\t{l}" for i, l in enumerate(lines))
    return header + numbered
