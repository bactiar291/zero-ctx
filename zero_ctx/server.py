#!/usr/bin/env python3
import sys
import json
from zero_ctx.tools import read, grep, find, diff, run, patch, write, tree, outline, stat

TOOLS = [
    {
        "name": "zc_read",
        "description": (
            "Read file. Modes: auto (smart 200L cap), lines:N-M, head:N, tail:N, around:N:CTX. "
            "Returns only needed portion — never full file unless forced."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "mode": {"type": "string", "default": "auto"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "zc_grep",
        "description": (
            "Regex grep. Returns matched lines + N context. "
            "Auto-skips: node_modules, dist, __pycache__, .git, venv. Capped at 50 matches."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "recursive": {"type": "boolean", "default": True},
                "context": {"type": "integer", "default": 1},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "zc_find",
        "description": (
            "Find files by glob pattern. Returns paths only. "
            "Auto-skips junk dirs. Max 100 results."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "type": {"type": "string", "enum": ["f", "d", "any"], "default": "f"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "zc_diff",
        "description": (
            "Compact git diff. Only +/- lines + file headers. "
            "Strips whitespace noise and index lines. Cap 300 lines."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "staged": {"type": "boolean", "default": False},
                "file": {"type": "string", "default": ""},
            },
        },
    },
    {
        "name": "zc_run",
        "description": (
            "Run shell command. Returns exit_code + last 30 lines stdout + stderr on error. "
            "Never streams — always summarizes. Default timeout 30s."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string"},
                "cwd": {"type": "string", "default": "."},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["cmd"],
        },
    },
    {
        "name": "zc_patch",
        "description": (
            "Surgical string replace in file. "
            "Fails if old_str not found or matches >1 place. Returns line number changed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_str": {"type": "string"},
                "new_str": {"type": "string"},
            },
            "required": ["path", "old_str", "new_str"],
        },
    },
    {
        "name": "zc_write",
        "description": (
            "Create or overwrite a file with content. "
            "Use for new files or full rewrites. Returns bytes written."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "append": {"type": "boolean", "default": False},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "zc_tree",
        "description": (
            "Compact directory tree. Shows structure without reading file contents. "
            "Auto-skips junk dirs. Default depth 3, max 200 entries."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."},
                "depth": {"type": "integer", "default": 3},
                "show_hidden": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "zc_stat",
        "description": (
            "File/dir metadata only: size, line count, mtime. "
            "Use before zc_read to check if file worth reading. Zero content read."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "zc_outline",
        "description": (
            "Extract function/class signatures from source file — no body. "
            "Supports: Python, JS/TS, Go, Rust. Use instead of reading full file to understand structure."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
]

HANDLERS = {
    "zc_read": read.handle,
    "zc_grep": grep.handle,
    "zc_find": find.handle,
    "zc_diff": diff.handle,
    "zc_run": run.handle,
    "zc_patch": patch.handle,
    "zc_write": write.handle,
    "zc_tree": tree.handle,
    "zc_stat": stat.handle,
    "zc_outline": outline.handle,
}


def respond(rid, result=None, error=None):
    if error:
        obj = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": error}}
    else:
        obj = {"jsonrpc": "2.0", "id": rid, "result": result}
    print(json.dumps(obj), flush=True)


def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            continue

        rid = req.get("id")
        method = req.get("method", "")

        if method == "initialize":
            respond(rid, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "zero-ctx", "version": "2.0.0"},
            })
        elif method == "tools/list":
            respond(rid, {"tools": TOOLS})
        elif method == "tools/call":
            name = req.get("params", {}).get("name", "")
            args = req.get("params", {}).get("arguments", {})
            handler = HANDLERS.get(name)
            if not handler:
                respond(rid, error=f"unknown tool: {name}")
                continue
            try:
                result = handler(args)
                respond(rid, {"content": [{"type": "text", "text": result}]})
            except Exception as e:
                respond(rid, error=f"{type(e).__name__}: {e}")
        elif method in ("notifications/initialized", "notifications/cancelled"):
            pass
        else:
            respond(rid, error=f"method not found: {method}")
