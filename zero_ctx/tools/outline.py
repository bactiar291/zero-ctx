import re
from pathlib import Path

_PY_DEF = re.compile(r"^(\s*)(async\s+)?(def|class)\s+(\w+)[^:]*:")
_GO_FN = re.compile(r"^func\s+(\(.*?\)\s+)?(\w+)\s*\(")
_RUST_FN = re.compile(
    r"^\s*(pub\s+)?(async\s+)?fn\s+(\w+)"
    r"|^\s*(pub\s+)?struct\s+(\w+)"
    r"|^\s*(pub\s+)?enum\s+(\w+)"
    r"|^\s*(pub\s+)?trait\s+(\w+)"
)

# JS/TS patterns — comprehensive
_JS_PATTERNS = [
    # function declaration
    (re.compile(r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\*?\s+(\w+)\s*\("), "fn"),
    # class declaration
    (re.compile(r"^(?:export\s+)?(?:default\s+)?class\s+(\w+)"), "class"),
    # const/let/var arrow or function
    (re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\()"), "fn"),
    # const arrow: name = (args) => or name = async args =>
    (re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\w+\s*=>"), "fn"),
    # export default async function / export default function
    (re.compile(r"^export\s+default\s+(?:async\s+)?function\s*(\w*)"), "fn"),
    # object/class method shorthand: methodName( or async methodName(
    (re.compile(r"^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{"), "method"),
    # TypeScript interface/type
    (re.compile(r"^(?:export\s+)?(?:interface|type)\s+(\w+)"), "type"),
]


def handle(args: dict) -> str:
    path = Path(args["path"]).expanduser()

    if not path.exists():
        return f"✗ not found: {path}"
    if not path.is_file():
        return f"✗ not a file: {path}"

    try:
        text = path.read_text(errors="replace")
    except Exception as e:
        return f"✗ read error: {e}"

    lines = text.splitlines()
    total = len(lines)
    suffix = path.suffix.lower()

    if suffix == ".py":
        results = _outline_python(lines)
    elif suffix in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
        results = _outline_js(lines)
    elif suffix == ".go":
        results = _outline_go(lines)
    elif suffix == ".rs":
        results = _outline_rust(lines)
    else:
        return f"✗ unsupported: {suffix} (supported: .py .js .ts .go .rs)"

    if not results:
        return f"∅ no symbols in {path}"

    header = f"# {path} — {len(results)} symbols ({total} lines)\n"
    return header + "\n".join(results)


def _outline_python(lines):
    out = []
    for i, line in enumerate(lines, 1):
        m = _PY_DEF.match(line)
        if m:
            indent = len(m.group(1))
            kind = m.group(3)
            name = m.group(4)
            prefix = "  " * (indent // 4)
            out.append(f"{i:4d}  {prefix}{'class' if kind == 'class' else 'def'} {name}")
    return out


def _outline_js(lines):
    out = []
    seen = set()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue
        for pattern, kind in _JS_PATTERNS:
            m = pattern.match(line)
            if m:
                name = m.group(1) or "(anonymous)"
                if name and name not in ("if", "for", "while", "switch", "catch"):
                    key = f"{i}:{name}"
                    if key not in seen:
                        seen.add(key)
                        out.append(f"{i:4d}  {kind} {name}")
                break
    return out


def _outline_go(lines):
    out = []
    for i, line in enumerate(lines, 1):
        m = _GO_FN.match(line)
        if m:
            receiver = m.group(1) or ""
            name = m.group(2)
            recv_str = f"({receiver.strip()}) " if receiver.strip() else ""
            out.append(f"{i:4d}  func {recv_str}{name}()")
    return out


def _outline_rust(lines):
    out = []
    for i, line in enumerate(lines, 1):
        m = _RUST_FN.match(line)
        if m:
            fn_name = m.group(3) or m.group(5) or m.group(7) or m.group(9)
            if m.group(3):
                kind = "fn"
            elif m.group(5):
                kind = "struct"
            elif m.group(7):
                kind = "enum"
            else:
                kind = "trait"
            pub = "pub " if any([m.group(1), m.group(4), m.group(6), m.group(8)]) else ""
            out.append(f"{i:4d}  {pub}{kind} {fn_name}")
    return out
