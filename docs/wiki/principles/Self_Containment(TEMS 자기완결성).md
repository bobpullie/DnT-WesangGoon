---
date: 2026-04-20
status: Active
phase: Wave-1-Standard
scope: tems-all-deployments
tags: [tems, self-contained, dependency, isolation, portability, tgl-92]
---

# Principle — Self-Containment (TEMS 자기완결성)

## 원리 본문

TEMS 시스템은 프로젝트 루트의 `memory/` 디렉토리만으로 완결되어야 한다.  
외부 PyPI 패키지(`tems`, `tems_core` 등)를 `import`하는 코드는 `memory/` 내에 존재할 수 없다.

**검증 명령어:**
```bash
grep -rn "^import tems\|^from tems" memory/
# 결과 0건이어야 함
```

허용 범위: Python 표준 라이브러리 (`sqlite3`, `json`, `subprocess`, `pathlib` 등)  
금지 범위: `pip install` 기반 외부 패키지 (단, 표준 라이브러리 제외)

## 일반화 범위

모든 TEMS 이식·배포에 적용. Wave 1 이식 시 첫 번째 체크 항목.  
`memory/` 외부 파일(hook scripts, CLAUDE.md)에도 동일 원칙 적용.

## 도출 근거

**TGL #92 (외부 패키지 검증):**  
`tems` PyPI 패키지를 외부 의존으로 사용하다가 패키지 부재/버전 drift로 여러 에이전트에서 장애 발생.  
S29 사고 분석 결과 "TEMS 개선은 위상군에서 먼저 검증 후 전파" 결정과 함께 self-contained 전환 결정.

**코드군 Wave 1 이식 (S33):**  
`memory/` 10 모듈을 복사하고 외부 `tems` 패키지 참조를 제거하는 것이 이식의 첫 단계였음.  
이식 완료 후 외부 의존 0건 확인 → 원칙 타당성 재확인.

**이식 용이성 실증:**  
`memory/` 디렉토리 복사 한 번으로 TEMS 기능 완전 이전 가능.  
외부 패키지 없으므로 환경 차이(OS, Python 버전)에 강건함.

**버전 drift 방지:**  
각 에이전트가 독립적으로 `memory/` 관리 → 업그레이드 타이밍을 에이전트별로 제어 가능.  
중앙 패키지 업그레이드로 여러 에이전트 동시 파손 위험 제거.

## 예외 조건

- `requirements.txt`에 명시된 분석/ML 라이브러리(`numpy`, `scipy` 등)는 `memory/` 스코프 밖이므로 해당 없음
- `memory/` 내에서 `subprocess`로 외부 바이너리 호출은 허용 (시스템 레벨, pip 패키지 아님)
- 현재 알려진 예외: 없음

## 관련 원리

[[../decisions/2026-04-20_wave1-standardization]] [[../concepts/TEMS]]

## 참조

- [[../concepts/TEMS]] — TEMS 시스템 전체 정의
- [[../decisions/2026-04-20_wave1-standardization]] — Wave 1 표준화 결정 (self-contained 이식 포함)

---
_승격 승인일: 2026-04-20_
_승인자: 종일군_
