from pathlib import Path


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    old_str = args["old_str"]
    new_str = args["new_str"]

    if not path.exists():
        return f"✗ not found: {path}"

    try:
        content = path.read_text(errors="replace")
    except Exception as e:
        return f"✗ read error: {e}"

    count = content.count(old_str)
    if count == 0:
        return "✗ old_str not found — check exact whitespace/indentation"
    if count > 1:
        return f"✗ ambiguous: old_str found {count}x — be more specific"

    line_no = content[: content.index(old_str)].count("\n") + 1
    new_content = content.replace(old_str, new_str, 1)

    try:
        path.write_text(new_content)
    except Exception as e:
        return f"✗ write error: {e}"

    return f"✓ patched {path}:{line_no}"
