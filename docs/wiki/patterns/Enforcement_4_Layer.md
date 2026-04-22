---
date: 2026-04-22
status: Active
phase: Phase-3
scope: TEMS 규칙 강제력 설계 · 타 에이전트 adoption
tags: [pattern, tems, enforcement, tgl, deny-hook, compliance]
cssclass: twk-pattern
---

# Pattern — Enforcement 4-Layer (TEMS 강제력 4계층 구조)

## ID

PAT-TEMS-ENF-4L

## 정의

TEMS 규칙의 강제력을 **4개 계층** 으로 분리해 적용하는 아키텍처. 각 층은 강제력 / 오버헤드 / 구현 복잡도가 상이하며, 규칙의 성격에 따라 어느 층에 배치할지 판단한다.

| Layer | 수단 | 강제력 | 런타임 오버헤드 | 적용 대상 |
|-------|------|--------|----------------|----------|
| **L1** | 자연어 주입 강화 + `violation_count` 노출 | 소프트 (LLM 순응 의존) | ~50-100 tokens/prompt | 모든 TGL |
| **L2** | PreToolUse `permissionDecision: "deny"` JSON | 하드 (harness 가 도구 호출 차단) | ~10-50ms/call (subprocess) | TGL-T + `tool_pattern` + `severity=critical` |
| **L3** | PostToolUse compliance 측정 + `violation_count` 누적 | 사후 적발 + 데이터화 | ~20-100ms/tool call | 모든 TGL (`forbidden` / `failure_signature` 슬롯 보유) |
| **L4** | DVC case 승격 (결정론적 빌드 검증) | CI/cron 차단 | 매 호출 0 (CI 전용) | 빌드 산출물로 체크 가능한 규칙 |

## 데이터 소스 / 의존성

- L1 구현: `templates/preflight_hook.py` `format_rules` (Layer 1 강화 v0.2.0+)
- L2 구현: `templates/tool_gate_hook.py` (Phase 3, v0.2.0+)
- L3 구현: `templates/compliance_tracker.py` (Phase 3)
- L4: DVC (Deterministic Verification Checklist) 별도 시스템 — `src/checklist/cases.json`
- 건강 지표 저장소: `rule_health` 테이블 (fire_count / compliance_count / violation_count)

## 현재 상태

Active — `bobpullie/TEMS` v0.2.1 릴리즈에 L1~L3 전체 포함. L4 는 DVC 별도 시스템으로 운영.

## 적용 원칙

### 배치 판단 기준

| 규칙 성격 | 권장 Layer |
|-----------|-----------|
| 결정론적 패턴 매칭 가능 (도구 호출 / 파일 경로 / 명령어) | L2 (하드 차단) — `tool_pattern` 정의 필수 |
| 실패 시그니처로 검출 가능 | L3 (사후 적발) — `failure_signature` 정의 |
| 의미 매칭만 가능한 맥락 규칙 | L1 (자연어 주입 강화) 만 |
| 빌드 산출물 기반 규칙 | L4 (DVC case) — 런타임 오버헤드 0 |

### 승격 경로

**L1 → L2**: 특정 규칙이 `violation_count` 가 반복 증가 → `tool_pattern` 정규식으로 기술 가능하면 `severity=critical` 승격 → `tool_gate_hook` 에서 자동 차단.

**L1 → L4**: 규칙 위반이 빌드 산출물(HTML / JSON / 번들) 로 검증 가능하면 DVC case 로 승격. 런타임 소프트 → CI 차단.

**L2 → L1**: false positive 심한 경우 `severity=warning` 으로 강등.

### L2 deny JSON 스펙

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "TGL #N (TGL-T) — 도구 호출 차단\n패턴: ...\n..."
  }
}
```

hook 이 stdout 으로 위 JSON 출력 → Claude Code harness 가 도구 호출 자체를 취소. 단순 stdout 텍스트 경고(소프트) 와 결정적으로 다름.

## 관련 실험·결과

### S42 (2026-04-22) 실증

- **Layer 1 강화 구현** (위상군 로컬 → v0.2.0 템플릿 포팅):
  - `get_rule_health()` 로 rule_health 의 5지표 노출
  - TGL 헤더 "필수 준수" 승격 + 각 규칙에 `(v:N c:M)` 주석 + 말미 준수 directive
  - 자연어 주입의 ceiling 안에서 social pressure + explicit acknowledgment 유도

- **Layer 2 live 증명**: Smoke test 중 cleanup 명령이 dummy TGL-T 규칙에 self-block — tool_gate_hook 의 deny 경로 실제 작동 확인.

- **Layer 3 운영 데이터**: 위상군 TGL #102 (memory/*.py 직접 편집 방지) 가 `violation_count=14 c=1` 누적. 반복 위반 규칙 식별의 근거.

- **오버헤드 실측**:
  - 자연어 주입 강화: ~$0.001/prompt (Opus 1M context)
  - PreToolUse deny (정규식): ~10-50ms/call, 50 call 세션 ≈ 0.5-2.5s
  - Haiku pre-eval (기각): ~500-1500ms/call, 50 call ≈ **25-75s 누적 레이턴시**, UX 저해로 제외

### 반패턴 (검토 후 제외)

- **Haiku LLM-as-judge pre-eval** — 의미 매칭 규칙에 써볼 수 있으나 레이턴시 치명적. 극단적 중요 규칙 1~2건에만 local 적용 가능성은 남김.
- **Stop hook 사후 regeneration** — 대안 정답 생성 부담 크고 사용성 저하. violation_count 누적 만으로 충분 판정.

## 주의점

- L1 만 쓰면 본질적으로 LLM 순응 의존 — "banner blindness" 로 희석 가능. score ≥ 0.55 threshold + MAX_TGL=2 로 주입 절제.
- L2 의 `tool_pattern` 이 과도하게 넓으면 정상 작업도 차단 (false positive). severity=warning 로 시작해 데이터 축적 후 critical 승격 권장.
- L3 의 `forbidden_action` 휴리스틱 fallback 은 FORBIDDEN 노이즈 토큰이 많을 수 있음 — `tool_pattern` / `failure_signature` 명시 권장.
- L4 승격 결정은 "빌드 산출물 기반으로 체크 가능한가" 가 유일한 기준. 런타임 동작 기반이면 L1~L3 에 남김.

## 관련 엔티티

[[../concepts/TEMS]] [[../concepts/TCL_vs_TGL]] [[Classification_7_Category]] [[../decisions/2026-04-22_tems-upstream-canonical]]

## 참조

- [[../concepts/TEMS]] — TEMS 전체 아키텍처
- [[../concepts/TCL_vs_TGL]] — TCL/TGL 분류 기준
- [[Classification_7_Category]] — TGL 7-카테고리 (L2 적용 대상 식별)
- [[../concepts/DVC_vs_TEMS]] — L4 승격 시 DVC 와의 관계
- [[../decisions/2026-04-22_tems-upstream-canonical]] — v0.2.0/v0.2.1 릴리즈 결정 (이 패턴의 배포)
