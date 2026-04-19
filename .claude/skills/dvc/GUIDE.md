# DVC 운영 가이드

## 1. 신규 프로젝트에 DVC 도입

### 자동 스캐폴딩

```bash
python E:/DnT/DnT_WesangGoon/.claude/skills/dvc/init.py /path/to/project
```

생성 결과:
```
/path/to/project/
├── dvc_config.json          (경로 커스터마이징용, 필요 시 편집)
├── docs/
│   └── BUILD_VERIFICATION.md
└── src/
    └── checklist/
        ├── __init__.py
        ├── base.py
        ├── runner.py
        ├── cases.json
        └── chk_example.py
```

### 수동 설치 (init.py 사용 불가 시)

```bash
mkdir -p /path/to/project/src/checklist
cp templates/{base,runner,chk_example,__init__}.py /path/to/project/src/checklist/
cp templates/cases.json /path/to/project/src/checklist/
```

그 후 `/path/to/project/dvc_config.json` 작성:
```json
{
  "src_dir": "src",
  "data_dir": "data",
  "logs_dir": "logs",
  "scan_dirs": {
    "pages": "src/pages"
  }
}
```

### 첫 실행 검증

```bash
cd /path/to/project
python -m checklist.runner --list       # 등록된 모듈 확인 (example 만 있어야 함)
python -m checklist.runner --module example
```

---

## 2. 새 Case 추가 절차 (반복 버그 발견 시)

### 3-step workflow

**Step 1 — `cases.json` 에 메타데이터 등록**

```json
{
  "case_id": "CONFIG_HARDCODE_001",
  "category": "config",
  "title": "환경변수 하드코딩 탐지",
  "generalized": "환경변수 대신 하드코딩된 API 키/URL/경로가 실행 모듈에 남아있지 않은지",
  "origin_bug": "2026-04-20 API_KEY 하드코딩 커밋 사고 — 리포지토리 공개 후 revoke",
  "checker": "chk_config.py → check_config_hardcoded_secrets",
  "scope": "src/*.py (test_*, config.py 제외)",
  "auto_discover": true,
  "added_date": "2026-04-20",
  "severity": "HIGH"
}
```

필수 필드:
- `case_id` — UPPER_SNAKE + _NNN 번호. prefix 매칭이므로 계층 구조 가능
- `generalized` — **단일 사례가 아닌 위상**으로 서술
- `origin_bug` — 왜 추가했는지, 언제
- `checker` — 구현 메서드 경로 (문서화용, 실제 매칭은 자동)

**Step 2 — `chk_<category>.py` 에 메서드 구현**

```python
class ConfigChecklist(BaseChecklist):
    module_name = "config"

    def check_config_hardcoded_secrets(self) -> list[CheckResult]:
        """CONFIG_HARDCODE_001: API 키/URL/토큰 하드코딩 탐지."""
        results = []
        py_files = self.get_all_py_files(SRC_DIR)
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']{20,}', "API 키"),
            (r'(?:password|token|secret)\s*=\s*["\'][^"\']{8,}', "시크릿"),
        ]

        for py_file in py_files:
            if py_file.name in ("config.py",) or py_file.name.startswith("test_"):
                continue
            for pattern, desc in secret_patterns:
                hits = self.find_pattern_in_file(py_file, pattern, re.IGNORECASE)
                hits = self.filter_bypassed(py_file, hits, "CONFIG_HARDCODE")
                if hits:
                    results.append(CheckResult(
                        case_id="CONFIG_HARDCODE_001",
                        title=f"{desc} 하드코딩: {py_file.name}",
                        severity="HIGH",
                        passed=False,
                        detail=f"L{hits[0][0]}: {hits[0][1][:60]}",
                        file_path=str(py_file),
                        line_number=hits[0][0],
                        suggestion="환경변수(os.environ[...]) 또는 비밀 관리 서비스 사용",
                    ))

        if not results:
            results.append(CheckResult(
                case_id="CONFIG_HARDCODE_001",
                title="시크릿 하드코딩 점검",
                severity="HIGH",
                passed=True,
                detail=f"{len(py_files)}개 파일 점검 완료, 하드코딩 없음",
            ))
        return results
```

**Step 3 — 로컬 검증**

```bash
python -m checklist.runner --module config
```

- 실패 케이스가 원조 버그를 재현하는지 확인
- 허위 양성(false positive) 이 과다하면 allowlist 또는 `# chk:skip` 추가
- `--audit-bypass` 로 바이패스 누적 감시

---

## 3. 바이패스 규약

### 기본 형태

