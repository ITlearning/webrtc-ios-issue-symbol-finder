---
name: webrtc-ios-issue-symbol-finder
description: "Systematically analyze and resolve WebRTC bugs in Obj-C/C++ codebases with iOS SDK priority. Use when a user reports a feature regression, crash, connection issue, media issue, or behavior mismatch and you must follow a fixed flow: (1) define repro/expected/actual behavior, (2) narrow scope with grep on .mm/.h/.cpp, (3) rank root-cause hypotheses, (4) propose validation checks, (5) map change impact, and (6) draft AGENTS.md retrospective notes. Prioritize sdk/objc, pc, api, p2p/base, and media/engine."
---

# WebRTC iOS Issue Symbol Finder

Follow the six sections below in order for every issue.

## 1) Problem Definition

Rewrite the user report into:

- Repro conditions (device/OS/build/environment/timing)
- Expected behavior
- Actual behavior
- Scope guess (audio, capture, render, signaling, ICE, data channel, codec, threading)

If required details are missing, state assumptions explicitly before searching.

## 2) Scope Narrowing (.mm/.h/.cpp Only)

Search only `*.mm`, `*.h`, `*.cpp` first. Focus roots:

- `sdk/objc/` for Obj-C bridge and iOS SDK surface
- `pc/` for PeerConnection core
- `api/` for public headers/interfaces
- `p2p/base/` for ICE and transport
- `media/engine/` for media/codec engine

Run:

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "<symptom text>" \
  --repo-root <webrtc-root>
```

Add explicit symbols when known (stack trace or suspect API):

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "<symptom text>" \
  --symbol RTCAudioSession \
  --symbol OnIceConnectionChange \
  --repo-root <webrtc-root>
```

중점 키워드/심볼을 지정하고 싶으면 `--focus`를 사용:

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "<symptom text>" \
  --focus RTCAudioSession \
  --focus AVAudioSession \
  --repo-root <webrtc-root>
```

질문 문장에 `중점/집중/우선/focus`가 들어가면 스크립트가 자동으로 포커스 후보도 추출해 가중치를 준다.

Output from this step must include:

- Related module list (ranked)
- Related file list (ranked)
- Symbol list (ranked)

## 3) Hypothesis Ranking

Build 2-5 root-cause hypotheses from step 2 evidence. Rank high to low confidence.

For each hypothesis, include:

- Why this is plausible from matches
- Which file/symbol supports it
- One disconfirming signal to check

## 4) Verification Plan

For each hypothesis, propose minimum verification:

- Minimal reproduction steps, or
- Exact code location to inspect (`file + symbol + line intent`)

Prefer low-cost checks first (state transitions, delegate callbacks, configuration paths) before broad instrumentation.

## 5) Change Impact (Blast Radius)

List likely impacted files/modules before editing:

- Directly touched files
- Wrappers/bridges that mirror the same state
- Tests that should be updated or added
- Adjacent modules likely to regress

Use the reference map in `references/webrtc-path-playbook.md`.

## 6) Retrospective Draft for AGENTS.md

After resolution, draft a concise AGENTS.md entry:

```markdown
## <Issue title>
- Date:
- Symptom:
- Repro:
- Root cause:
- Fix summary:
- Verification:
- Impacted modules/files:
- Guardrails for future debugging:
```

Keep this draft short and copy-pastable.

## Install (Codex and Claude Code)

From this repo root:

```bash
bash tools_webrtc/skills/webrtc-ios-issue-symbol-finder/scripts/install_local_skill.sh --target both
```

Optional:

- `--mode copy` to copy files instead of creating symlinks.
- `--force` to replace an existing installation (moves old one to a backup path).
