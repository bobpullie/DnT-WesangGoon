---
date: 2026-04-20
status: Active
scope: all-projects (dogfood in wesang)
tags: [dvc, build-verification, checklist, deterministic, cases]
---

# Concept — DVC (Deterministic Verification Checklist)

## 정의

DVC는 프로젝트별 **결정론적 빌드 검증 프레임워크**다.  
정적 분석 + 데이터 파일 검증 + 배포 정합성 점검을 하나의 checklist 시스템으로 통합하여,  
누적 버그를 개별 수정이 아닌 **case로 일반화**해 영구 회귀 방지 장치를 만든다.

**DVC ≠ TEMS TCL — 절대 혼동 금지.** 상세 분리 기준: [[DVC_vs_TEMS]]

## 출처 문헌

코드군(FermionQuant) 원조 TCL — 빌드 검증 체크리스트가 축적되며 일반화 요청.  
2026-04-20 S33: 위상군 프로젝트 로컬 스킬 `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/` 로 추출·정식화 + dogfood 설치.  
글로벌(`~/.claude/skills/dvc/`) 승격 및 타 에이전트 이식: 1~2세션 관찰 후 결정 (현재 미결).  
결정 이력: [[../decisions/2026-04-20_dvc-skill-promotion]]

## 이 프로젝트 내 적용처

**파일 구조 (위상군 dogfood):**

```
src/checklist/
├── __init__.py
├── base.py          BaseChecklist + CheckResult + 바이패스 시스템
├── runner.py        CLI + 자동 discovery + 감사 도구
├── cases.json       케이스 레지스트리 (case ID, category, origin_bug 등)
└── chk_*.py         도메인별 checker 모듈 (카테고리 1개당 1파일)
```

**실행 방법:**

```bash
python -m checklist.runner                    # 전체 점검
python -m checklist.runner --module example   # 특정 모듈만
python -m checklist.runner --list             # 등록된 모듈 목록
python -m checklist.runner --audit-bypass     # 바이패스 감사
python -m checklist.runner --audit-cases      # 케이스 생명주기 분석
```

**Case ID 형식:**

`CATEGORY_NAME_NNN` — 대문자 카테고리 + 동사형 이름 + 3자리 번호.  
예: `DISPLAY_HUMANIZE_001`, `CONFIG_HARDCODE_001`, `EXAMPLE_README_001`

바이패스 허용 시: `# chk:skip DISPLAY_HUMANIZE_001 사유` (사유 필수, prefix 매칭 지원)

## 핵심 설계 원칙

1. **결정론 — 랜덤·LLM 판정 금지.** 동일 입력 → 항상 동일 결과.
2. **빠른 피드백.** 각 case 실행 목표: 1초 이내.
3. **일반화 우선.** 버그 발견 시 개별 수정 전에 "같은 부류 재발 가능성?" 질문.
4. **원점 보존 (`origin_bug`).** 케이스가 왜 생겼는지 이유를 반드시 기록.

## 주의점

- **anti-pattern:** LLM 판정에 의존하는 case → TEMS TGL 영역으로 이전
- **anti-pattern:** 수정 없이 케이스만 등록하여 green 체크 가짜 증가
- **anti-pattern:** 환경 의존(네트워크·랜덤 시드) case → 비결정론, DVC 범위 밖

## 관련 개념

[[DVC_vs_TEMS]] [[../patterns/DVC_Case_Lifecycle]] [[../principles/Case_Generalization]] [[../decisions/2026-04-20_dvc-skill-promotion]]

## 참조

- [[DVC_vs_TEMS]] — DVC와 TEMS TCL 혼동 방지 대조표
- [[../patterns/DVC_Case_Lifecycle]] — 버그 발견 → case 일반화 → 회귀 방지 순환
- [[../principles/Case_Generalization]] — 일반화 우선 원리 (왜 case로 만드는가)
- [[../decisions/2026-04-20_dvc-skill-promotion]] — 스킬 승격 + 위상군 dogfood 결정
