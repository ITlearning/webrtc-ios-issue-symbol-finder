# webrtc-ios-issue-symbol-finder

Structured WebRTC iOS issue triage skill for Obj-C/C++ codebases.

- [한국어](#한국어)
- [English](#english)

## 한국어

Obj-C/C++ 기반 WebRTC 코드베이스에서 iOS 이슈를 체계적으로 분석하기 위한 스킬입니다.

### 왜 만들었나요

iOS WebRTC 회귀(regression) 이슈는 아래 이유로 디버깅이 느려지기 쉽습니다.

- 증상 보고가 모호함 (예: "오디오가 깨져요", "콜이 멈춰요")
- 코드 표면이 넓음 (`sdk/objc`, `pc`, `api`, `p2p/base`, `media/engine`)
- 이슈 분석 방식이 사람/상황마다 달라 품질 편차가 큼

이 스킬은 문제 정의부터 회고까지 6단계 흐름을 강제해, 분석 품질을 재현 가능하게 만듭니다.

### 포함 구성

- `SKILL.md`: 에이전트용 고정 이슈 분석 워크플로우
- `scripts/find_webrtc_issue_scope.py`: 증상 텍스트 기준 관련 모듈/파일/심볼 랭킹
- `references/webrtc-path-playbook.md`: 영향 범위(Blast Radius) 확인용 경로 가이드
- `scripts/install_local_skill.sh`: Codex/Claude Code 설치 스크립트

### 빠른 설치 (Codex + Claude Code)

저장소 루트에서 실행:

```bash
bash scripts/install_local_skill.sh --target both
```

설치 후 Codex/Claude Code를 재시작하세요.

### 설치 옵션

```bash
# Codex만 설치
bash scripts/install_local_skill.sh --target codex

# Claude Code만 설치
bash scripts/install_local_skill.sh --target claude

# 기존 설치 교체 (기존 경로는 .bak.<timestamp>로 백업)
bash scripts/install_local_skill.sh --target both --force

# 심볼릭 링크 대신 복사 방식 설치
bash scripts/install_local_skill.sh --target both --mode copy
```

### 기본 사용법

에이전트에게 "재현 조건 + 기대 동작 + 실제 동작"을 포함해 이슈 분석을 요청하세요.

예시:

```text
iOS 17에서 통화 중 블루투스를 재연결하면 송신 오디오가 끊깁니다.
Expected: 2초 내 오디오 복구
Actual: 앱 재시작 전까지 상대방이 무음으로 들음
webrtc-ios-issue-symbol-finder로 분석해줘.
```

스킬은 아래 6단계로 진행합니다.

1. 문제 정의
2. 범위 축소 (`*.mm`, `*.h`, `*.cpp`)
3. 가설 우선순위화
4. 검증 계획
5. 변경 영향도 점검
6. `AGENTS.md` 회고 초안 작성

### 수동 범위 검색 (선택)

직접 스크립트를 실행할 수도 있습니다.

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "Audio drops after Bluetooth reconnect on iOS" \
  --repo-root /path/to/webrtc/src
```

심볼을 명시하는 경우:

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "ICE state mismatch after network handoff" \
  --symbol RTCAudioSession \
  --symbol OnIceConnectionChange \
  --repo-root /path/to/webrtc/src
```

### 설치 확인

```bash
ls -la ~/.codex/skills/webrtc-ios-issue-symbol-finder
ls -la ~/.claude/skills/webrtc-ios-issue-symbol-finder
```

### 기여

PR 환영합니다.

권장 기여 흐름:

1. 이슈 또는 PR 초안에 재현 절차/기대 동작/실제 동작을 명확히 작성
2. 변경 범위를 작게 유지 (워크플로우, 랭킹 로직, 레퍼런스, 설치 UX)
3. 동작 변경 시 `README.md`, `SKILL.md`, 레퍼런스 문서 함께 업데이트
4. PR에 before/after 예시를 포함해 검증 가능성 확보

첫 기여 아이디어:

- `find_webrtc_issue_scope.py`의 query-심볼 매칭 개선
- `references/` 내 iOS 특화 디버깅 체크리스트 보강
- 로컬 설치/검증 UX 단순화

## English

Structured WebRTC iOS issue triage skill for Obj-C/C++ codebases.

### Why This Exists

Debugging WebRTC regressions on iOS is often slow because:

- symptoms are reported vaguely ("audio broke", "call stuck", "random crash")
- the code surface is large across `sdk/objc`, `pc`, `api`, `p2p/base`, and `media/engine`
- issue analysis quality varies by engineer and by day

This skill enforces a repeatable six-step flow from problem definition to retrospective notes.

### What You Get

- `SKILL.md`: fixed issue-analysis workflow for agents
- `scripts/find_webrtc_issue_scope.py`: ranks related modules/files/symbols from symptom text
- `references/webrtc-path-playbook.md`: path map for likely impact and blast-radius checks
- `scripts/install_local_skill.sh`: install helper for Codex and Claude Code

### Quick Install (Codex + Claude Code)

From this repository root:

```bash
bash scripts/install_local_skill.sh --target both
```

Restart Codex and/or Claude Code after installation.

### Install Options

```bash
# Codex only
bash scripts/install_local_skill.sh --target codex

# Claude Code only
bash scripts/install_local_skill.sh --target claude

# Replace existing installation (creates backup path with .bak.<timestamp>)
bash scripts/install_local_skill.sh --target both --force

# Copy files instead of symlink
bash scripts/install_local_skill.sh --target both --mode copy
```

### Basic Usage

Ask your agent to investigate a WebRTC issue with concrete expected vs actual behavior.

Example:

```text
On iOS 17, outgoing audio stops after reconnecting Bluetooth during an active call.
Expected: audio resumes within 2 seconds.
Actual: remote side hears silence until app restart.
Please analyze with webrtc-ios-issue-symbol-finder.
```

The skill will run a fixed flow:

1. Problem definition
2. Scope narrowing (`*.mm`, `*.h`, `*.cpp`)
3. Hypothesis ranking
4. Verification plan
5. Change impact review
6. Retrospective draft for `AGENTS.md`

### Manual Scope Search (Optional)

You can run the scope helper directly:

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "Audio drops after Bluetooth reconnect on iOS" \
  --repo-root /path/to/webrtc/src
```

With explicit symbols:

```bash
python3 scripts/find_webrtc_issue_scope.py \
  --query "ICE state mismatch after network handoff" \
  --symbol RTCAudioSession \
  --symbol OnIceConnectionChange \
  --repo-root /path/to/webrtc/src
```

### Verify Installation

```bash
ls -la ~/.codex/skills/webrtc-ios-issue-symbol-finder
ls -la ~/.claude/skills/webrtc-ios-issue-symbol-finder
```

### Contributing

PRs are welcome.

Suggested contribution flow:

1. Open an issue (or draft in PR) with repro steps, expected behavior, and actual behavior.
2. Keep changes focused (workflow, ranking logic, references, or install path improvements).
3. Update docs (`README.md`, `SKILL.md`, and references) when behavior changes.
4. Submit a PR with before/after examples so reviewers can verify impact quickly.

Good first PR ideas:

- better query-to-symbol matching in `find_webrtc_issue_scope.py`
- clearer iOS-specific debug checklists in `references/`
- tighter install/verify UX for local skill development
