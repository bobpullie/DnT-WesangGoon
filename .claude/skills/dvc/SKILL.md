---
name: dvc
description: Deterministic Verification Checklist — 프로젝트별 결정론적 빌드 검증 프레임워크. 정적 분석 + 데이터 파일 검증 + 배포 정합성 점검을 하나의 checklist 시스템으로 통합. 누적 버그를 case로 일반화하여 회귀 방지. Use when — 신규 프로젝트에 build verification 시스템을 도입할 때, 반복 발생 버그를 일반화된 case로 등록할 때, CI/cron 용 결정론적 품질 게이트가 필요할 때, TEMS (LLM memory system) 와 구분되는 build-time 검증 레이어가 필요할 때.
---

# DVC — Deterministic Verification Checklist

## 정체성

**DVC는 TEMS의 TCL이 아니다.** 두 시스템은 층위가 다르다:

| 축 | DVC | TEMS TCL |
|----|-----|----------|
| 실행 시점 | build-time / CI / cron | prompt-time (preflight hook) |
| 저장 형태 | `cases.json` + `chk_*.py` Python | SQLite DB 자연어 규칙 |
| 검증 방식 | 정적 분석 + 파일 패턴 + SSH 해시 | LLM 의미 매칭 + 컨텍스트 주입 |
| 소비자 | 개발자, CI 서버, cron | LLM agent (Claude) |
| 결과 | pass/fail + suggestion | 규칙 본문 주입 |
| 예외 처리 | `# chk:skip CASE_ID 사유` 주석 | score threshold |

원조는 DnT_Fermion 프로젝트(코드군)에서 발생한 실 버그들을 일반화하여 누적한 시스템. 2026-03-17 단일 인시던트에서 13개 case가 귀납적으로 추출된 구조가 완성도 높음.

## 언제 호출하는가

**YES (DVC 호출 트리거):**
- "빌드 검증 체크리스트 만들어줘"
- "이 프로젝트에 정적 분석 가드 도입"
- "같은 버그 3회 이상 반복되었으니 회귀 방지 case 추가"
- "cron/CI로 돌릴 결정론적 체크리스트"
- "배포 전 해시 비교 + cron 등록 점검"

**NO (DVC 호출하지 말 것):**
- LLM agent가 미래 행동 교정용으로 기억할 규칙 → **TEMS TCL/TGL** 사용 (`memory/tems_commit.py`)
- 단발성 스크립트 검증 → DVC 과잉. 간단한 pytest가 낫다
- 런타임 예외 감지 → exception tracking/sentry 사용

## 스킬이 제공하는 것

1. **[templates/base.py](templates/base.py)** — `BaseChecklist`, `CheckResult`, `CheckReport`, `# chk:skip` 바이패스 시스템 (프로젝트 무관)
2. **[templates/runner.py](templates/runner.py)** — CLI 실행기 + 자동 체커 discovery + 바이패스/케이스 감사 도구
3. **[templates/cases.json](templates/cases.json)** — case 레지스트리 스키마 (필드: case_id, category, generalized, origin_bug, checker, scope, auto_discover, added_date, severity)
4. **[templates/chk_example.py](templates/chk_example.py)** — checker 모듈 템플릿 (케이스 → 메서드 매핑, scope 한정, false-positive 억제 패턴)
5. **[init.py](init.py)** — 신규 프로젝트 스캐폴딩 CLI: `python init.py <project_root>` → `{root}/src/checklist/` 생성 + docs 스캐폴드
6. **[ARCHITECTURE.md](ARCHITECTURE.md)** — 설계 원리: 왜 이 구조가 탄탄한가, 핵심 원리 10가지
7. **[GUIDE.md](GUIDE.md)** — 운영 가이드: 새 case 추가 절차, 바이패스 규약, 통합/archive 임계값

## 즉시 사용 — 3가지 시나리오

### 시나리오 A — 신규 프로젝트에 DVC 도입

```bash
python E:/DnT/DnT_WesangGoon/.claude/skills/dvc/init.py /path/to/new_project
# 생성: {new_project}/src/checklist/{base,runner,chk_example}.py + cases.json
# 생성: {new_project}/docs/BUILD_VERIFICATION.md
# 생성: {new_project}/dvc_config.json (경로 설정)
```

이후 프로젝트 내에서:
```bash
cd /path/to/new_project
python -m checklist.runner                    # 전체 실행
python -m checklist.runner --audit-bypass     # 바이패스 감사
python -m checklist.runner --audit-cases      # 케이스 생명주기 분석
```

### 시나리오 B — 기존 프로젝트(코드군 등)에 적용 완료된 DVC 유지

코드군의 `src/checklist/`는 **현 상태 완성도 높음**. 이 skill은 코드군을 건드리지 않는다. 단, `docs/BUILD_VERIFICATION.md`에 "DVC ≠ TEMS TCL" 선언이 추가된다.

### 시나리오 C — 반복 버그 발견 → 새 case 일반화

`[GUIDE.md](GUIDE.md) → "새 case 추가 절차"` 참조. 3단계:
1. `cases.json`에 case 메타데이터 추가 (`origin_bug` 필수)
2. `chk_{category}.py`에 `check_{case_id}()` 메서드 구현 (scope 한정)
3. `python -m checklist.runner --module {category}` 로 로컬 검증

## TEMS와의 상호 운용 원칙

- DVC는 **LLM이 보지 않는다** — 결정론적 빌드 품질 게이트 전용
- TEMS는 **개발자가 직접 편집하지 않는다** — LLM 컨텍스트용 규칙 저장소
- 한 프로젝트에 둘 다 도입 가능. 충돌 없음 — 서로 다른 파일/DB/디렉토리 사용
- DVC의 특정 case가 반복 실패하면(예: `--audit-cases`로 카테고리 10+ 감지) → TEMS TGL로 승격 검토 가능. 단, 자동 bridge는 제공 안 함 (의도적 분리)

## 명명 규약 (혼동 방지)

| 용어 | 의미 |
|------|------|
| **DVC case** | `cases.json` 항목. CASE_ID로 식별 (예: `DISPLAY_HUMANIZE_001`) |
| **DVC checker** | `chk_*.py` 내 `check_*` 메서드 |
| **DVC bypass** | `# chk:skip CASE_ID 사유` 주석 |
| **TEMS TCL** | `memory/error_logs.db` 의 `category='TCL'` 규칙. 번호 체계 `#N` |
| **TEMS TGL** | 동일 DB의 `category='TGL'` 규칙. 7-카테고리 분류 |

문서/대화에서 반드시 **"DVC case #ID"** vs **"TEMS TCL #N"** 접두사를 사용해 구분.
