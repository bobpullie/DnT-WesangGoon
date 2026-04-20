---
date: 2026-04-20
status: Accepted
phase: Dogfood
scope: wesang-dogfood
tags: [dvc, skill-promotion, dogfood, wesang]
---

# Decision — DVC 스킬 추출·정식화 + 위상군 dogfood (글로벌 승격 보류)

## 결정

DVC를 위상군 프로젝트 로컬 스킬 `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/` 로 추출·정식화하고 dogfood 설치한다.  
글로벌(`~/.claude/skills/dvc/`) 승격 및 타 에이전트 이식 판정은 **1~2세션 dogfood 관찰 후** 결정한다 (현재 미결).

## 배경

**코드군(FermionQuant) 기원:** 빌드 검증 체크리스트가 코드군에서 축적되며,  
다른 프로젝트도 동일 패턴이 필요하다는 판단이 들었다 (일반화 가치 확인).

**혼동 사고 발생:** DVC를 "TEMS 체크리스트"로 지칭하다 TEMS TCL과 혼용되는 사고 발생.  
시스템 분리 없이 확산하면 혼동이 심화될 위험 → 용어·시스템 정식 분리가 선행 필요.

## 대안 검토

| 옵션 | 설명 | 판정 |
|------|------|------|
| (α) 코드군 내부 유지 | 현상 유지, 다른 프로젝트는 별도 구현 | 확장 불가, 중복 발생 ❌ |
| (β) TEMS에 흡수 | DVC case를 TEMS TCL로 등록 | 혼동 심화, 결정론 보장 불가 ❌ |
| (γ) 별도 스킬 승격 + dogfood 검증 후 보편화 | 분리 유지, 검증 후 확산 | 위험 최소화 ✅ **선택** |

## 실행 내용 (S33)

**위상군 로컬 스킬 구조 (`E:/DnT/DnT_WesangGoon/.claude/skills/dvc/`) — 글로벌 미배포:**

- `SKILL.md` — 스킬 메타데이터 + 트리거 조건
- `ARCHITECTURE.md` — 설계 원리 10가지
- `GUIDE.md` — 새 case 추가 절차, 바이패스 규약, CI 통합
- `__init__.py` — 스킬 초기화 스크립트
- `templates/` — cases.json 템플릿, chk_template.py

**위상군 dogfood (`src/checklist/`):**

- scaffold 설치: `__init__.py`, `base.py`, `runner.py`, `cases.json`, `chk_example.py`
- baseline 3 cases (EXAMPLE 카테고리) + runner 전체 통과 확인

**코드군 원본 유지:** 기존 코드군 DVC 구현 보존 (분리 원칙)

## 판정 보류 조건

1~2세션 위상군 실사용 관찰 후 판단:
- 다른 에이전트(리얼군/디니군/어플군)도 동일 필요 확인 시 → 이식
- 위상군에서 문제 발생 시 → 스킬 설계 개선 후 확산

## 관련 결정

- [[2026-04-20_wave1-standardization]] — TEMS Wave 1 표준화 (병렬 표준화 트렌드)

## 참조

- [[../concepts/DVC]] — DVC 전체 정의
- [[../concepts/DVC_vs_TEMS]] — 분리 기준 (이 결정의 근거)
- [[2026-04-20_wave1-standardization]] — TEMS Wave 1 표준화 결정
