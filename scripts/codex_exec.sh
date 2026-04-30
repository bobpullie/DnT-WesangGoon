#!/usr/bin/env bash
# codex_exec.sh — codex CLI 안전 호출 wrapper (위상군 git bash 환경)
#
# === 역사 ===
# S51 정착 (PowerShell tool 환경): cmd.exe wrapper + stdin file redirect
#   1) Start-Process codex.cmd 직접 실행 X (.cmd 는 Win32 exe 아님)
#   2) Tee-Object pipe stdin → codex EOF 못 받아 hang
#   3) 정착 = cmd /c "codex ... < prompt > out 2> err"
#
# S53 단순화 (Bash tool / git bash 환경):
#   1) git bash 의 codex 는 POSIX 셸 wrapper (`exec node codex.js`) — 직접 호출 가능
#   2) `< prompt.txt` file redirect 로 stdin EOF 자연 제공
#   3) codex 0.125.0 known issue — 작업 완료 후 "rollout items not found" + WebSocket
#      cleanup 으로 프로세스가 정상 종료 안 함. `timeout` 으로 bound 필수.
#   4) 완료 판정 = stderr 에 "tokens used" 라인 존재 (codex 가 정상 finish 시 항상 찍힘)
#
# === 핵심 4원칙 ===
#   A) codex 직접 호출 (POSIX wrapper) — git bash 에서 정상 작동
#   B) stdin file redirect (`< prompt.txt`) — non-TTY pipe 는 EOF 없어 hang
#   C) `timeout` 으로 hard limit — codex shutdown hang 회피
#   D) "tokens used" 마커로 의미적 완료 판정 — exit 124 라도 작업 성공 가능
#
# === Output ===
#   <log-dir>/<prefix>_stdout.log     — codex 정규 출력
#   <log-dir>/<prefix>_stderr.log     — codex 진단 (tokens used / 세션 메타)
#   <log-dir>/<prefix>.done           — sentinel: 실제 완료 (parser 가 탐지)
#   <log-dir>/<prefix>.exit           — codex exit code (timeout 발동 시 124)
#   exit code                          — wrapper exit (0 = 완료 마커 확인, 1+ = 미확인)

set -euo pipefail

usage() {
    cat <<EOF >&2
Usage: $0 <prompt_file> [options]

Options:
  --model MODEL       기본: gpt-5.5
  --sandbox MODE      read-only | workspace-write | danger-full-access
                       (미지정 시 --full-auto = workspace-write 동등)
  --workdir DIR       기본: 현재 디렉토리
  --log-dir DIR       기본: \$TEMP 또는 /tmp
  --log-prefix NAME   기본: codex_<YYYYMMDD_HHMMSS>
  --timeout SECONDS   기본: 900 (15분). codex hard timeout
  --kill-after SEC    SIGTERM 후 SEC 뒤 SIGKILL (기본 10)

동작:
  watch mode — codex 의 stderr 에 "tokens used" 라인 (작업 완료 마커) 이
  나타나면 즉시 SIGTERM 으로 종료 시도. codex 0.125.0 의 known shutdown hang
  (rollout error + WebSocket cleanup) 회피. 마커 미발견 시 hard timeout.

Output:
  <log-dir>/<prefix>_stdout.log     — codex 정규 출력
  <log-dir>/<prefix>_stderr.log     — codex 진단/세션 메타
  <log-dir>/<prefix>.done           — sentinel (의미적 완료 마커)
  <log-dir>/<prefix>.exit           — codex 본체 exit code
  wrapper exit                       — 0 = "tokens used" 관측, 1+ = 미관측

호출 권장:
  - 짧은 ping/test (≤60s):  Bash tool 직접 (foreground)
  - 실제 구현 (5~15분):     Bash tool run_in_background=true + 별도 polling
EOF
    exit 1
}

[[ $# -lt 1 ]] && usage

PROMPT_FILE="$1"
shift

MODEL="gpt-5.5"
SANDBOX_FLAG="--full-auto"
WORKDIR="$(pwd)"
LOG_DIR="${TEMP:-/tmp}"
LOG_PREFIX="codex_$(date +%Y%m%d_%H%M%S)"
HARD_TIMEOUT=900
KILL_AFTER=10

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)        MODEL="$2"; shift 2 ;;
        --sandbox)      SANDBOX_FLAG="--sandbox $2"; shift 2 ;;
        --workdir)      WORKDIR="$2"; shift 2 ;;
        --log-dir)      LOG_DIR="$2"; shift 2 ;;
        --log-prefix)   LOG_PREFIX="$2"; shift 2 ;;
        --timeout)      HARD_TIMEOUT="$2"; shift 2 ;;
        --kill-after)   KILL_AFTER="$2"; shift 2 ;;
        -h|--help)      usage ;;
        *) echo "[ERROR] Unknown option: $1" >&2; usage ;;
    esac
done

