import subprocess
import shlex
import re

MAX_TAIL = 30
MAX_STDERR = 20
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def handle(args: dict) -> str:
    cmd = args["cmd"]
    cwd = args.get("cwd", ".")
    timeout = args.get("timeout", 30)

    try:
        r = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"✗ timeout ({timeout}s): {cmd}"
    except FileNotFoundError as e:
        return f"✗ not found: {e}"
    except Exception as e:
        return f"✗ {type(e).__name__}: {e}"

    stdout = ANSI_RE.sub("", r.stdout)
    stderr = ANSI_RE.sub("", r.stderr)

    stdout_lines = stdout.splitlines()
    skipped = max(0, len(stdout_lines) - MAX_TAIL)
    tail = stdout_lines[-MAX_TAIL:]
    stderr = stderr.strip()

    parts = [f"exit={r.returncode}"]
    if skipped:
        parts.append(f"[{skipped} lines skipped]")
    if tail:
        parts.append("\n".join(tail))
    if stderr and r.returncode != 0:
        parts.append("stderr:\n" + "\n".join(stderr.splitlines()[-MAX_STDERR:]))

    return "\n".join(parts)
