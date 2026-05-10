#!/usr/bin/env python3
import sys
import json
import subprocess
import tempfile
import os
import time
from pathlib import Path

_HERE = str(Path(__file__).parent)
SERVER_CMD = [sys.executable, "-c",
              f"import sys; sys.path.insert(0,{_HERE!r}); from zero_ctx.server import main; main()"]
PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
DIM = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"

_id = 0


def _next_id():
    global _id
    _id += 1
    return _id


def rpc(proc, method, params=None):
    req = {"jsonrpc": "2.0", "id": _next_id(), "method": method}
    if params:
        req["params"] = params
    line = json.dumps(req) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()
    out = proc.stdout.readline()
    return json.loads(out)


def call(proc, name, args):
    return rpc(proc, "tools/call", {"name": name, "arguments": args})


def ok(resp):
    if "error" in resp:
        return False, resp["error"].get("message", "unknown error")
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "")
    return True, text


def check(proc, label, name, args, expect=None, not_expect=None):
    try:
        resp = call(proc, name, args)
        passed, text = ok(resp)
        if passed and expect and expect not in text:
            passed, text = False, f"expected {expect!r} in output"
        if passed and not_expect and not_expect in text:
            passed, text = False, f"unexpected {not_expect!r} in output"
        status = PASS if passed else FAIL
        short = text[:80].replace("\n", " ") if not passed else text.split("\n")[0][:80]
        print(f"  {status} {label}{DIM}  {short}{RESET}")
        return passed
    except Exception as e:
        print(f"  {FAIL} {label}{DIM}  exception: {e}{RESET}")
        return False


def main():
    print(f"\n{BOLD}zero-ctx validate{RESET}  v2.0.0\n")

    proc = subprocess.Popen(
        SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    init = rpc(proc, "initialize", {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "validator", "version": "1.0"},
    })
    assert "result" in init, f"initialize failed: {init}"
    server_name = init["result"]["serverInfo"]["name"]
    print(f"  {PASS} server handshake  {DIM}{server_name}{RESET}\n")

    tools_resp = rpc(proc, "tools/list")
    tools = [t["name"] for t in tools_resp["result"]["tools"]]
    expected = ["zc_read", "zc_grep", "zc_find", "zc_diff",
                "zc_run", "zc_patch", "zc_write", "zc_tree", "zc_outline"]
    missing = [t for t in expected if t not in tools]
    if missing:
        print(f"  {FAIL} tools/list  {DIM}missing: {missing}{RESET}")
    else:
        print(f"  {PASS} tools/list  {DIM}{len(tools)} tools registered{RESET}")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        tf = os.path.join(tmp, "sample.py")
        Path(tf).write_text(
            "class Foo:\n"
            "    def bar(self):\n"
            "        return 42\n\n"
            "def baz(x, y):\n"
            "    return x + y\n"
            + "x = 1\n" * 250
        )

        print(f"{BOLD}zc_read{RESET}")
        check(proc, "auto mode (large file)", "zc_read", {"path": tf}, expect="lines skipped")
        check(proc, "head:5 mode", "zc_read", {"path": tf, "mode": "head:5"}, expect="Foo")
        check(proc, "lines:1-3", "zc_read", {"path": tf, "mode": "lines:1-3"}, expect="class Foo")
        check(proc, "around:5:2", "zc_read", {"path": tf, "mode": "around:5:2"}, expect="def baz")
        check(proc, "missing file", "zc_read", {"path": "/nonexistent/x.py"}, expect="✗")
        print()

        print(f"{BOLD}zc_grep{RESET}")
        check(proc, "find def", "zc_grep", {"pattern": "def", "path": tf}, expect="def")
        check(proc, "no match", "zc_grep", {"pattern": "ZZZNOMATCH", "path": tf}, expect="∅")
        check(proc, "regex pattern", "zc_grep", {"pattern": r"def \w+", "path": tf}, expect="def")
        print()

        print(f"{BOLD}zc_find{RESET}")
        check(proc, "find *.py", "zc_find", {"pattern": "*.py", "path": tmp}, expect="sample.py")
        check(proc, "find *.rs (none)", "zc_find", {"pattern": "*.rs", "path": tmp}, expect="∅")
        print()

        print(f"{BOLD}zc_run{RESET}")
        check(proc, "echo hello", "zc_run", {"cmd": "echo hello"}, expect="hello")
        check(proc, "exit code capture", "zc_run", {"cmd": "sh -c 'exit 1'"}, expect="exit=1")
        check(proc, "timeout", "zc_run", {"cmd": "sleep 10", "timeout": 1}, expect="✗")
        print()

        wf = os.path.join(tmp, "target.txt")
        Path(wf).write_text("hello world\nfoo bar\n")

        print(f"{BOLD}zc_patch{RESET}")
        check(proc, "exact replace", "zc_patch",
              {"path": wf, "old_str": "hello world", "new_str": "hi earth"}, expect="✓")
        check(proc, "not found", "zc_patch",
              {"path": wf, "old_str": "MISSING", "new_str": "x"}, expect="✗")
        print()

        print(f"{BOLD}zc_write{RESET}")
        nf = os.path.join(tmp, "new_file.txt")
        check(proc, "create file", "zc_write", {"path": nf, "content": "test content"}, expect="✓")
        assert Path(nf).read_text() == "test content"
        check(proc, "append mode", "zc_write",
              {"path": nf, "content": "\nmore", "append": True}, expect="✓")
        assert "more" in Path(nf).read_text()
        check(proc, "nested dirs", "zc_write",
              {"path": os.path.join(tmp, "a/b/c.txt"), "content": "deep"}, expect="✓")
        print()

        print(f"{BOLD}zc_tree{RESET}")
        check(proc, "tree output", "zc_tree", {"path": tmp}, expect="sample.py")
        check(proc, "depth 1", "zc_tree", {"path": tmp, "depth": 1})
        check(proc, "missing path", "zc_tree", {"path": "/nonexistent"}, expect="✗")
        print()

        print(f"{BOLD}zc_outline{RESET}")
        check(proc, "python outline", "zc_outline", {"path": tf}, expect="class Foo")
        check(proc, "shows def baz", "zc_outline", {"path": tf}, expect="def baz")
        check(proc, "shows symbol count", "zc_outline", {"path": tf}, expect="symbols")
        check(proc, "unsupported ext", "zc_outline",
              {"path": os.path.join(tmp, "x.unknown")}, expect="✗")
        print()

        print(f"{BOLD}zc_diff{RESET}")
        check(proc, "no git repo (graceful)", "zc_diff", {"path": tmp})
        print()

    proc.stdin.close()
    proc.wait(timeout=3)

    print(f"{BOLD}done{RESET}\n")


if __name__ == "__main__":
    main()
