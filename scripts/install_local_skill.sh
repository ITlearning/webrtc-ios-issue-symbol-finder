#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="webrtc-ios-issue-symbol-finder"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="both"
MODE="symlink"
FORCE=0

usage() {
  cat <<'EOF'
Install webrtc-ios-issue-symbol-finder into Codex and/or Claude Code.

Usage:
  install_local_skill.sh [--target codex|claude|both] [--mode symlink|copy] [--force] [--source <dir>]

Options:
  --target  Installation target. Default: both
  --mode    symlink (default) or copy
  --force   Replace existing installation (old directory is moved to backup)
  --source  Skill directory path that contains SKILL.md
  -h, --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --source)
      SOURCE_DIR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$TARGET" in
  codex|claude|both) ;;
  *)
    echo "Invalid --target: $TARGET" >&2
    exit 1
    ;;
esac

case "$MODE" in
  symlink|copy) ;;
  *)
    echo "Invalid --mode: $MODE" >&2
    exit 1
    ;;
esac

if [[ ! -f "$SOURCE_DIR/SKILL.md" ]]; then
  echo "SKILL.md not found in source: $SOURCE_DIR" >&2
  exit 1
fi

install_one() {
  local tool_home="$1"
  local label="$2"
  local skill_root="$tool_home/skills"
  local dst="$skill_root/$SKILL_NAME"
  local ts
  local backup

  mkdir -p "$skill_root"

  if [[ -L "$dst" || -e "$dst" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      ts="$(date +%Y%m%d%H%M%S)"
      backup="${dst}.bak.${ts}"
      mv "$dst" "$backup"
      echo "[$label] Existing installation moved to: $backup"
    else
      echo "[$label] Already exists: $dst"
      echo "[$label] Use --force to replace."
      return
    fi
  fi

  if [[ "$MODE" == "symlink" ]]; then
    ln -s "$SOURCE_DIR" "$dst"
  else
    cp -R "$SOURCE_DIR" "$dst"
  fi

  echo "[$label] Installed at: $dst ($MODE)"
}

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

if [[ "$TARGET" == "codex" || "$TARGET" == "both" ]]; then
  install_one "$CODEX_HOME" "Codex"
fi

if [[ "$TARGET" == "claude" || "$TARGET" == "both" ]]; then
  install_one "$CLAUDE_HOME" "Claude Code"
fi

echo "Done. Restart Codex/Claude Code to pick up the new skill."
