# DVC Architecture — 설계 원리

## 출발점

DVC는 **추상적 설계의 산물이 아니다**. DnT_Fermion 프로젝트(코드군)에서 2026-03-17 단일 인시던트 후 13개 case가 귀납적으로 추출되면서 귀결된 구조를 일반화한 것이다. "실전 귀납 설계"가 이 프레임워크의 정체성.

## 핵심 원리 10가지

### 1. 일반화 우선 (Generalize-First)

단일 버그는 규칙이 아니다. `cases.json` 의 `generalized` 필드는 반드시 *유사 사례까지 포착하는 위상*으로 작성한다.

- 나쁜 예: "2026-03-17 BlastCombiner 페이지에 종목코드만 표시" (단일 인스턴스)
- 좋은 예: "모든 사용자 대면 UI에서 내부코드가 사람이 읽을 수 있는 이름으로 변환되고 있는지" (위상)

구현(checker)은 정규식 + scope 기반이므로 자연스럽게 다수 위치를 커버한다.

### 2. Origin Bug 보존 (Why-First)

각 case 에 `origin_bug: "2026-03-17 자본비중 0.5 하드코딩 — CS 연동 무시됨"` 필드 필수. 규칙의 *왜*를 코드에 묻어둠으로써:

- 미래에 케이스가 쓸모없어졌을 때 근거 추적 가능 (archive 판단 재료)
- 신규 개발자 onboarding 시 맥락 설명
- 비슷한 버그 재발 시 기존 case 로 해결되는지 먼저 확인

### 3. 바이패스는 사유 필수

