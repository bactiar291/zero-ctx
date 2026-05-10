from pathlib import Path


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    content = args["content"]
    append = args.get("append", False)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        size = path.stat().st_size
        action = "appended" if append else "written"
        return f"✓ {action} {path} ({size} bytes)"
    except Exception as e:
        return f"✗ write error: {e}"