```python
secret = "hardcoded_for_local_testing"  # chk:skip CONFIG_HARDCODE 개발환경 전용 더미값
```

- `chk:skip` → `#` 뒤 공백 하나 이상
- `CASE_ID` → prefix 매칭 (CONFIG_HARDCODE 로 쓰면 CONFIG_HARDCODE_001, CONFIG_HARDCODE_002 모두 바이패스)
- 사유 → **필수**. 없으면 바이패스 무효

### 바이패스 감사

```bash
python -m checklist.runner --audit-bypass
```

출력 예:
```
📋 chk:skip 바이패스 감사 보고
  src/dashboard.py:L47 — [DISPLAY_HUMANIZE] yfinance API 용 ticker
  src/api_client.py:L12 — [CONFIG_HARDCODE] 로컬 테스트용 더미
  ...
총 15건 바이패스
```

20건 초과 시 자동 경고 — 케이스 통합 검토 시그널.

---

## 4. 케이스 생명주기 관리

### 자동 분석

```bash
python -m checklist.runner --audit-cases
```

출력:
```
총 케이스: 18개
카테고리: 4개
  ⚠️ display: 11개   ← 카테고리당 10개 초과 경고
  ✅ config: 4개
  ✅ telegram: 2개
  ✅ deploy: 1개

자동탐지: 15/18 (83%)

📌 통합 제안:
  🔄 [display] 11개 > 10개 임계 — 카테고리 내 통합 검토
```

### 통합 절차

1. 같은 카테고리에서 유사한 `generalized` 를 가진 case 들을 찾는다
2. 상위 개념의 새 case_id 로 통합 (예: `DISPLAY_HUMANIZE_001~005` → `DISPLAY_HUMANIZE`)
3. 기존 `# chk:skip` 주석은 prefix 매칭 덕에 자동 호환
4. 구 case_id 는 `cases.json` 에서 제거 + checker 메서드 병합

### Archive 후보

`auto_discover=true` 인 case 인데 30일 간 failed 탐지 0건이면 archive 후보. 수동으로:
1. 최근 30일치 `logs/checklist/checklist_*.json` 스캔
2. 해당 case 의 failed 기록 0 → archive 제안
3. `cases.json` 에서 제거하거나 `archived: true` 플래그 추가 (스키마 확장 시)

---

## 5. CI / cron 통합

### GitHub Actions 예시

```yaml
- name: DVC Build Verification
  run: |
    python -m checklist.runner --json > dvc_report.json
    python -c "
    import json, sys
    data = json.load(open('dvc_report.json'))
    failed_critical = sum(
        1 for r in data for res in r['results']
        if not res['passed'] and res['severity'] in ('CRITICAL', 'HIGH')
    )
    sys.exit(1 if failed_critical else 0)
    "
```

### cron 예시 (Linux/macOS)

```cron
# 매일 09:00 빌드 검증 + 결과를 Slack 으로
0 9 * * * cd /project && python -m checklist.runner > /tmp/dvc_$(date +\%F).log 2>&1
```

### Windows Task Scheduler

```
프로그램: python
인수: -m checklist.runner
시작 폴더: C:\project
트리거: 매일 09:00
```

---

## 6. 실전 팁

- **새 checker 작성 시** — 기존 `chk_display.py` 의 `_scan_ticker_only_display` 컨텍스트 ±5줄 스캔 패턴을 참조. 정규식만으로는 false positive 통제 어렵다.
- **파일 범위 한정** — class 변수 `_TARGETS = [SRC_DIR / "file1.py", ...]` 로 대상 파일을 명시하는 것이 `get_all_py_files()` 보다 정확하다.
- **Passed 케이스도 1건** — 침묵 실패 방지. 전체 통과 시에도 `CheckResult(passed=True, detail="N개 점검 완료")` 반환.
- **Suggestion 은 `어떻게` 까지** — "수정 필요" 가 아니라 "`int(float(val))` 사용" 같이 구체적 치환형.

---

## 7. TEMS 와의 상호 작용

- **DVC case 반복 실패 → TEMS TGL 승격 검토**: 같은 case 가 30일 동안 15+ 건 failed 누적되면 해당 패턴은 LLM 행동 교정으로도 처리할 가치. TEMS TGL-P (Pattern Reuse) 로 수동 등록 고려.
- **자동 승격 없음**: 두 시스템은 의도적으로 독립. 개발자가 판단하여 승격.
- **이름 혼동 방지**: 문서/대화에서 반드시 **"DVC case #ID"** vs **"TEMS TCL #N"** 접두사 사용.
