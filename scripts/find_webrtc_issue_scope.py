#!/usr/bin/env python3
"""Rank likely WebRTC files/modules/symbols for a bug description."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_ROOTS = ["sdk/objc", "pc", "api", "p2p/base", "media/engine"]
EXT_GLOBS = ["*.mm", "*.h", "*.cpp"]
FOCUS_CUES = ["focus", "prioritize", "priority", "중점", "집중", "우선"]
STOP_QUERY_TOKENS = {
    "webrtc",
    "issue",
    "bug",
    "problem",
    "after",
    "before",
    "during",
    "with",
    "without",
    "from",
    "this",
    "that",
    "when",
    "then",
    "into",
    "onto",
    "i",
    "you",
    "they",
    "ios",
    "android",
}

MODULE_WEIGHTS = [
    ("sdk/objc", 5.0),
    ("pc", 4.4),
    ("p2p/base", 4.0),
    ("media/engine", 3.6),
    ("api", 3.2),
]

CATEGORY_KEYWORDS = {
    "audio": [
        "audio",
        "mic",
        "microphone",
        "speaker",
        "route",
        "interruption",
        "callkit",
        "bluetooth",
        "mute",
        "avaudiosession",
        "오디오",
        "마이크",
        "스피커",
        "라우트",
        "인터럽션",
        "콜킷",
        "블루투스",
        "음소거",
    ],
    "capture": [
        "camera",
        "capture",
        "fps",
        "orientation",
        "rotation",
        "front",
        "rear",
        "카메라",
        "캡처",
        "회전",
        "프레임",
    ],
    "render": [
        "render",
        "renderer",
        "metal",
        "eagl",
        "opengl",
        "pixelbuffer",
        "blank",
        "black screen",
        "렌더",
        "검은",
    ],
    "ice": [
        "ice",
        "candidate",
        "turn",
        "stun",
        "dtls",
        "disconnect",
        "reconnect",
        "network",
        "offer",
        "answer",
        "sdp",
        "연결",
        "끊김",
        "재연결",
        "후보",
    ],
    "datachannel": ["datachannel", "sctp", "ordered", "unreliable", "데이터채널"],
    "codec": [
        "codec",
        "encoder",
        "decoder",
        "h264",
        "vp8",
        "vp9",
        "av1",
        "코덱",
        "인코더",
        "디코더",
    ],
    "threading": [
        "thread",
        "deadlock",
        "race",
        "queue",
        "dispatch",
        "assert",
        "lock",
        "스레드",
        "데드락",
        "경합",
    ],
}

CATEGORY_SYMBOLS = {
    "audio": [
        "RTCAudioSession",
        "AVAudioSession",
        "audioSessionDid",
        "audio_device_ios",
        "voice_processing_audio_unit",
    ],
    "capture": [
        "RTCCameraVideoCapturer",
        "AVCaptureSession",
        "RTCDispatcherTypeCaptureSession",
        "UIDevice",
    ],
    "render": [
        "RTCMTLVideoView",
        "RTCEAGLVideoView",
        "RTCCVPixelBuffer",
        "objc_video_renderer",
    ],
    "ice": [
        "RTCPeerConnection",
        "RTCIceCandidate",
        "RTCIceServer",
        "OnIceConnectionChange",
        "PeerConnectionInterface",
        "jsep_transport",
    ],
    "datachannel": [
        "RTCDataChannel",
        "DataChannelInterface",
        "sctp_data_channel",
        "RTCPeerConnection+DataChannel",
    ],
    "codec": ["VideoEncoder", "VideoDecoder", "H264", "VP8", "VP9", "AV1"],
    "threading": ["RTCDispatcher", "rtc::Thread", "NSAssert", "lockForConfiguration"],
}

CATEGORY_PATH_BOOSTS = {
    "audio": ["sdk/objc/components/audio", "sdk/objc/native/src/audio"],
    "capture": ["sdk/objc/components/capturer", "sdk/objc/helpers"],
    "render": [
        "sdk/objc/components/renderer/metal",
        "sdk/objc/components/renderer/opengl",
        "sdk/objc/native/src/objc_video_renderer",
    ],
    "ice": ["pc", "p2p/base", "sdk/objc/api/peerconnection"],
    "datachannel": ["pc/data_channel", "pc/sctp", "sdk/objc/api/peerconnection"],
    "codec": ["media/engine", "sdk/objc/components/video_codec"],
    "threading": ["sdk/objc/helpers", "sdk/objc/components/audio", "pc"],
}

BASE_SYMBOLS = [
    "RTCPeerConnection",
    "RTCConfiguration",
    "RTCAudioSession",
    "RTCCameraVideoCapturer",
    "RTCMTLVideoView",
    "RTCEAGLVideoView",
    "RTCDataChannel",
    "RTCIceCandidate",
]

SYMBOL_RE = re.compile(
    r"(RTC[A-Za-z0-9_:+]+|AVAudioSession[A-Za-z0-9_]*|"
    r"PeerConnectionInterface::[A-Za-z0-9_]+|DataChannelInterface|"
    r"audioSessionDid[A-Za-z0-9_]+|OnIceConnectionChange|"
    r"voice_processing_audio_unit|audio_device_ios|jsep_transport)"
)

STOP_SYMBOLS = {
    "RTC_OBJC_TYPE",
    "RTCLog",
    "RTCLogError",
    "RTCDCHECK",
    "RTC_CHECK",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find and rank candidate files/symbols for WebRTC issues."
    )
    parser.add_argument("--query", required=True, help="Issue description text.")
    parser.add_argument(
        "--repo-root", default=".", help="Path to the WebRTC repository root."
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="Additional search root (repeatable).",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        default=[],
        help="Known symbol hint (repeatable; comma-separated also accepted).",
    )
    parser.add_argument(
        "--focus",
        action="append",
        default=[],
        help="Priority keyword/symbol to boost in ranking (repeatable; comma-separated allowed).",
    )
    parser.add_argument("--max-files", type=int, default=15)
    parser.add_argument("--max-symbols", type=int, default=20)
    parser.add_argument("--show-lines", type=int, default=2)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def detect_categories(query: str) -> list[str]:
    q = query.lower()
    categories: list[str] = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in q for keyword in keywords):
            categories.append(category)
    return categories


def extract_query_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_:+.-]{3,}", query)
    unique: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        lowered = token.lower()
        if lowered in seen or lowered in STOP_QUERY_TOKENS:
            continue
        seen.add(lowered)
        unique.append(token)
    return unique


def parse_csv_args(raw_values: list[str]) -> list[str]:
    result: list[str] = []
    for raw in raw_values:
        for part in raw.split(","):
            value = part.strip()
            if value:
                result.append(value)
    return result


def infer_focus_terms(query: str) -> list[str]:
    lowered_query = query.lower()
    if not any(cue in lowered_query for cue in FOCUS_CUES):
        return []

    # Prefer explicit code-like tokens when user asks to focus.
    raw_terms = re.findall(
        r"(RTC[A-Za-z0-9_:+]+|AVAudioSession[A-Za-z0-9_]*|"
        r"[A-Z][A-Za-z0-9_:+]{4,}|[A-Za-z0-9_:+.-]{4,})",
        query,
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        lowered = term.lower()
        if lowered in seen or lowered in STOP_QUERY_TOKENS:
            continue
        seen.add(lowered)
        deduped.append(term)
    return deduped[:8]


def existing_roots(repo_root: Path, extra_roots: list[str]) -> list[str]:
    roots: list[str] = []
    for root in DEFAULT_ROOTS + extra_roots:
        if (repo_root / root).exists():
            roots.append(root)
    return roots


def module_for_path(path: str) -> str:
    if path.startswith("sdk/objc/"):
        return "sdk/objc"
    if path.startswith("p2p/base/"):
        return "p2p/base"
    if path.startswith("media/engine/"):
        return "media/engine"
    if path.startswith("pc/"):
        return "pc"
    if path.startswith("api/"):
        return "api"
    return path.split("/", 1)[0]


def module_weight(path: str) -> float:
    for prefix, weight in MODULE_WEIGHTS:
        if path.startswith(prefix):
            return weight
    return 1.0


def category_path_boost(path: str, categories: list[str]) -> float:
    boost = 0.0
    for category in categories:
        for prefix in CATEGORY_PATH_BOOSTS.get(category, []):
            if path.startswith(prefix):
                boost += 0.8
                break
    return boost


def extract_symbols(text: str) -> list[str]:
    symbols = []
    for match in SYMBOL_RE.findall(text):
        symbol = match.strip("[](){}<>,;:.")
        if not symbol or symbol in STOP_SYMBOLS:
            continue
        symbols.append(symbol)
    return symbols


def build_search_terms(
    query: str,
    categories: list[str],
    query_tokens: list[str],
    symbols: list[str],
    focus_terms: list[str],
) -> list[str]:
    terms: list[str] = []
    terms.extend(query_tokens)
    terms.extend(symbols)
    terms.extend(focus_terms)
    if categories:
        for category in categories:
            terms.extend(CATEGORY_SYMBOLS.get(category, []))
    else:
        terms.extend(BASE_SYMBOLS)

    if not terms:
        terms.extend(BASE_SYMBOLS)

    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(term)
    return deduped


def regex_term(term: str) -> str:
    escaped = re.escape(term)
    if re.fullmatch(r"[A-Za-z0-9_]+", term):
        return rf"\b{escaped}\b"
    return escaped


def run_rg(repo_root: Path, roots: list[str], terms: list[str]) -> list[str]:
    if not terms:
        return []
    pattern = "|".join(regex_term(term) for term in terms)
    cmd = ["rg", "-n", "--no-heading", "-S"]
    for glob in EXT_GLOBS:
        cmd.extend(["-g", glob])
    cmd.extend(["-e", pattern])
    cmd.extend(roots)

    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        print(proc.stderr.strip(), file=sys.stderr)
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def collect_rankings(
    matches: list[str],
    categories: list[str],
    query_tokens: list[str],
    focus_terms: list[str],
    show_lines: int,
) -> tuple[Counter, dict, Counter]:
    module_hits: Counter = Counter()
    file_data: dict = defaultdict(
        lambda: {"hits": 0, "score": 0.0, "symbols": Counter(), "samples": []}
    )
    symbol_hits: Counter = Counter()

    lowered_query_tokens = [token.lower() for token in query_tokens]
    lowered_focus_terms = [term.lower() for term in focus_terms]

    for raw in matches:
        parts = raw.split(":", 2)
        if len(parts) != 3:
            continue
        path, line_text, code = parts
        line_no = int(line_text) if line_text.isdigit() else 0
        stripped = code.strip()
        lowered = stripped.lower()
        if "license file in the root of the source" in lowered:
            continue

        module = module_for_path(path)
        module_hits[module] += 1

        data = file_data[path]
        data["hits"] += 1
        data["score"] += 1.0 + module_weight(path) + category_path_boost(path, categories)

        token_bonus = 0.0
        for token in lowered_query_tokens:
            if token in lowered:
                token_bonus += 0.2
        data["score"] += min(token_bonus, 1.0)

        found_symbols = extract_symbols(stripped)
        for symbol in found_symbols:
            data["symbols"][symbol] += 1
            symbol_hits[symbol] += 1
        if found_symbols:
            data["score"] += 0.3

        if lowered_focus_terms:
            focus_bonus = 0.0
            lowered_path = path.lower()
            unique_found = {symbol.lower() for symbol in found_symbols}
            for focus in lowered_focus_terms:
                if focus in lowered_path:
                    focus_bonus += 0.9
                if focus in lowered:
                    focus_bonus += 0.8
                for symbol in unique_found:
                    if focus == symbol:
                        focus_bonus += 1.0
                    elif focus in symbol or symbol in focus:
                        focus_bonus += 0.4
            data["score"] += min(focus_bonus, 3.0)

        if len(data["samples"]) < show_lines:
            preview = stripped[:180]
            data["samples"].append({"line": line_no, "text": preview})

    for entry in file_data.values():
        entry["score"] += min(1.5, 0.1 * len(entry["symbols"]))

    return module_hits, file_data, symbol_hits


def format_text_output(
    query: str,
    roots: list[str],
    categories: list[str],
    focus_terms: list[str],
    module_hits: Counter,
    file_data: dict,
    symbol_hits: Counter,
    max_files: int,
    max_symbols: int,
) -> None:
    sorted_files = sorted(
        file_data.items(),
        key=lambda item: (-item[1]["score"], -item[1]["hits"], item[0]),
    )
    top_symbols = symbol_hits.most_common(max_symbols)

    print("[Scope Narrowing]")
    print(f"Query: {query}")
    print(f"Search roots: {', '.join(roots)}")
    print(
        "Detected categories: "
        + (", ".join(categories) if categories else "none (generic scan)")
    )
    print("Focus terms: " + (", ".join(focus_terms) if focus_terms else "none"))

    print("\nModules:")
    for index, (module, hits) in enumerate(module_hits.most_common(10), start=1):
        print(f"{index}. {module} (hits={hits})")

    print("\nFiles:")
    for index, (path, data) in enumerate(sorted_files[:max_files], start=1):
        top_file_symbols = [name for name, _ in data["symbols"].most_common(3)]
        symbol_text = ", ".join(top_file_symbols) if top_file_symbols else "-"
        print(
            f"{index}. {path} (score={data['score']:.2f}, hits={data['hits']}, "
            f"symbols={symbol_text})"
        )
        for sample in data["samples"]:
            if sample["line"] > 0:
                print(f"   L{sample['line']}: {sample['text']}")

    print("\nSymbols:")
    for index, (symbol, hits) in enumerate(top_symbols, start=1):
        print(f"{index}. {symbol} ({hits})")

    suggested_terms = [symbol for symbol, _ in top_symbols[:6]]
    if suggested_terms:
        joined = "|".join(suggested_terms)
        print("\nSuggested grep:")
        print(
            "rg -n -S -g '*.mm' -g '*.h' -g '*.cpp' "
            f"'{joined}' {' '.join(roots)}"
        )


def format_json_output(
    query: str,
    roots: list[str],
    categories: list[str],
    focus_terms: list[str],
    module_hits: Counter,
    file_data: dict,
    symbol_hits: Counter,
    max_files: int,
    max_symbols: int,
) -> None:
    sorted_files = sorted(
        file_data.items(),
        key=lambda item: (-item[1]["score"], -item[1]["hits"], item[0]),
    )[:max_files]

    files = []
    for path, data in sorted_files:
        files.append(
            {
                "path": path,
                "score": round(data["score"], 3),
                "hits": data["hits"],
                "symbols": data["symbols"].most_common(max_symbols),
                "samples": data["samples"],
            }
        )

    payload = {
        "query": query,
        "roots": roots,
        "categories": categories,
        "focus_terms": focus_terms,
        "modules": module_hits.most_common(20),
        "files": files,
        "symbols": symbol_hits.most_common(max_symbols),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    if shutil.which("rg") is None:
        print("Error: `rg` is required but not found in PATH.", file=sys.stderr)
        return 2
    if not repo_root.exists():
        print(f"Error: repo root not found: {repo_root}", file=sys.stderr)
        return 2

    categories = detect_categories(args.query)
    query_tokens = extract_query_tokens(args.query)
    extra_symbols = parse_csv_args(args.symbol)
    explicit_focus_terms = parse_csv_args(args.focus)
    inferred_focus_terms = infer_focus_terms(args.query)
    focus_terms: list[str] = []
    seen_focus: set[str] = set()
    for term in explicit_focus_terms + inferred_focus_terms:
        lowered = term.lower()
        if lowered in seen_focus:
            continue
        seen_focus.add(lowered)
        focus_terms.append(term)
    roots = existing_roots(repo_root, args.root)

    if not roots:
        print("Error: no valid search roots found.", file=sys.stderr)
        return 2

    terms = build_search_terms(
        args.query,
        categories,
        query_tokens,
        extra_symbols,
        focus_terms,
    )
    matches = run_rg(repo_root, roots, terms)

    if not matches and query_tokens:
        matches = run_rg(repo_root, roots, query_tokens)

    if not matches:
        print("[Scope Narrowing]")
        print(f"Query: {args.query}")
        print("No matches found in configured roots.")
        print("Try adding explicit symbols with `--symbol` or focus hints with `--focus`.")
        return 0

    module_hits, file_data, symbol_hits = collect_rankings(
        matches,
        categories,
        query_tokens,
        focus_terms,
        args.show_lines,
    )

    if args.json:
        format_json_output(
            args.query,
            roots,
            categories,
            focus_terms,
            module_hits,
            file_data,
            symbol_hits,
            args.max_files,
            args.max_symbols,
        )
    else:
        format_text_output(
            args.query,
            roots,
            categories,
            focus_terms,
            module_hits,
            file_data,
            symbol_hits,
            args.max_files,
            args.max_symbols,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
