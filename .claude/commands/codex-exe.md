---
description: codex GPT-5.5 위임 호출 — 위상군이 audit 받은 spec 을 외부 모델 (Opus 4.7 ≠ 구현자) 로 구현 시 사용. S51 정착 + S53 단순화 패턴 캡슐화.
argument-hint: "<prompt-file-path> [--sandbox MODE] [--timeout SECONDS]"
---

# /codex-exe — codex GPT-5.5 위임 호출

위상군이 설계·audit 한 spec 을 **외부 모델 (codex CLI / GPT-5.5)** 로 구현하는 워크플로우. 메타-결함 자기-방어 동기 (Opus 4.7 본체 = 설계자 = 구현자 → 자축 패턴) 를 구조적으로 차단.

배경 = S51 (Self-Cognition Auto-Register Gate) 첫 적용 → S53 환경 단순화. 자세한 history: [[../../docs/session_archive/20260429_session3_raw|S51 raw]] §A18-A45 / [[../../handover_doc/2026-04-29_session51|S51 핸드오버]] §4.

---

## 0. 사용 결정 (위임 게이트)

다음 중 **하나 이상** 해당 시 codex 위임 고려:

| Signal | 이유 |
|--------|------|
| Spec 자체가 **메타-결함 차단 hook** (자기 평가 / 자기 등록 등) | 본체 = 설계자 = 구현자 → 자축 패턴 위험 |
| 구현 분량 ≥ ~15 파일 (모듈 + tests + templates) | 본체 컨텍스트 보존 필요 |
| 구현 후 본체가 **trust-but-verify** 단계로 비판 검토 필요 | 검증자 ≠ 구현자 분리 효과 |
| Spec 이 사전에 **superpowers:code-reviewer audit** 통과 (P0 모두 반영) | audit 가 critical 결함 사전 차단 |

위 조건 미충족 (단순 1~2 파일 / 본체 직접 가능 / audit 없음) → SDC 스킬로 Sonnet 위임 또는 본체 직접 처리.

---

## 1. Prompt 작성 가이드 (필수 5섹션)

`<workspace-write 만 허용되는 sandbox> 안에서 codex 가 자율 실행`. 따라서 prompt 는 **anti-acceptance hard fence** 가 필수.

```markdown
# Task: <한줄 요약>

## §1 Scope (작업 범위)
- 신규 N개 / 수정 M개 — 정확히 명시
- 작업 디렉토리: <절대 경로>

## §2 Spec (audit 통과한 v2 본문)
<spec 전문 또는 link>

## §3 Deliverables (acceptance criteria)
- [ ] criterion 1
- [ ] criterion 2 (≥18개 권장 — S51 = 18 acceptance)

## §4 Smoke Tests (codex 가 실행해서 모두 PASS 보고)
- pytest <module> -q
- 무회귀 hook 5종 alive 확인 (`python <hook>.py --self-check`)

## §5 Anti-Acceptance (Hard Fence — 위반 = reject)
- [ ] LLM 호출 금지 (codex 자체 외)
- [ ] tems_commit / 외부 등록 호출 금지
- [ ] 본 spec 이 명시한 파일 외 수정 금지 (settings.local.json 외)
- [ ] 자축 / 절대화 어휘 0건 (본 spec 본문에도 점검)
```

S51 spec 실제 사례: [[../../docs/superpowers/plans/2026-04-29-self-cognition-auto-register|self-cognition gate spec v2]]

---

## 2. 호출 (wrapper script)

Wrapper 위치: [`scripts/codex_exec.sh`](../../scripts/codex_exec.sh)

### 2.1 짧은 ping/test (≤60s)

```bash
bash scripts/codex_exec.sh /path/to/prompt.txt \
    --sandbox read-only \
    --workdir e:/DnT/DnT_WesangGoon \
    --timeout 60
```

### 2.2 실제 구현 (5~15분, background 권장)

```bash
# Bash tool 의 run_in_background=true 로 호출
bash scripts/codex_exec.sh /path/to/prompt.txt \
    --sandbox workspace-write \
    --workdir e:/DnT/DnT_WesangGoon \
    --log-prefix codex_<task-id> \
    --timeout 1200
```

호출 후 별도 polling task 로 sentinel 감시:

```bash
DONE=/tmp/codex_<task-id>.done
until [[ -f "$DONE" ]]; do sleep 5; done
echo "✓ codex 작업 완료"
cat "$DONE"
```

### 2.3 wrapper 동작 원리 (요약)

