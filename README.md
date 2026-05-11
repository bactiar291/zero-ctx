<div align="center">

# zero-ctx

**Minimal MCP toolkit for low-token AI coding workflows**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-brightgreen?style=flat-square)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Zero Deps](https://img.shields.io/badge/Dependencies-Zero-success?style=flat-square)]()
[![Token Reduction](https://img.shields.io/badge/Token%20Reduction-70--90%25-blue?style=flat-square)]()

*Give the model less noise and more signal.*

</div>

---
**Zero-dependency MCP server. 10 surgical tools. 90%+ token reduction.**

Pure Python · No Rust · No setup hell · Works anywhere Python 3.9+ runs.

---

## Why

Most AI token waste comes from reading files you don't need, grepping output that's too verbose, or running commands that dump 500 lines of logs.

zero-ctx fixes that. Every tool has hard output caps and returns only what the model needs.

## Tools

| Tool | Function | Estimated Token Savings |
|---|---|---|
| `zc_read` | Surgical file reading (lines/head/tail/around/auto) | ~85% vs full file reads |
| `zc_stat` | File metadata without reading contents | ~99% vs full file reads |
| `zc_grep` | Compact grep with capped matches | ~70% vs raw grep output |
| `zc_find` | Path-only file discovery | ~90% vs raw find output |
| `zc_diff` | Compact git diff with stripped noise | ~60% vs standard git diff |
| `zc_run` | Command execution with compressed output | ~80% vs raw terminal logs |
| `zc_patch` | Surgical string patching inside files | avoids full-file rewrites |
| `zc_write` | Create or overwrite files directly | — |
| `zc_tree` | Compact directory tree generation | ~90% vs verbose directory listings |
| `zc_outline` | Symbol extraction without reading file bodies | ~95% vs full source reads |
---

## Install

```bash
git clone https://github.com/bactiar291/zero-ctx
cd zero-ctx
bash install.sh
```

Or directly:

```bash
pip install git+https://github.com/bactiar291/zero-ctx
```

---

## MCP Config

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zero-ctx": {
      "command": "zero-ctx"
    }
  }
}
```

**Cursor / Windsurf** — `.cursor/mcp.json` or `.windsurf/mcp.json`

```json
{
  "mcpServers": {
    "zero-ctx": {
      "command": "zero-ctx"
    }
  }
}
```

If `zero-ctx` isn't on PATH, use the full path: `python -m zero_ctx.server`

---

## Tools

### `zc_read` — surgical file reader
Read specific ranges instead of full files.

```
mode: auto          → smart 200-line cap, head+tail for large files
mode: head:50       → first 50 lines
mode: tail:30       → last 30 lines
mode: lines:100-150 → exact range
mode: around:87:10  → line 87 ± 10 lines
```

### `zc_grep` — minimal grep
Returns matched lines + N context (default 1). Capped at 50 matches. Auto-skips node_modules, dist, .git, __pycache__, venv.

### `zc_find` — path-only file finder
Returns file paths only, no metadata. Skips junk dirs. Max 100 results.

### `zc_diff` — compact git diff
Strips index lines, whitespace noise, unchanged context. Only shows `+/-` lines and file headers. Cap: 300 lines.

### `zc_run` — compressed command output
Returns `exit=N` + last 30 lines stdout + stderr only on failure. Never streams full output.

### `zc_patch` — surgical string replace
Replace exact string in file. Fails if not found or ambiguous (multiple matches). Safer than full rewrites.

### `zc_write` — create or overwrite file
Create new files or fully overwrite existing ones. Supports append mode. Auto-creates parent dirs.

### `zc_tree` — compact directory tree
Shows folder structure without reading any file content. Default depth 3, max 200 entries.

```
project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md
```

### `zc_outline` — extract symbols without reading file body
**Biggest token saver.** Get all function/class signatures from a file in ~10 lines instead of reading 500 lines.

Supports: Python, JS/TS, Go, Rust.

```
# src/api.py — 8 symbols (312 lines total)
   1  class Router
  15    def get
  22    def post
  31    def delete
  44  class Middleware
  58    def auth
  71    def cors
  89  def create_app
```

---

## Token savings example

**Without zero-ctx:**
- Read 300-line file to find one function → 300 tokens
- Grep with 10-line context → 200 tokens per match
- Run `npm test` → 500 lines output → 500 tokens

**With zero-ctx:**
- `zc_outline` → see all functions in 10 lines → 10 tokens
- `zc_grep` context=1 → 3 lines per match → 30 tokens
- `zc_run npm test` → last 30 lines → 30 tokens

**~90% reduction on typical dev workflows.**

---

## Validate

Test all 10 tools automatically:

```bash
python validate.py
```

Expected output:

```
zero-ctx validate  v2.0.0

  ✓ server handshake  zero-ctx
  ✓ tools/list  10 tools registered

zc_read
  ✓ auto mode (large file)
  ✓ head:5 mode
  ...

done
```

---

## Design principles

- **Caps everywhere.** Every tool has a hard output limit.
- **Fail loud.** Errors return `✗ reason`, never silent failures.
- **Zero deps.** No external packages. Works in any Python 3.9+ environment.
- **Composable.** Use alongside rtk or lean-ctx — different tools, no conflicts.

---

## License

MIT