`# chk:skip CASE_ID 사유` 패턴. 사유 없이 `chk:skip CASE_ID` 만 쓰면 **바이패스 무효** ([base.py](templates/base.py#L183)). 이유:

- 예외 허용하되 설명 책임 강제
- `--audit-bypass` 감사 시 사유가 없으면 정책 위반 탐지
- 과거의 "왜 여기는 예외인가"를 미래가 알 수 있게

**바이패스 20건 초과 시 경고** — 예외가 규칙화되기 전 압박.

### 4. 생명주기 임계값 자동 제안

| 임계값 | 값 | 동작 |
|--------|---|------|
| 카테고리당 케이스 | 10개 | 통합 검토 제안 |
| 전체 케이스 | 50개 | 통합 검토 제안 |
| 미탐지 기간 | 30일 | archive 후보 |

임계값 초과 시 `audit_cases()` 가 자동으로 통합 제안 출력. 케이스 팽창 억제.

### 5. 결정론적 반복성

`BaseChecklist.run()` 이 `check_*` 메서드를 자동 수집 → 순차 실행 → `CheckReport` 집계. 같은 입력 → 같은 출력. **예외도 이벤트로 포착** (HIGH severity CheckResult 로 변환) — 침묵 실패 방지.

### 6. 풍부한 결과 스키마 (CheckResult 8필드)

```
case_id, title, severity, passed, detail, file_path, line_number, suggestion
```

특히 `suggestion` 필드는 **linter가 fixer 역할도 겸함**. 실패만 보고하는 게 아니라 *어떻게 고치라는 지침* 제공.

### 7. 5단계 Severity

CRITICAL / HIGH / MEDIUM / LOW / INFO — 배포 차단과 경고를 분리할 수 있다. CI 통합 시 `--strict` 플래그로 "HIGH 이상 실패 시 exit 1" 같은 게이트 가능.

### 8. 정적 분석 + 데이터 검증 + 배포 검증 통합

한 프레임워크로 3영역 모두 다룬다:
- 코드 패턴 스캔 (`find_pattern_in_file`, `get_all_py_files`)
- 데이터 파일 검증 (JSON 스키마, 신선도, 파이프라인 체인)
- 배포 정합성 (SSH 해시 비교, crontab 확인 — 선택적)

별도 도구 분산이 아니라 **단일 실행기**로 통합된다.

### 9. 자동 Discovery

원조 Fermion 은 `CHECKLIST_REGISTRY.update({...})` 하드코딩 방식이었지만, DVC 는 `discover_checklists()` 로 `chk_*.py` 자동 스캔 → `BaseChecklist` 서브클래스 자동 등록. **새 checker 추가 시 runner 수정 불필요**.

### 10. 메타 자기점검 (Self-Referential Audit)

체크리스트 자체를 체크리스트가 점검:
- `--audit-bypass`: 전체 바이패스 현황 + 20건 초과 경고
- `--audit-cases`: 카테고리/총합 임계값 초과 + auto_discover 비율

시스템이 스스로의 건강도를 보고한다. 운영자 개입 최소화.

## 파일 구조 요약

```
{project_root}/
├── dvc_config.json             (선택) 경로 커스터마이징
├── docs/
│   └── BUILD_VERIFICATION.md   DVC 정체성 + TEMS TCL 과의 구분 선언
├── src/
│   └── checklist/              패키지
│       ├── __init__.py
│       ├── base.py             BaseChecklist + CheckResult + bypass
│       ├── runner.py           CLI + discover_checklists + audit
│       ├── cases.json          케이스 레지스트리
│       └── chk_*.py            도메인별 checker 모듈
└── logs/
    └── checklist/              결과 저장 디렉토리
        └── checklist_{date}.json
```

## 실행 흐름

```
python -m checklist.runner
   ↓
discover_checklists()           → chk_*.py 스캔, BaseChecklist 서브클래스 수집
   ↓
run_checklists()                → 각 모듈 인스턴스화 후 .run() 호출
   ↓
BaseChecklist.run()             → check_* 메서드 자동 수집 → 순차 실행
   ↓
CheckReport                     → format_console_report()
                                → save_report() → logs/checklist/checklist_{date}.json
```

## TEMS 와의 명시적 경계

**DVC 는 LLM 이 보지 않는다.** 결과가 prompt 에 주입되지 않으며, hook 에 연결되지 않는다. 개발자·CI·cron 이 소비하는 **결정론적 빌드 품질 게이트**다.

**TEMS 는 개발자가 편집하지 않는다.** 규칙은 `tems_commit.py` 를 통해서만 등록되며, preflight hook 이 자동 주입한다. LLM agent 의 행동 교정 레이어다.

한 프로젝트에 둘 다 도입 가능. 서로 다른 파일/DB/디렉토리를 사용하므로 충돌 없음. 이름 충돌을 피하기 위해 **DVC 는 case, TEMS 는 rule** 로 명명 구분한다.

## 확장 가이드 (Fermion 에서 누적된 패턴)

새 checker 모듈을 추가할 때 고려사항:

1. **Scope 명시** — `scope` 메타필드에 대상 경로를 구체적으로. `src/**/*.py` 보다 `src/pages/*.py` 가 낫다.
2. **Allowlist 설계** — `_HARDCODE_ALLOW`, `_PRINT_ALLOW_FILES` 같이 예외 허용 경로를 class 변수로 분리.
3. **정규식 + 컨텍스트** — 라인 단위 매칭 후 주변 ±N 줄 스캔하여 false positive 억제. 원조 `chk_display.py` 의 `name_resolve_re` context 스캔 패턴 참조.
4. **바이패스 존중** — `filter_bypassed()` 로 `# chk:skip` 라인 제거 필수.
5. **Suggestion 필수** — 실패 시 "어떻게 고치라"를 반드시 제공.
6. **Passed 케이스도 보고** — 모든 점검 통과 시에도 `CheckResult(passed=True, detail="N개 파일 점검 완료")` 반환하여 침묵 방지.

## 한계 및 절제

DVC 는 **AST 파서가 아니다**. 정규식 기반이므로 리팩토링에 약하다. 중요 규칙은 AST 기반으로 승격하는 것이 이상적이나, 운영 현장의 현실적 타협으로 정규식 + 컨텍스트 + 바이패스를 조합한다.

**병렬화 부재** — 현재는 순차 실행. 체크리스트 50+ 확장 시 `concurrent.futures` 도입 검토 필요.

**의존성 그래프 없음** — checker 간 순서 의존은 표현 불가. 필요 시 별도 DAG 레이어 위에 구축해야 한다.
