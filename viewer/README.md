# TEMS Rule Viewer

위상군 TEMS 규칙들을 **별도 네이티브 윈도우**에서 모니터링/편집하는 옵션 패키지.

## 핵심 설계

- **격리:** TEMS core 는 이 디렉터리를 import 하지 않음. `viewer/` 통째로 삭제해도 TEMS 정상 작동.
- **단방향 데이터 흐름:** viewer → `rule_user_annotations` 테이블 + `memory/user_annotations.jsonl` 백업. 기존 `memory_logs` / `qmd_rules` 무수정.
- **에이전트 컨텍스트 0:** 슬래시 명령(`/tems-view`)이 viewer 를 detached subprocess 로 실행 → viewer 출력은 GUI 윈도우에만 표시 → 에이전트 컨텍스트엔 PID 만.
- **선택 설치:** NiceGUI + pywebview 의존성. 안 깔면 슬래시 명령이 친절히 안내.

## 설치

```bash
pip install -r viewer/requirements.txt
```

설치 후 자동으로 다음이 가능:
- DB 의 `rule_user_annotations` 테이블 (없으면 viewer 첫 실행 시 자동 생성)
- `memory/user_annotations.jsonl` (편집 이벤트 append-only 백업, git tracked 권장)

## 실행 방법

### 1. 슬래시 명령 (권장)

Claude Code 안에서:
```
/tems-view
```
→ 별도 OS 윈도우로 viewer 가 뜨고, 에이전트 컨텍스트엔 PID 한 줄만 남음.

### 2. 직접 실행 (셸)

```bash
python viewer/rule_viewer.py            # 네이티브 윈도우 (pywebview)
python viewer/rule_viewer.py --browser  # 브라우저 모드 (디버그용, http://localhost:8765)
```

## 기능

| 기능 | 동작 |
|---|---|
| 테이블 뷰 | ID / Category / Status / Fire / Viol/Comp / THS / Rule preview / 코멘트 |
| 필터 | All · TCL · TGL · hot · warm · cold · archive · commented · disabled |
| 검색 | rule 텍스트 / tags / triggers / 코멘트 부분 일치 |
| 행 더블클릭 | 본문 + 메타 + 코멘트 편집 모달 |
| Save | `rule_user_annotations` upsert + JSONL append |
| Severity | `info` / `warn` / `disable` 라디오 |
| Archive | 소프트 삭제 (`status='archive'`) — TEMS lifecycle 종착 |
| Hard Delete | `memory_logs` + `rule_health` + `qmd_rules/rule_NNNN.md` 영구 제거 |
| Auto-refresh | 5초 주기 토글 (기본 OFF) |

## Severity 의미 (preflight 연동)

종일군 코멘트 + severity 는 **preflight_hook 가 매칭된 규칙 옆에 자동 주입**. 향후 에이전트(=위상군 등)가 규칙 발동 시 코멘트를 함께 본다.

| Severity | preflight 동작 |
|---|---|
| `info` | 규칙 텍스트 아래 `💬 [종일군 코멘트]: ...` 한 줄 추가 |
| `warn` | `⚠ [종일군 코멘트 — WARN]: ...` 강조 — 에이전트 우선 고려 |
| `disable` | 해당 규칙을 preflight 주입에서 **완전히 제외** (소프트 비활성화). 규칙 자체는 DB 에 보존되어 언제든 severity 변경으로 재활성 가능 |

## DB 스키마

```sql
CREATE TABLE rule_user_annotations (
    rule_id      INTEGER PRIMARY KEY,
    comment      TEXT    NOT NULL DEFAULT '',
    severity     TEXT    NOT NULL DEFAULT 'info'
                 CHECK(severity IN ('info', 'warn', 'disable')),
    author       TEXT    NOT NULL DEFAULT 'jongil',
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (rule_id) REFERENCES memory_logs(id) ON DELETE CASCADE
);
```

## 백업 / 복원

`memory/user_annotations.jsonl` 은 모든 편집 이벤트 append-only 로그:
```jsonl
{"action": "upsert", "rule_id": 92, "comment": "...", "severity": "warn", "updated_at": "..."}
{"action": "delete_annotation", "rule_id": 92, "updated_at": "..."}
{"action": "archive", "rule_id": 75, "updated_at": "..."}
{"action": "hard_delete", "rule_id": 12, "updated_at": "..."}
```

DB 손상으로 `rebuild_from_qmd` 를 돌린 뒤, 이 JSONL 을 replay 하면 코멘트/severity 복원 가능.

## 제거

```bash
# 1. viewer 디렉터리 삭제
rm -rf viewer/

# 2. (선택) annotation 데이터도 삭제하려면
sqlite3 memory/error_logs.db "DROP TABLE IF EXISTS rule_user_annotations;"
rm -f memory/user_annotations.jsonl
```

→ TEMS 100% 정상 작동 (preflight_hook 의 LEFT JOIN 은 테이블 없으면 빈 결과 반환하도록 try/except 처리됨).

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `ModuleNotFoundError: nicegui` | `pip install -r viewer/requirements.txt` |
| 윈도우 안 뜨고 브라우저로 열림 | pywebview 미설치. 위와 동일 |
| DB lock | preflight 와 동시 실행 중. WAL 모드라 일반적으로는 충돌 안 남. 이상하면 viewer 닫고 재시도 |
| 행 더블클릭 무반응 | 브라우저 콘솔(`--browser` 모드) 또는 viewer 윈도우 로그 확인. NiceGUI 버전 호환성 의심 |
| Hard Delete 후 규칙 다시 나타남 | `tems_commit.py` 가 외부에서 동일 ID 로 재등록한 경우. ID 충돌 방지 위해 archive 권장 |