[[ -f "$PROMPT_FILE" ]] || { echo "[ERROR] prompt file not found: $PROMPT_FILE" >&2; exit 2; }
command -v codex >/dev/null 2>&1 || { echo "[ERROR] codex not on PATH" >&2; exit 3; }
command -v timeout >/dev/null 2>&1 || { echo "[ERROR] GNU timeout not on PATH" >&2; exit 3; }

mkdir -p "$LOG_DIR"

STDOUT_LOG="$LOG_DIR/${LOG_PREFIX}_stdout.log"
STDERR_LOG="$LOG_DIR/${LOG_PREFIX}_stderr.log"
DONE_FILE="$LOG_DIR/${LOG_PREFIX}.done"
EXIT_FILE="$LOG_DIR/${LOG_PREFIX}.exit"
PROMPT_BYTES=$(wc -c < "$PROMPT_FILE")

# Workdir 은 codex 가 Windows path 로 받는 게 안전
if command -v cygpath >/dev/null 2>&1; then
    WORKDIR_C="$(cygpath -w "$WORKDIR")"
else
    WORKDIR_C="$WORKDIR"
fi

cat <<EOF
[codex-exe] model:    $MODEL
[codex-exe] sandbox:  $SANDBOX_FLAG
[codex-exe] workdir:  $WORKDIR_C
[codex-exe] prompt:   $PROMPT_FILE ($PROMPT_BYTES bytes)
[codex-exe] timeout:  ${HARD_TIMEOUT}s (kill-after ${KILL_AFTER}s)
[codex-exe] stdout:   $STDOUT_LOG
[codex-exe] stderr:   $STDERR_LOG
[codex-exe] done:     $DONE_FILE
[codex-exe] exit:     $EXIT_FILE
[codex-exe] starting (direct codex + GNU timeout) ...
EOF

START_TS=$(date +%s)

# --- 핵심 호출 ---
# codex 를 background 로 띄우고 stderr 의 "tokens used" 마커를 polling.
# 마커 발견 즉시 SIGTERM → SIGKILL — codex 의 shutdown hang (rollout error +
# WebSocket cleanup) 을 회피하면서 실제 작업 완료 직후 빠르게 반환.
# 마커 없이 hard timeout 도달 시 실패로 처리.

set +e
codex exec -m "$MODEL" $SANDBOX_FLAG -C "$WORKDIR_C" \
    < "$PROMPT_FILE" > "$STDOUT_LOG" 2> "$STDERR_LOG" &
CODEX_PID=$!

SEMANTIC_OK=0
DEADLINE=$(($(date +%s) + HARD_TIMEOUT))

while kill -0 "$CODEX_PID" 2>/dev/null; do
    if grep -q "^tokens used$" "$STDERR_LOG" 2>/dev/null; then
        # 실제 작업 완료 — 즉시 종료 시도
        SEMANTIC_OK=1
        sleep 1  # codex 가 stdout flush 마무리 시간
        kill -TERM "$CODEX_PID" 2>/dev/null || true
        # KILL_AFTER 초 후 SIGKILL escalate
        for i in $(seq 1 $((KILL_AFTER * 2))); do
            kill -0 "$CODEX_PID" 2>/dev/null || break
            sleep 0.5
        done
        kill -KILL "$CODEX_PID" 2>/dev/null || true
        break
    fi
    if [[ $(date +%s) -ge $DEADLINE ]]; then
        # hard timeout 도달
        kill -TERM "$CODEX_PID" 2>/dev/null || true
        sleep "$KILL_AFTER"
        kill -KILL "$CODEX_PID" 2>/dev/null || true
        break
    fi
    sleep 0.5
done

wait "$CODEX_PID" 2>/dev/null
CODEX_EXIT=$?
set -e

ELAPSED=$(($(date +%s) - START_TS))
echo "$CODEX_EXIT" > "$EXIT_FILE"

[[ $SEMANTIC_OK -eq 1 ]] && echo "tokens_used_observed" > "$DONE_FILE"

cat <<EOF

[codex-exe] codex exit:     $CODEX_EXIT  (124 = timeout, 0 = clean)
[codex-exe] elapsed:        ${ELAPSED}s
[codex-exe] semantic ok:    $SEMANTIC_OK  (1 = "tokens used" 마커 발견)
[codex-exe] stdout bytes:   $(wc -c < "$STDOUT_LOG" 2>/dev/null || echo 0)
[codex-exe] stderr bytes:   $(wc -c < "$STDERR_LOG" 2>/dev/null || echo 0)

----- stdout (last 30 lines) -----
EOF
tail -n 30 "$STDOUT_LOG" 2>/dev/null || echo "(empty)"

cat <<EOF

----- stderr (last 10 lines) -----
EOF
tail -n 10 "$STDERR_LOG" 2>/dev/null || echo "(empty)"

# wrapper exit: semantic 우선
if [[ $SEMANTIC_OK -eq 1 ]]; then
    exit 0
else
    exit "$CODEX_EXIT"
fi
