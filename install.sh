#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pip install -e "$REPO_DIR" --quiet

echo ""
echo "✓ zero-ctx installed"
echo ""
echo "Add to your MCP config (Claude / Cursor / Windsurf):"
echo ""
echo '  "zero-ctx": {'
echo '    "command": "zero-ctx"'
echo '  }'
echo ""
echo "Validate:"
echo "  python validate.py"
