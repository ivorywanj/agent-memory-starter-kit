#!/bin/sh
set -eu

REPO_URL="${JOURNEYMEM_REPO_URL:-https://github.com/ivorywanj/agent-memory-starter-kit.git}"
HOME_DIR="${JOURNEYMEM_HOME:-$HOME}"
PACKAGE_DIR="${JOURNEYMEM_PACKAGE_DIR:-$HOME_DIR/.journeymem/starter-kit}"
WORKSPACE="${JOURNEYMEM_WORKSPACE:-$(pwd)}"
AGENT="${JOURNEYMEM_AGENT:-auto}"
FORCE="${JOURNEYMEM_FORCE:-0}"

echo "Installing JourneyMem"

mkdir -p "$HOME_DIR/.journeymem" "$HOME_DIR/.local/bin"

if ! command -v python3 >/dev/null 2>&1; then
  echo "install_blocked: python3 is required"
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -f "$SCRIPT_DIR/scripts/memory" ] && [ -f "$SCRIPT_DIR/scripts/memory_runtime.py" ]; then
  LOCAL_SOURCE="$SCRIPT_DIR"
  if [ -f "$SCRIPT_DIR/public-export/scripts/memory" ] && [ -f "$SCRIPT_DIR/public-export/scripts/memory_runtime.py" ]; then
    LOCAL_SOURCE="$SCRIPT_DIR/public-export"
  fi
  python3 - "$LOCAL_SOURCE" "$PACKAGE_DIR" <<'PY'
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).expanduser().resolve()
if source != target:
    if target.exists():
        is_package = (target / "scripts/memory").exists() and (target / "scripts/memory_runtime.py").exists()
        if is_package:
            shutil.rmtree(target)
        elif any(target.iterdir()):
            raise SystemExit("install_blocked: package dir exists but is not JourneyMem")
    ignore = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "public-export",
        ".DS_Store",
    )
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)
PY
  SOURCE_DIR="$PACKAGE_DIR"
else
  if ! command -v git >/dev/null 2>&1; then
    echo "install_blocked: git is required when install.sh is not run from a cloned JourneyMem repository"
    exit 1
  fi
  if [ -d "$PACKAGE_DIR/.git" ]; then
    git -C "$PACKAGE_DIR" pull --ff-only
  else
    python3 - "$PACKAGE_DIR" <<'PY'
from pathlib import Path
import shutil
import sys

target = Path(sys.argv[1]).expanduser().resolve()
if target.exists():
    is_package = (target / "scripts/memory").exists() and (target / "scripts/memory_runtime.py").exists()
    if is_package:
        shutil.rmtree(target)
    elif any(target.iterdir()):
        raise SystemExit("install_blocked: package dir exists but is not JourneyMem")
PY
    mkdir -p "$(dirname "$PACKAGE_DIR")"
    git clone "$REPO_URL" "$PACKAGE_DIR"
  fi
  SOURCE_DIR="$PACKAGE_DIR"
fi

REGISTRY="$HOME_DIR/.journeymem/registry.json"
if [ ! -f "$REGISTRY" ]; then
  printf '{\n  "agents": {},\n  "default_library": null,\n  "libraries": [],\n  "version": 1\n}\n' > "$REGISTRY"
fi

if [ "$FORCE" = "1" ]; then
  python3 "$SOURCE_DIR/scripts/memory" install --agent "$AGENT" --workspace "$WORKSPACE" --home "$HOME_DIR" --force
else
  python3 "$SOURCE_DIR/scripts/memory" install --agent "$AGENT" --workspace "$WORKSPACE" --home "$HOME_DIR"
fi

echo ""
echo "JourneyMem installed"
echo "Start now:"
echo "  $HOME_DIR/.local/bin/memory"
echo ""
echo "If your shell already has $HOME_DIR/.local/bin on PATH, you can also type:"
echo "  memory"
echo ""
echo "If memory is not found in this terminal, run:"
echo "  export PATH=\"$HOME_DIR/.local/bin:\$PATH\""
echo ""
echo "What do you want to do?"
echo "1. memory new - Create a memory library"
echo "2. memory connect - Connect this Agent to an existing memory library"
echo ""
echo "Other command:"
echo "- memory backup - Back up a memory library"
