---
date: 2026-04-22
status: Implemented
aliases: [TEMS upstream, TEMS 배포]
tags: [decision, tems, phase3, layer1, distribution, packaging]
phase: 운영중
scope: 전체 에이전트 TEMS 배포·업그레이드 경로
project: TEMS
cssclass: twk-decision
---

# Decision — bobpullie/TEMS 를 TEMS Canonical Upstream 으로 확정

## TL;DR

TEMS 를 **pip 설치 가능한 독립 패키지 (`bobpullie/TEMS`)** 로 canonical 배포. 위상군 로컬 `memory/` 는 working copy — 검증 완료된 변경만 패키지에 반영. 타 에이전트는 `pip install -U git+https://github.com/bobpullie/TEMS.git` + `tems scaffold` 로 일괄 이식.

## 배경

### 이전 배포 경로 (~S41)
- 위상군이 `memory/` 를 로컬에서 직접 개발
- 타 에이전트(코드군 · 리얼군 · 디니군) 에 Wave 1/2 수동 이식 (rsync 또는 개별 파일 복사)
- 각 에이전트의 `memory/` 가 점진적으로 divergence → upgrade 절차 일관성 부재

### bobpullie/TEMS 기존 상태 (S42 진입 전)
- 2026-04-13~20 동안 **pip 패키지화** 완료 (pyproject.toml / scaffold CLI / 35 pytest)
- 하지만 **Phase 2 멈춰있음** — Phase 3 enforcement 인프라 (`tool_gate_hook` / `compliance_tracker` / `decay` 등) 미반영
- **Layer 1 강화 (preflight violation_count 노출)** 도 미반영 — 위상군 로컬에만 존재

### 문제
- 위상군 이 최신 Phase 3 + Layer 1 을 쓰는데 타 에이전트는 구버전
- Wave 2 수동 이식 비용 높음 + 일관성 보장 어려움
- 종일군이 "앞으로는 TEMS 변경은 패키지 repo 로 올려줘" 명시 지시 (S42)

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| A. 기존 방식 유지 (수동 이식) | 변경 없음 | divergence 심화, Wave 2 비용 ↑ |
| B. README 만 업데이트 | 최소 비용 | 코드는 여전히 Phase 2, `pip install` 받은 사용자 혼란 |
| **C. Phase 3 전체 포팅 + v0.2.0 릴리즈** (채택) | 업스트림이 실제 canonical. 타 에이전트 일괄 이식 가능화. in-place 마이그레이션 지원 | 1~2시간 작업. scaffold 확장 필요 |
| D. 릴리즈 품질 (테스트 포함) | 가장 완전 | 세션 하나 통째로 필요, 과잉 |

## 결정

**대안 C 채택** — Phase 3 전체 포팅 + Layer 1 + scaffold 6-hook 등록 + Phase 2→3 ALTER 마이그레이션 + README 재작성.

### 구현 범위 (v0.2.0 → v0.2.1)
1. **Templates 8종 추가**: `tool_gate_hook.py` · `compliance_tracker.py` · `tool_failure_hook.py` · `retrospective_hook.py` · `pattern_detector.py` · `memory_bridge.py` · `decay.py` · `sdc_commit.py`
2. **templates/preflight_hook.py** 에 Layer 1 포팅 (`get_rule_health` / 헬스 주석 / "필수 준수" 헤더 / 준수 directive)
3. **scaffold.py 확장**:
   - `copy_templates` 10종
   - `register_hook` 6 이벤트 멱등 등록 (UserPromptSubmit / PreToolUse / PostToolUse×3 / Stop)
   - `rule_health` Phase 3 컬럼 8개 추가 (fire/violation/compliance 등)
   - FTS5 `summary` 컬럼 포함
   - `_migrate_rule_health` — 기존 Phase 2 DB 에 `ALTER TABLE ADD COLUMN` 자동 수행
4. **README 재작성** — pip install 중심, 패키지 구조 + 에이전트 구조 분리
5. **`__version__` 동기화** (pyproject ↔ `__init__.py` ↔ test)
6. **cwd fallback + case-insensitive project 태그** (v0.2.1, 아트군 실설치 중 발견한 defect fix)

### 검증
- pytest 35/35 통과 (기존 테스트 회귀 없음)
- Clean scaffold smoke: 10 templates + 6 hooks + Phase 3 schema + FTS summary
- Migration smoke: Phase 2 DB (3 cols + 1 row) → scaffold → 11 cols, 데이터 보존
- 아트군 실설치 end-to-end: `project:DnT` 태그 TCL → preflight 정상 주입

### 타 에이전트 이식 절차 (표준)
```bash
python -m pip install -U git+https://github.com/bobpullie/TEMS.git
tems scaffold --agent-id <ID> --agent-name "<NAME>" --project <PROJ> --cwd <PATH>
# 기존 agent 에서 실행하면:
#  - 누락 템플릿만 복사 (기존 custom 파일 보존)
#  - rule_health 에 Phase 3 컬럼 ALTER TABLE 추가 (데이터 보존)
#  - settings.local.json hook 멱등 등록 (non-TEMS hook 보존)
```

## 위험 및 제약

- **위상군 ↔ 패키지 dual commit 피로** — TEMS 변경 시 두 곳에 반영해야 함. 향후 git subtree 또는 submodule 고려.
- **QMD Dense Fallback 은 외부 의존성** (qmd-embed 스킬 + CUDA) — 기본 BM25 only, 고급 기능은 opt-in. README v0.2.1 에 "Advanced" 섹션으로 명시.
- **구세대 `tems/tems_db.db` 자동 마이그레이션 미구현** — 아트군 등 legacy tems/ 디렉토리 보유 에이전트는 신 `memory/error_logs.db` 가 빈 상태로 시작. Wave 2 확장 시 마이그레이션 툴 필요.
- **Wave 1 에이전트 재스캐폴드 필요** — `pip install -U` 만으로는 신 hook 템플릿이 에이전트 `memory/` 로 옮겨가지 않음. `tems scaffold --force` 또는 `tems restore` 실행 권장.

## 참조

- [[../../session_archive/20260422_session2_raw]] — S42 Q&A 원본
- [[../../../handover_doc/2026-04-22_session42]] — S42 핸드오버
- [[../patterns/Enforcement_4_Layer]] — 4층 강제력 구조 (같은 세션 도출)
- [[../concepts/TEMS]] — TEMS 개념 전체
