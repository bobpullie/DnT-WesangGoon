# Session 2 — 2026-04-21

> Source: `7ecf3bf2-e0fb-49ca-9b57-36d46143bc7f.jsonl`
> Generated: 2026-04-21 13:26:29

## Q1

위상군 어제 SDC가 모든 프롬프트에 트리거 조건을 탐색하는데 이걸 선택적으로 바꿔 줄수 있어? 규칙기반으로 SDC를 활성화할지 규칙기반+자동트리거 기반으로 활성화 할지 선택할수 있게 바꿔줄수 있어? 기본은 규칙기반으로 하고.

## A1

brainstorming 스킬을 사용해 SDC 트리거 선택화 설계를 먼저 정리할게. 시작 전 현재 SDC 트리거 구조를 파악하겠음.

## A2

현재 SDC 구조 파악됨. hook 쪽 구현도 확인하겠음.

## A3

현재 구조 파악됨. "모든 프롬프트에 트리거 탐색"은 [.claude/skills/SDC.md:15-31](.claude/skills/SDC.md#L15-L31)의 **§0 Auto-Dispatch Check** 섹션 — skill 자체 지침으로 LLM이 매 task마다 키워드 매칭을 자의적으로 수행하는 방식임. hook 레벨 gate는 따로 있음([memory/tool_gate_hook.py:226-265](memory/tool_gate_hook.py#L226-L265)).

요청을 설계로 옮기기 전에 "규칙기반"의 정의부터 맞추고 싶어. 두 해석이 가능한데:

**Q1. "규칙기반" 모드에서 SDC를 활성화시키는 신호는 구체적으로 뭐야?**

(a) **Hook 출력 기반** — preflight가 SDC 관련 TEMS 규칙(#86/#115/#117/#120 등)을 주입하거나, tool_gate_hook이 `<sdc-gate-alert>`를 띄운 경우에만 LLM이 3-question gate 수행. 즉 hook이 이미 컨텍스트에 신호를 주입했을 때만 반응.

(b) **특정 TEMS 규칙 슬롯 기반** — 규칙에 `sdc_trigger: true` 같은 슬롯을 달고, 그 슬롯을 가진 규칙이 fire됐을 때만 활성.

(c) **명시적 호출 기반** — 사용자가 `@SDC` 또는 slash command로 부를 때만. 그 외엔 skill §0 자체를 생략.

직관적으로는 (a) 같은데 — 이미 SDC 게이트 신호가 hook으로 다 들어오고 있어서 이걸 "규칙기반"의 정의로 쓰면 자연스럽거든. 이 해석 맞아? 아니면 다른 정의 염두에 둔 거 있어?

## Q2

아.. 지금 규칙등록된거 처럼 "앞으로 코드구현은 SDC활용하라." , "앞으로 git 커밋 배포는 SDC활용하라" 같이 규칙을 세우는 방식말야.

## A4

아 — 의도 이해됨. (b) 해석으로 가는 거구나. 즉:

> **TCL 한 줄 등록 → preflight가 task에 매칭되면 자동으로 SDC 활성**
> 그 외 task에서는 SDC §0 자체를 LLM이 무시 (매 prompt 키워드 탐색 X)

이건 깔끔해. TEMS preflight가 이미 BM25+dense로 selective 매칭하고 있으니까 SDC도 그 메커니즘에 얹으면 됨.

예시 흐름:
- 등록: `tems_commit --type TCL --rule "앞으로 git 커밋/배포는 SDC 활용" --triggers "git, commit, push, deploy, 배포"`
- 사용자: "이거 push 해줘" → preflight가 이 TCL을 매칭해서 주입 → LLM이 SDC §0 수행
- 사용자: "이 코드 설명해줘" → preflight 매칭 없음 → SDC §0 생략

**Q2. "확장 모드 (규칙기반 + 자동트리거)" 토글은 어떻게 할 거야?**

(a) **TCL 한 줄로 통합** — `"앞으로 모든 SDC 키워드 자동탐색 활성"` 같은 TCL을 등록하면 LLM이 SDC.md §0의 키워드 자동탐색을 켬. 등록 해제하면 끔. **별도 config 파일/CLI 없음**, 모든 모드 전환이 TCL 등록/제거로 통합. TEMS-내재화 일관성 ↑. 단점: LLM 컴플라이언스 의존 (강제력은 hook이 아니라 텍스트 지침).

(b) **별도 config 파일** — `memory/sdc_config.json`에 `mode: "rule-based" | "rule+auto"` 저장. `python memory/sdc_commit.py --set-mode auto` 같은 CLI로 전환. preflight가 모드값을 같이 주입. 강제력 ↑, 별도 파일 1개 추가.

(c) **하이브리드** — 기본은 (a)지만, `tool_gate_hook`의 SDC git-gate (현재 항상 켜져 있는 hook-level 강제)는 별도 토글 유지. 즉 "LLM 자동탐색"과 "hook git 강제"를 분리 관리.

내 추천: **(a)** — 새 config 파일/CLI 추가 안 하고 TEMS의 "규칙=행동" 일관성 그대로 살림. tool_gate_hook의 sdc-gate-alert는 그대로 두면 됨 (이건 hook 레벨이라 SDC §0와 독립적으로 동작). 어떻게 갈까?

## Q3

a

## A5

좋아. (a)로 가는 1차 설계 정리해볼게.

## 1차 설계: SDC 트리거 모드 시스템

### 메커니즘
모든 모드 전환을 **TCL 등록/제거 1액션**으로 통합. 별도 config 파일/CLI 신설 안 함.

### 두 모드

| 모드 | 발동 조건 | 등록 방식 |
|------|----------|----------|
| **규칙기반 (기본)** | preflight가 `tags: sdc_trigger` 보유 TCL을 task에 매칭해 주입했을 때만 SDC 3-question gate 수행 | `tems_commit --tags "sdc_trigger"` 로 trigger TCL을 등록 |
| **규칙기반 + 자동트리거** | 위 + SDC.md §0 키워드 자동탐색 | 약속된 메타 TCL 1건 추가 등록 (`tags: sdc_auto_trigger_enabled`) |

### LLM 인지 메커니즘
preflight_hook.py에 한 줄 추가: 매 prompt마다 active TCL 중 `sdc_auto_trigger_enabled` 태그 보유 규칙 있는지 검사 → 출력에 `<sdc-mode>rule-based</sdc-mode>` 또는 `<sdc-mode>rule+auto</sdc-mode>` 1줄 주입. LLM은 이 태그를 보고 §0의 자동탐색 수행 여부 결정.

### SDC.md §0 재작성 골자
- 첫머리에 모드 분기 명시
- 기본 모드: "키워드 자동탐색 생략. preflight 주입 규칙에 `sdc_trigger` 태그 있는 것 발견 시에만 3-question gate"
- 확장 모드: "위 + 기존 키워드 자동탐색 §0 그대로 수행"

### 사용 예시 (사용자 워크플로우)
```bash
# 기본 trigger TCL 등록 (선별적 SDC 활성화)
python memory/tems_commit.py --type TCL \
  --rule "앞으로 git commit/push/merge 등 배포 명령은 SDC 3-question gate 활용" \
  --triggers "git, commit, push, merge, deploy, 배포" \
  --tags "sdc_trigger"

python memory/tems_commit.py --type TCL \
  --rule "앞으로 코드 구현/리팩터링 작업은 SDC 활용" \
  --triggers "구현, refactor, 리팩터" \
  --tags "sdc_trigger"

# 확장 모드 토글 ON (선택)
python memory/tems_commit.py --type TCL \
  --rule "SDC 자동트리거 모드 활성. §0 키워드 자동탐색 수행" \
  --triggers "sdc, mode" \
  --tags "sdc_auto_trigger_enabled"

# 확장 모드 OFF: 위 TCL을 archive 처리
```

### 수정 파일
- [.claude/skills/SDC.md](.claude/skills/SDC.md) — §0 재작성
- [memory/preflight_hook.py](memory/preflight_hook.py) — `<sdc-mode>` 출력 + sdc_trigger 태그 강조 표시 추가

### tool_gate_hook과의 관계
[memory/tool_gate_hook.py:226-265](memory/tool_gate_hook.py#L226-L265)의 hook-level git sdc-gate-alert는 **이번 범위 밖** — 그대로 유지. 모드와 독립적으로 작동(hook은 git 쓰기 명령에 항상 강제). 만약 이것도 모드 따라 토글하고 싶으면 별도 작업.

---

이 큰 그림 OK? 특히 **"메타 TCL 1건 등록으로 자동트리거 모드 토글"** 방식이 마음에 들어? 아니면 더 단순한 거 (예: 자동트리거 부분 자체를 그냥 빼버리고 규칙기반 only로 가기) 원해?

## Q4

응 좋어ㅏ.

## A6

설계 OK. TodoWrite로 단계 추적하고 바로 구현 시작할게.

## A7

Auto mode 진입. preflight_hook.py 구조 먼저 확인하고 병렬로 구현 진행.

## A8

구조 파악 완료. 바로 patch 작성.

## A9

이제 main()에 `<sdc-mode>` 출력 추가.

## A10

이제 SDC.md §0 재작성.

## A11

기본값 섹션도 rule-based 기본 맥락에 맞게 조정.

## A12

이제 smoke test. preflight_hook을 직접 실행해 mode 출력 확인.

## A13

Smoke test 통과. 규칙기반(기본) 모드 — `<sdc-mode>` 무출력, 규칙만 정상 주입, `[SDC]` 마커 없음(기존 TCL에 `sdc_trigger` 태그 없음). 의도대로 작동.

기존 DB에 `sdc_trigger` 태그 TCL이 있는지도 확인.

## A14

DB에 기존 규칙 없음 — 사용자가 필요 시 등록하면 됨. 이제 SDC.md §0이 깨끗하게 재구성됐는지 상단 확인.

## A15

코드 + 문서 변경 완료. 최종 정상 동작 확인을 위해 한 번 더 smoke test.

## A16

모든 hook 정상. TodoWrite 정리하고 사용자에게 결과 보고.

## A17

## 구현 완료

**변경 파일 (2개):**

1. [.claude/skills/SDC.md](.claude/skills/SDC.md#L15-L75) — §0 전면 재작성. 매 prompt 키워드 자의 탐색 deprecated, 발동 조건을 TCL 등록으로 제어. 모드 구조 표 + Step 1/2 판정 로직 + 사용자 등록 예시 + Hook-level 강제 관계 명시.

2. [memory/preflight_hook.py](memory/preflight_hook.py) — 3가지 추가:
   - `_has_sdc_trigger_tag()` — context_tags에 `sdc_trigger` 포함 여부 검사
   - `detect_sdc_mode()` — DB에서 `sdc_auto_trigger_enabled` 태그 활성 TCL 유무 → `rule-based` or `rule+auto`
   - TCL hit이 `sdc_trigger` 태그 보유 시 `[SDC]` 마커 prefix, 확장 모드일 때만 `<sdc-mode>rule+auto</sdc-mode>` 출력 (기본 모드는 침묵)

**Smoke test 결과:**
- 기본 모드: `<sdc-mode>` 미출력, 규칙만 정상 주입 ✓
- `detect_sdc_mode()` → `rule-based` (DB에 toggle TCL 없음) ✓
- `_has_sdc_trigger_tag` 마커 탐지 정상 ✓
- `tool_gate_hook` 회귀 없음 ✓

**사용 방법:**
```bash
# 예: git 배포는 SDC 활용 — 등록하면 git/commit/push 매칭 task에 [SDC] 마커 자동 부착
python memory/tems_commit.py --type TCL \
  --rule "앞으로 git commit/push/merge 등 배포 명령은 SDC 3-question gate 활용" \
  --triggers "git, commit, push, merge, deploy, 배포, 푸시" \
  --tags "sdc_trigger"
```

**미실행 (사용자 결정 대기):**
- TCL 등록 — 어떤 triggers를 쓸지는 사용자 의도 반영 필요
- 커밋 — 변경 2개 + CURRENT_STATE 갱신 묶어서 커밋할지, 세션 종료 핸드오버 시 통합할지

커밋 지금 할까, 아니면 사용자가 trigger TCL 먼저 등록해보고 실제 작동 확인 후 묶을까?

## Q5

그럼 컷밋 배포해줘.

## A18

SDC 선택적 발동 기본 모드에서 현재 preflight에 `[SDC]` 마커 없음 → §0 생략, 본체 직접 커밋 진행. 사용자 명시 승인 있음.

git 상태 확인 후 2개 파일만 스테이징.

## A19

SDC 파일 2개만 스테이징, 나머지 unrelated 변경(.obsidian, Claude-Sessions 등)은 건드리지 않음.

## A20

커밋 성공. 이제 push.

## A21

## 커밋/푸시 완료

- **커밋**: `4d31cf5` — `feat(tems): S38 SDC 트리거 선택화 — 규칙기반(기본) / 자동트리거(확장) 모드 분리`
- **푸시**: `c5edb14..4d31cf5  master -> master` (origin 동기화)
- **범위**: SDC 관련 2개 파일만 (`.claude/skills/SDC.md`, `memory/preflight_hook.py`). 무관한 .obsidian/Claude-Sessions/session_archive 변경은 손대지 않음.

**현재 상태: 규칙기반 모드 (기본) 활성.** SDC §0은 `[SDC]` 마커 TCL이 매칭되기 전까지 침묵. 필요하면 다음 단계로:

```bash
# 예: git 배포 명령에만 SDC 활성화
python memory/tems_commit.py --type TCL \
  --rule "앞으로 git commit/push/merge 등 배포 명령은 SDC 3-question gate 활용" \
  --triggers "git, commit, push, merge, deploy, 배포, 푸시" \
  --tags "sdc_trigger"
```

이 TCL을 등록할까, 아니면 당분간 SDC 없이 운영하면서 어떤 task에 SDC가 실제로 필요한지 관찰해볼까?

## Q6

등록해줘.

## A22

TCL 등록. `tems_commit.py` 시그니처 먼저 확인.

## A23

TCL #122 등록 완료. A2 키워드 다양성 경고는 slash 구분자 파싱 문제로 인한 false warning — triggers는 실제로 다 포함됨. 등록 자체는 성공.

실전 매칭 검증.

## A24

`[SDC]` 마커 정상 부착. 관련 없는 prompt에는 매칭 안 되는지도 확인.

## A25

실전 검증 통과.

## 등록 결과 요약

**TCL #122 등록 완료** — git 배포 명령 SDC 선택 활성화

| 검증 케이스 | 결과 |
|-----------|------|
| `"git push origin master 해줘"` | `#122 [SDC]` 마커 주입 ✓ |
| `"오늘 날씨 어때"` | preflight 침묵 (매칭 없음) ✓ |
| `"이 파일 내용 설명해줘"` | 다른 TCL 매칭, #122 미주입 ✓ |

**현재 상태:**
- 모드: **rule-based (기본)** — `<sdc-mode>` 무출력
- 활성 trigger TCL: #122 (git 배포 전용)
- 다음 git commit/push 시 preflight가 #122를 `[SDC]` 마커와 함께 주입 → 본체가 3-Question Gate 수행

**추가 고려:**
- "앞으로 코드 구현 작업도 SDC" — 원래 예시로 든 거. 하지만 triggers 범위가 너무 넓으면(구현/refactor 등) 거의 모든 task에 매칭돼 rule-based의 selective 장점이 희석됨. 일단 git 배포 1건으로 출발해서 세션 경과 관찰 후 필요 시 추가 등록 권장.
- **확장 모드 토글** (`sdc_auto_trigger_enabled` TCL)은 지금 미등록 — `<sdc-mode>` 출력 없음. 나중에 "자동 키워드 탐색까지 켜겠다" 결정하면 추가.

S38 SDC 트리거 선택화 본 기능 완전 가동 상태.

## Q7

그럼 글로벌 CLAUDE.md와 글로벌.claude를 좀  최적화해줘. 혹시 애매한건 나한테물어보고, 줄일 수 있는 것들은 줄여줘.

## A26

글로벌 ~/.claude 구조부터 파악. 변경 전에 전체 그림이 필요하니 먼저 탐색.

## A27

구조 파악 완료. 최적화 대상과 에매한 항목 정리했음.

## 현재 구조 요약

**CLAUDE.md (52줄, 매 세션 컨텍스트 주입)**
- QMD 메모리 시스템 안내 (6줄) — `/recall` 용법 예시는 recall skill에 이미 있음
- Opus Advisor 사용법 (15줄) — advisor skill + agent에 중복
- Advisor Tool API SDK 참조 (27줄) — Anthropic SDK 앱 빌드용. `/advisor` 슬래시 명령과 다른 용도

**settings.json** — DnT_Fermion 프로젝트 전용 find 명령 + WSL `//mnt/e/...` 경로 등 stale 권한 섞여있음

**scripts/** — artkoon_bootstrap.py + artkoon_session_end_sync.py 등 아트군 전용 스크립트 (설치 시기 Mar-Apr)

**skills/** — TWK/qmd-embed/recall/sync-claude-sessions/tems 각 스킬 + advisor.md + tems-project.md. 기능적으로 다 현역으로 보임.

---

## 명확한 감축 (저위험, 바로 적용 가능)

1. **CLAUDE.md "QMD 메모리 시스템" 섹션** → "설치 완료" 상태 표시 제거, `/recall` 용법 예시 제거 (skill에 있음). 6줄 → 2줄.
2. **CLAUDE.md "Opus Advisor" 섹션 (9~23줄)** → 호출 방법 1줄만 남기고 나머지 `~/.claude/skills/advisor.md` + `~/.claude/agents/advisor.md`에 위임. 15줄 → 2줄.

## 애매한 항목 (확인 필요)

**Q1. Advisor Tool API 참조 섹션 (CLAUDE.md 25~52줄, 27줄)**
이건 Anthropic SDK 앱을 빌드할 때 쓰는 코드 레퍼런스야 (beta tool 시그니처). `/advisor` 슬래시 명령과는 다른 용도. 매 세션에 주입될 필요 거의 없음.
- (a) `~/.claude/references/advisor-sdk.md`로 이전 + CLAUDE.md에 "SDK에서 advisor tool 쓸 때는 references/advisor-sdk.md 참조" 1줄만 남김
- (b) CLAUDE.md에서 완전 제거 (필요 시 `anthropic` SDK 문서 직접 참조)
- (c) 그대로 유지 (매 세션 27줄 소비)

**Q2. CLAUDE.md.bak (Mar 26, 79줄)** — 전체 설치 절차 백업. CLAUDE.md 현재 2줄(#6)에서 참조 중. 이 포인터 삭제해도 돼? (.bak 파일 자체는 유지)

**Q3. settings.json의 stale permissions**
- `Bash(find e:\\\\...\\DnT_Fermion -type d ...)` — DnT_Fermion 전용 find, 한 번 승인받은 특정 패턴
- `Read(//mnt/e/QuantProject/**)` — WSL 경로. Windows 네이티브에선 미사용

둘 다 제거해도 될까? 나중에 DnT_Fermion 재작업 시 다시 prompt 뜨는 정도의 영향.

**Q4. `scripts/artkoon_bootstrap.py` + `artkoon_session_end_sync.py`**
아트군 전용 부트스트랩/세션엔드싱크. 현재 아트군은 E:/ART_Project에 자체 .claude 갖고 있나? (team-delegation.md에 `E:\ART_Project` 표시돼 있음.) 글로벌 ~/.claude/scripts/에 두 파일이 지금도 호출되는지, 아니면 아트군 로컬로 이전됐는지?

---

1~4 답 주면 명확한 감축(1,2) + 승인된 항목 일괄 적용할게.

## Q8

모두 삭제해도돼. 아트군은 지금 로컬에 있음

## A28

승인 확인. 삭제 전 artkoon 스크립트가 다른 곳에서 호출되는지만 빠르게 확인하고 진행.

## A29

artkoon 스크립트는 self-reference 외 참조 없음. 안전하게 삭제 가능. 이제 일괄 적용.

## A30

settings.json 편집은 self-modification protection으로 블록됨 (글로벌 permissions 파일 자기수정은 harness 레벨 강제). CLAUDE.md 감축 + artkoon 삭제는 성공. 나머지는 사용자 결정 필요.

## A31

## 최적화 적용 결과

### ✓ 완료

**1. `~/.claude/CLAUDE.md` — 52줄 → 7줄 (86% 감축)**

```markdown
# Global Claude Code Instructions

## 슬래시 명령 quick reference
- `/recall` — 세션 히스토리/토픽 검색 (QMD + JSONL timeline)
- `/qmd-embed` — QMD Dense vector 운용 (CUDA 백엔드, 트러블슈팅)
- `/advisor [문제]` — Opus 4.6 전략적 자문. **루틴 작업 사용 금지** — 아키텍처/복잡 디버깅/설계 리뷰 전용

상세 사용법은 각 스킬 정의 참조.
```

제거된 항목:
- QMD 설치 상태 정보 (4줄)
- Opus Advisor 사용법 세부 (15줄, skill/agent에 중복)
- Advisor Tool API SDK 참조 블록 (27줄) — SDK 앱 빌드 시에만 필요, 매 세션 주입 불필요
- CLAUDE.md.bak 포인터 (1줄)

**2. `~/.claude/scripts/` 정리**
- `artkoon_bootstrap.py` 삭제 ✓
- `artkoon_session_end_sync.py` 삭제 ✓
- 잔존: `session_end_sync.py`, `qmd_bootstrap.py` (현역)

### ⚠️ 블록됨 (사용자 수동 적용 필요)

**3. `~/.claude/settings.json` stale permissions 제거**

Harness가 글로벌 settings.json self-modification을 자동 차단함 (permissions 파일은 에이전트 자체 권한 수정이라 안전 게이트). 수동 적용용 diff:

```json
// BEFORE (lines 3-8):
    "allow": [
      "Bash(python3 -c ' *)",
      "Bash(find e:\\\\\\\\QuantProject\\\\\\\\DnT_Fermion -type d \\\\\\( -name \"results\" -o -name \"logs\" -o -name \"reports\" -o -name \"tests\" -o -name \"docs\" \\\\\\))",
      "Bash(find e:\\\\\\\\QuantProject\\\\\\\\DnT_Fermion -type f \\\\\\( -name \"*.csv\" -o -name \"*.json\" -o -name \"*.md\" \\\\\\))",
      "Read(//mnt/e/QuantProject/**)"
    ],

// AFTER:
    "allow": [
      "Bash(python3 -c ' *)"
    ],
```

제거 대상 3줄:
- `Bash(find ... DnT_Fermion -type d ...)` — 특정 세션에서 받은 find 명령
- `Bash(find ... DnT_Fermion -type f ...)` — 동일
- `Read(//mnt/e/QuantProject/**)` — WSL 경로, Windows 네이티브 미사용

직접 편집하거나, `settings.json` self-edit 허용 Bash 권한을 추가해주면 내가 적용 가능. 어떻게 할까?

---

### 순효과
- 매 세션 주입 텍스트 46줄 감소 (~500 토큰/세션 절약)
- 글로벌 scripts 디렉토리 legacy 2개 정리
- CLAUDE.md 초점을 "Claude가 알아야 하는 것"에만 맞춤

## Q9

그래 고마워. 그럼 세션종료!

## A32

세션종료 프로토콜 실행. handover 문서 + CURRENT_STATE 업데이트 + L2 raw 추출 + L3 wiki curation (SDC 선택화는 L3 거리) + 최종 커밋/푸시 순.

## A33

CURRENT_STATE.md 갱신.

## A34

이제 L2 session raw 추출 + L3 wiki page + 커밋.
