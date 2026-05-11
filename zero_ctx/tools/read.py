from pathlib import Path
from collections import deque

MAX_AUTO = 200
AUTO_HEAD = 80
AUTO_TAIL = 40


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    mode = args.get("mode", "auto")

    if not path.exists():
        return f"✗ not found: {path}"
    if not path.is_file():
        return f"✗ not a file: {path}"

    if mode == "auto":
        try:
            total = _count_lines(path)
            if total <= MAX_AUTO:
                lines = _read_range(path, 1, total)
                return _fmt(lines, 1, total, total, path)
            head = _read_range(path, 1, AUTO_HEAD)
            tail = _read_tail(path, AUTO_TAIL)
        except Exception as e:
            return f"✗ read error: {e}"
        skipped = total - AUTO_HEAD - AUTO_TAIL
        return (
            _fmt(head, 1, AUTO_HEAD, total, path)
            + f"\n... [{skipped} lines skipped] ...\n"
            + _fmt(tail, total - AUTO_TAIL + 1, total, total, path)
        )

    if mode.startswith("lines:"):
        parts = mode[6:].split("-")
        start = max(1, int(parts[0]))
        total = _count_lines(path)
        end = min(total, int(parts[1])) if len(parts) > 1 else total
        return _fmt(_read_range(path, start, end), start, end, total, path)

    if mode.startswith("head:"):
        n = int(mode[5:])
        total = _count_lines(path)
        end = min(n, total)
        return _fmt(_read_range(path, 1, end), 1, end, total, path)

    if mode.startswith("tail:"):
        n = int(mode[5:])
        total = _count_lines(path)
        start = max(1, total - n + 1)
        return _fmt(_read_tail(path, n), start, total, total, path)

    if mode.startswith("around:"):
        parts = mode[7:].split(":")
        center = int(parts[0])
        ctx = int(parts[1]) if len(parts) > 1 else 10
        total = _count_lines(path)
        start = max(1, center - ctx)
        end = min(total, center + ctx)
        return _fmt(_read_range(path, start, end), start, end, total, path)

    return f"✗ unknown mode: {mode}"


def _fmt(lines, start, end, total, path) -> str:
    header = f"# {path} [{start}-{end}/{total}]\n"
    numbered = "\n".join(f"{start + i:4d}\t{l}" for i, l in enumerate(lines))
    return header + numbered


def _count_lines(path: Path) -> int:
    total = 0
    last = b""
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            total += chunk.count(b"\n")
            last = chunk[-1:]
    if last and last != b"\n":
        total += 1
    return total


def _read_range(path: Path, start: int, end: int) -> list[str]:
    if end < start:
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            if lineno < start:
                continue
            if lineno > end:
                break
            out.append(line.rstrip("\n"))
    return out


def _read_tail(path: Path, n: int) -> list[str]:
    if n <= 0:
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in deque(f, maxlen=n)]
