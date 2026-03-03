# webrtc-ios-issue-symbol-finder

WebRTC iOS issue triage skill for Obj-C/C++ codebases.

## Quick Install (Codex + Claude Code)

From this repository root:

```bash
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target both
```

## Install Options

```bash
# Codex only
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target codex

# Claude Code only
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target claude

# Replace existing installation (creates backup path with .bak.<timestamp>)
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target both --force

# Copy files instead of symlink
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target both --mode copy
```

## Verify

```bash
ls -la ~/.codex/skills/webrtc-ios-issue-symbol-finder
ls -la ~/.claude/skills/webrtc-ios-issue-symbol-finder
```