1. **codex 직접 호출** — git bash 의 `codex` 는 POSIX 셸 wrapper (`exec node codex.js`). cmd.exe 우회 불필요.
2. **stdin file redirect** (`< prompt.txt`) — non-TTY pipe 는 EOF 없어 hang. 파일은 자연 EOF.
3. **Watch mode** — codex 가 stderr 에 `"tokens used"` 라인 출력 = 작업 완료 마커. wrapper 가 polling 으로 마커 발견 즉시 SIGTERM → SIGKILL.
4. **Hard timeout** — 마커 안 보이면 `--timeout` 초 후 강제 종료.

이유: codex 0.125.0 의 known issue — 작업 완료 후 "rollout items not found" + WebSocket cleanup 으로 프로세스가 정상 종료 안 함. 마커 기반 종료가 30초 → 6초로 단축.

---

## 3. Trust-But-Verify (위상군 본체)

codex 자가 보고는 **신뢰 대상 X**. S48/S49 패턴 = 자가 보고만 신뢰 → 메타-결함 재발 위험. 본체가 직접 검증.

| # | 검증 항목 | 명령 |
|---|----------|------|
| 1 | 산출물 무결성 | `git status` + `git diff --stat` — spec §1 의 신규/수정 카운트와 일치? |
| 2 | 단위 테스트 재실행 | `python -m pytest tests/ -q` — codex 자가 보고와 일치? |
| 3 | 핵심 모듈 spot read | `Read` 로 layer/함수 구조 직접 확인 — spec 에 적힌 함수명 grep |
| 4 | In-band 발동 | fixture 로 의도된 trigger 입력 → 출력 확인 (예: 자축 텍스트 → draft 생성) |
| 5 | 무회귀 hook alive | 기존 hook 5종 (preflight/retro/handover_gate/tool_gate/audit_diag) 단위 실행 |
| 6 | settings/config diff | spec 명시 외 변경 0건 |
| 7 | jsonl 진단 채널 | 의도된 이벤트 적재 확인 |

검증 PASS → 종일군에게 commit 여부 보고. 결함 발견 → codex 재지시 또는 수동 patch.

---

## 4. 주의사항

- **codex zombie 프로세스** — codex 0.125.0 의 cleanup 이슈로 `codex.exe` / `node.exe` 가 메모리에 남을 수 있음. 누적되면 다음 세션 호출이 파일 락 충돌. 종일군이 수동으로 `taskkill` 또는 PC 재기동 시 자연 정리.
- **Permission** — `.claude/settings.local.json` line 78: `"Bash(codex exec -m gpt-5.5 --full-auto*)"` 등록 확인 (또는 `permissionMode: bypassPermissions` 모드).
- **Trusted directory** — `~/.codex/config.toml` 에 `[projects.'E:\DnT\DnT_WesangGoon'] trust_level = "trusted"` 등록 확인. 미등록 시 codex 가 "Not inside a trusted directory" 에러 반환.
- **Sandbox 선택** — 기본 `--full-auto` (= workspace-write). 읽기만 필요 시 `--sandbox read-only` 명시. `danger-full-access` 는 spec hard fence 가 weak 할 때만 (사용 비권장).

---

## 5. S51 정착 패턴 vs S53 단순화

| 단계 | S51 (PowerShell tool) | S53 (Bash tool / git bash) |
|------|----------------------|---------------------------|
| 호출 진입 | PowerShell `Start-Process` | bash 직접 |
| .cmd wrapper 우회 | cmd.exe `/c` 필수 | 불필요 (POSIX wrapper 가 node 직접 실행) |
| stdin EOF | NUL device or 파일 redirect | 파일 redirect |
| stdout/stderr | log 파일 redirect | log 파일 redirect |
| 종료 처리 | task-notification 대기 | watch mode (tokens used 마커 + SIGTERM) |

본체 환경이 git bash → S53 패턴 사용. PowerShell 환경에서 호출해야 한다면 S51 raw §A40 재참조.

---

## 6. 호출 워크플로우 (체크리스트)

`/codex-exe` 사용 시 본체가 따라야 할 순서:

1. **위임 게이트 통과 확인** (§0) — 4 signal 중 ≥1 해당
2. **spec v1 작성** — `docs/superpowers/plans/<date>-<task>.md`
3. **superpowers:code-reviewer audit** — P0 결함 list 받기
4. **spec v2 작성** — Appendix A binding amendments + audit P0 모두 반영
5. **prompt 파일 작성** — §1 가이드의 5 섹션 (anti-acceptance 포함)
6. **wrapper 호출** — §2.2 (background + sentinel polling)
7. **trust-but-verify** — §3 의 7 검증 모두 PASS
8. **결과 보고** — 종일군에게 산출물 + 검증 결과 + commit 여부 결정 요청
