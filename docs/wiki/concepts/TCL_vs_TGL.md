---
date: 2026-04-20
status: Active
phase: Phase-2
scope: wesang-all-agents
tags: [tems, tcl, tgl, classification, rule-type, bm25, dense-retrieval]
---

# Concept — TCL vs TGL (좁은 규칙 vs 넓은 위상 패턴)

## 정의

TEMS 규칙은 일반화 수준에 따라 두 가지 타입으로 분리된다.

**TCL (Topological Checklist Loop):**  
사용자가 명시적으로 지정한 국지적·케이스 한정 규칙. 체크리스트처럼 작동.

**TGL (Topological Guard Loop):**  
누적 실수·심각 사고에서 추출한 카테고리 차원의 가드. 유사 사례 다수를 함께 차단.

## 출처 문헌

경험적 도출 — 위상군 S31 Phase 2 게이트 설계.  
v2026.4 재정의: 프로토콜 `.claude/rules/tems-protocol.md` 참조.

## 이 프로젝트 내 적용처

### 비교표

| 축 | TCL | TGL |
|----|-----|-----|
| **본질** | 명시적 사용자 지시 | 누적 실수에서 추출한 패턴 |
| **등록 트리거** | "앞으로/이제부터/항상/반드시" 명시 | 동일 시그니처 N≥5회 또는 종일군 명시 |
| **일반화 수준** | L1 Concrete Pattern | L2 Topological Case (sweet spot 강제) |
| **발동 메커니즘** | BM25 키워드 매칭(1차) | dense semantic(1차) + BM25(보강) |
| **필수 슬롯** | `correction_rule` + `keyword_trigger` | `classification` + `topological_case` + `forbidden_action` + `required_action` + `verification` |
| **검증 게이트** | A(schema) + 키워드 다양성 | A+B 거부형, C+D+E 경고형 |
| **예시** | 종일군 명명규칙(#47), 세션종료 핸드오버(#4) | 외부 패키지 검증(#92), useEffect deps(#54) |

### 등록 명령어

```bash
# TCL 등록 (BM25 키워드 중심)
python memory/tems_commit.py --type TCL \
  --rule "규칙 본문 (200자 이내 권장)" \
  --triggers "키워드1,키워드2,동의어3" \
  --tags "project:wesang,domain:XXX"

# TGL 등록 (7-카테고리 분류 포함)
python memory/tems_commit.py --type TGL \
  --classification TGL-D \
  --topological_case "외부 의존성 부재 시 런타임 예외" \
  --forbidden "미검증 패키지 import" \
  --required "pip show + import 테스트 선행" \
  --tags "project:wesang"
```

### 일반화 수준 (L0~L4)

| 레벨 | 설명 | TEMS 허용 |
|------|------|----------|
| L0 | 완전 구체 (1회성 사례) | TCL만 |
| L1 | 변수 추출 (Concrete Pattern) | TCL 적합 |
| **L2** | **위상 케이스 (Topological Case)** | **TGL sweet spot** |
| L3 | 도메인 초월 원리 | TGL 허용 (경고) |
| L4 | 철학적 추상 | 거부 |

### 검증 게이트

**TCL 게이트:**
- Gate A: 스키마 검증 (필수 슬롯 완성도)
- 키워드 다양성 검사 (keyword_trigger 80% 이상 커버)

**TGL 게이트:**
- Gate A (거부형): 스키마 + 분류 완성도
- Gate B (거부형): L0/L4 추상화 수준 거부
- Gate C (경고형): 중복 탐지
- Gate D (경고형): 재현성 검증
- Gate E (경고형): 검증 가능성

## 주의점

- TCL 키워드 희소 시 BM25 미발동 위험 → `keyword_trigger` 동의어 5개 이상 권장
- TGL에 L1 Concrete를 등록 시도하면 Gate B가 거부 — TCL로 재등록 필요
- TCL과 TGL을 혼용 등록 금지 (분류 명확히 선택 후 등록)
- `<rule-detected type="TCL">` / `<rule-detected type="TGL">` 힌트 발생 시 즉시 등록

## 관련 개념

[[TEMS]] [[../patterns/Classification_7_Category]] [[Self_Containment(TEMS 자기완결성)]]

## 참조

- [[TEMS]] — TEMS 시스템 전체 정의 및 아키텍처
- [[../patterns/Classification_7_Category]] — TGL 7-카테고리 분류 상세
- [[Self_Containment(TEMS 자기완결성)]] — self-contained 이식 원리
- [[DVC_vs_TEMS]] — DVC case vs TEMS TCL 용어 분리 기준
