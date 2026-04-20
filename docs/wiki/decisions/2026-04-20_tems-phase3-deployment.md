---
date: 2026-04-20
status: Observation
phase: Phase-3
scope: wesang-only
tags: [tems, phase-3, tool-gate, compliance-tracker, observation, wave-2]
---

# TEMS Phase 3 배포 유보 — 위상군 단독 관찰

## TL;DR

Phase 3 (tool_gate_hook + compliance_tracker + decay)는 위상군 단독으로 1~2세션 관찰.  
violation/compliance 통계를 확보한 후 Wave 2 배포 여부를 판정한다.

## 배경

Phase 3는 S32에서 신규 개발. 코드군은 8세션 동안 tool_gate 없이 무고장으로 운영됨.  
quant 도메인은 도구 사용 패턴이 보수적이어서 Phase 3의 효용이 실제로 있는지 데이터 부족.  
성급한 배포보다 위상군 단독 관찰 후 근거 기반 결정이 적합하다고 판단.

S33에서 추가 패치 2건 발견:
- **P1-a-follow**: `tool_gate_hook`/`preflight_hook`에서 `had_violation` 덮어쓰기 취약점 수정 (보존 로직 추가)
- **stale eviction 24h TTL**: `compliance_tracker`에서 24h 경과 guard 자동 eviction

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| 즉시 전 에이전트 배포 | 기능 통일성 | 관찰 데이터 없음, 안정성 미검증 |
| **(채택) 위상군 단독 관찰 후 판정** | 근거 기반 결정, 위험 최소화 | Wave 2 지연 |
| opt-in 방식 선택 배포 | 에이전트 자율성 | 관리 복잡도 증가 |

## 결정

**관찰 지표 (1~2세션):**
- `violation_count`: Phase 3 가드가 실제로 위반을 감지한 횟수
- `compliance_count`: 가드 적용 중 준수한 횟수
- `stale guard eviction 빈도`: TTL 24h 내 만료 비율

**Wave 2 배포 판정 기준:**

```
violation > 5 AND compliance/total > 0.7
→ Wave 2 전체 배포 (효용 검증됨)

violation ≤ 2
→ opt-in 방식 (선택적 배포)

violation 3~5, compliance/total ≤ 0.7
→ 추가 1세션 관찰 후 재판정
```

**현재 Phase 3 구성 (위상군 전용):**
- `tool_gate_hook.py`: PreToolUse에서 TGL-T 패턴 매칭, 차단/경고
- `compliance_tracker.py`: PostToolUse에서 active guard 위반/준수 카운팅 + 24h stale eviction
- `decay.py`: 30일 cold / 90일 archive 자동 전환

## 위험 및 제약

- Phase 3 미관찰 상태에서의 배포는 false positive 가드로 에이전트 흐름 방해 가능
- `had_violation` 덮어쓰기 버그(P1-a-follow)가 이전에 데이터 오염을 일으켰을 수 있음 — 과거 통계 신뢰도 낮음
- Windows Task Scheduler에 `decay.py` 등록 미완료 (매일 09:00, S34 작업 예정)

## 참조

- [[2026-04-20_wave1-standardization]] — Wave 1 표준화 (Phase 3 제외 배경)
- [[../concepts/TEMS]] — TEMS 전체 아키텍처 및 Hook 구성
