---
date: 2026-04-20
status: Active
scope: all-projects
tags: [dvc, tems, disambiguation, terminology]
---

# Concept — DVC vs TEMS 분리 기준

## 정의

DVC와 TEMS는 모두 "누적 학습을 통해 미래 오류를 방지"하는 시스템이지만,  
**층위, 대상, 실행 시점이 완전히 다르다.**  
S33에서 DVC case를 "TEMS 체크리스트"로 지칭하다 TCL과 혼용되는 실제 사고가 발생했으며,  
이를 계기로 용어 및 시스템을 정식 분리했다.

## 출처 문헌

S33 사고 — DVC를 TEMS TCL 용어로 혼용하던 관행이 preflight 오주입 혼란을 유발.  
2026-04-20 S33/S34에서 시스템 분리 + 용어 정식화.

## 핵심 대조표

| 축 | DVC | TEMS TCL |
|---|---|---|
| **대상** | 빌드·배포·데이터 결정론 | LLM 에이전트 행동 교정 |
| **타이밍** | build-time (정적·실행) | runtime (preflight/hook, 매 prompt) |
| **저장소** | `src/checklist/cases.json` + `chk_*.py` | `memory/error_logs.db` (SQLite FTS5) |
| **ID 형식** | `CATEGORY_NAME_001` (대문자) | `#N` (정수, 예: TCL #113) |
| **실행** | `python -m checklist.runner` (결정론적) | preflight_hook 자동 주입 (의미 매칭) |
| **검증 방식** | 정적 분석 + 파일 패턴 + 해시 비교 | BM25 + CUDA dense semantic 매칭 |
| **소비자** | 개발자, CI 서버, cron | LLM agent (Claude) |
| **LLM 관여** | 없음 (완전 결정론적) | 있음 (preflight·bridge·retrospective) |
| **일반화 단위** | case (regression test) | rule (behavioral guard) |
| **원조 에이전트** | 코드군 (FermionQuant) | 위상군 |

## 접두사 규약 (혼동 방지 필수)

| 시스템 | 올바른 지칭 | 잘못된 지칭 |
|--------|-----------|-----------|
| DVC | **"DVC case DISPLAY_HUMANIZE_001"** | "TCL #001", "체크리스트 TCL" |
| TEMS TCL | **"TEMS TCL #113"** | "DVC TCL", "케이스 #113" |

문서·대화에서 "TCL"이라는 단어는 **항상 TEMS TCL**을 의미한다.  
DVC 점검 항목은 반드시 **"case"**로 지칭한다.

## 공통점 (혼동의 근원)

- 둘 다 **누적 학습** — 버그·실수를 축적해 미래 회귀 방지
- 둘 다 **일반화 원칙** 적용 — 개별 수정이 아닌 패턴 추출
- 둘 다 **위상군 워크스페이스**에서 운영 중

이 공통 목적이 초기에 혼용을 유발했으나, 레이어(빌드 vs. LLM 런타임)가 명확히 다르다.

## 이 프로젝트 내 적용처

```
위상군 워크스페이스:
  DVC    → src/checklist/   (빌드 검증, python -m checklist.runner)
  TEMS   → memory/          (LLM 행동, preflight_hook 자동 발동)
```

## 주의점

- DVC case를 `memory/error_logs.db`에 등록하지 말 것 (TEMS는 LLM 행동 규칙만)
- TEMS TCL을 `cases.json`으로 옮기지 말 것 (결정론 보장 불가)
- `--audit-bypass`는 DVC 전용 명령 — TEMS에 해당 없음

## 관련 개념

[[DVC]] [[TEMS]] [[TCL_vs_TGL]]

## 참조

- [[DVC]] — DVC 전체 정의 및 파일 구조
- [[TEMS]] — TEMS 전체 정의 및 아키텍처
- [[TCL_vs_TGL]] — TEMS 내부 TCL vs TGL 분류 기준
