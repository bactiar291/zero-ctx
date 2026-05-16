import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

MAX_TAIL = 30
MAX_STDERR = 20
MAX_TIMEOUT = 90
KILL_GRACE_SECONDS = 2
MAX_READ_BYTES = 256 * 1024
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def handle(args: dict) -> str:
    cmd = args["cmd"]
    cwd = args.get("cwd", ".")
    requested_timeout = _coerce_timeout(args.get("timeout", 30))
    timeout = min(requested_timeout, MAX_TIMEOUT)
    timeout_note = ""
    if requested_timeout != timeout:
        timeout_note = f"timeout clamped {requested_timeout}s -> {timeout}s"

    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GCM_INTERACTIVE", "Never")
    env.setdefault("PAGER", "cat")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")

    try:
        return _run_with_deadline(cmd, cwd, timeout, env, timeout_note)
    except FileNotFoundError as e:
        return f"✗ not found: {e}"
    except Exception as e:
        return f"✗ {type(e).__name__}: {e}"


def _run_with_deadline(cmd: str, cwd: str, timeout: int, env: dict, timeout_note: str) -> str:
    stdout_path = None
    stderr_path = None
    proc = None

    try:
        with tempfile.NamedTemporaryFile(prefix="zc-run-out-", delete=False) as stdout_f, tempfile.NamedTemporaryFile(
            prefix="zc-run-err-", delete=False
        ) as stderr_f:
            stdout_path = stdout_f.name
            stderr_path = stderr_f.name
            proc = subprocess.Popen(
                cmd,
                shell=True,
                executable="/bin/bash",
                stdin=subprocess.DEVNULL,
                stdout=stdout_f,
                stderr=stderr_f,
                text=False,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )

        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(proc)
            try:
                proc.wait(timeout=KILL_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                _kill_process_group(proc)
                try:
                    proc.wait(timeout=KILL_GRACE_SECONDS)
                except subprocess.TimeoutExpired:
                    pass

        stdout = _read_tail_text(stdout_path, MAX_READ_BYTES)
        stderr = _read_tail_text(stderr_path, MAX_READ_BYTES)

        if timed_out:
            return _format_result(
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                header=f"✗ timeout ({timeout}s), process tree killed",
                notes=[timeout_note],
                stderr_on_success=True,
            )

        return _format_result(
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            notes=[timeout_note],
        )
    finally:
        for path in (stdout_path, stderr_path):
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception:
                    pass


def _coerce_timeout(value) -> int:
    try:
        timeout = int(value)
    except Exception:
        timeout = 30
    return max(1, timeout)


def _terminate_process_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def _kill_process_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _read_tail_text(path: str, max_bytes: int) -> str:
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            if size > max_bytes:
                fh.seek(-max_bytes, os.SEEK_END)
            data = fh.read()
        text = data.decode("utf-8", errors="replace")
        if size > max_bytes:
            text = "[output truncated before tail]\n" + text
        return ANSI_RE.sub("", text)
    except FileNotFoundError:
        return ""


def _format_result(
    exit_code,
    stdout: str,
    stderr: str,
    header: Optional[str] = None,
    notes: Optional[list] = None,
    stderr_on_success: bool = False,
) -> str:
    stdout_lines = stdout.splitlines()
    skipped = max(0, len(stdout_lines) - MAX_TAIL)
    tail = stdout_lines[-MAX_TAIL:]
    stderr = stderr.strip()

    parts = [header if header is not None else f"exit={exit_code}"]
    for note in notes or []:
        if note:
            parts.append(note)
    if skipped:
        parts.append(f"[{skipped} lines skipped]")
    if tail:
        parts.append("\n".join(tail))
    if stderr and (stderr_on_success or exit_code != 0):
        parts.append("stderr:\n" + "\n".join(stderr.splitlines()[-MAX_STDERR:]))

    return "\n".join(parts)
