# Session 2 — 2026-04-20

> Source: `3b0bd757-3cb0-49e4-b5d3-35134d9ed4cc.jsonl`
> Generated: 2026-04-20 22:15:36

## Q1

위상군 이전세션에서 만든 서브에이전트스킬이름을 뭐라고지을까?

## A1

현재 `subagent-brief`로 되어있는데, 몇 가지 대안입니다:

- **`subagent-brief`** (현재) — 가장 명확. "브리핑 템플릿"이라는 정체성이 이름에 드러남
- **`delegate-sonnet`** — Opus→Sonnet 위임이라는 행위가 강조됨. 단, 나중에 다른 모델로 확장 시 이름 제약
- **`exec-brief`** — "실행 브리핑"으로 짧고 도메인 중립적. 하지만 추상적이어서 역할 즉시 파악은 어려움

**추천: `subagent-brief` 유지**. 스킬 설명에 "Opus 본체가 Sonnet 서브에이전트에게 실행 작업을 위임할 때의 5항목 브리핑 템플릿"이 정확히 녹아있고, 타 에이전트(리얼군)에도 이미 배포돼 rename 시 CLAUDE.md·TCL #113·핸드오버 문서 수정 비용이 발생합니다. 바꿀만한 결정적 이유가 있나요?

## Q2

그럼 subagent-brief의 경우 나중에 모델업데이트에 따라 동일이름의 스킬이 나올수도 있을거 같다. 그리고 subagent-brief는 줄여서 부르기가 힘들다. TEMS나 TCL, TGL, DVC같이 줄임말로 네이밍을 바꿀 수 있겠는가?

## A2

TCL #80 맥락(수학적 동형) 감안하면 이 스킬의 본질은 **두 에이전트 경계에서 교환되는 계약(contract) / 프로토콜**입니다 — 사전조건(brief 5항목)·사후조건(verification)·invariant(분업 매트릭스). Design by Contract 구조 그대로.

**후보 (TEMS/DVC 3-letter 리듬 유지):**

| 이름 | 의미 | 강점 | 약점 |
|------|------|------|------|
| **SDC** | Subagent Delegation Contract | "Subagent"가 Opus→Sonnet 경계를 정확히 고정. Contract = 수학적 근거 (Hoare logic) | — |
| **ADC** | Agent Delegation Contract | 서브에이전트 외 팀 델리게이션(디니군 등)도 포함 가능 | 경계가 느슨해 TCL #80 위배 소지 |
| **SDP** | Subagent Delegation Protocol | 프로토콜이라 쌍방 확장 함축 | 현 스킬은 단방향 브리핑이라 덜 맞음 |

**추천: `SDC`** — subagent-brief가 실제로 하는 일(Opus가 Sonnet에 위임할 때 보내는 5항목 계약 + verification)과 구조적으로 정확히 일치하고, Anthropic이 3-letter 약어 스킬을 낼 가능성도 낮습니다. 리얼군 배포판까지 같이 rename해야 하는데 진행할까요?

## Q3

그럼 해당 스킬이름을 SDC로 다시 규정하고 위상군과 리얼군에게 적용된 스킬이름을 변경 후 SDC도 wiki에 등록하라.

## A3

작업 범위 확인 후 진행하겠습니다. 병렬 탐색부터.

## A4

리얼군 스킬 경로 재확인 필요합니다.

## A5

위상군 CLAUDE.md 참조만 확인하고 리얼군 CLAUDE.md + QMD 규칙 파일도 병렬 확인.

## A6

리얼군 스킬 본문도 확인 후 진행.

## A7

병렬 실행 시작. 위상군 스킬 파일 rename + header 업데이트부터.

## A8

이제 리얼군 스킬 헤더도 수정하고, 두 파일 rename + CLAUDE.md들 + CURRENT_STATE + 규칙 파일들 병렬 처리.

## A9

위상군 CLAUDE.md Read 필요. 재시도 + 나머지 파일 업데이트 병렬.

## A10

reclassify 파일 Read + DB 경로 확인 + wiki 페이지 생성 + index/log 업데이트.

## A11

DB 스키마 확인 후 재시도.

## A12

TEMS DB 본문(#113, #115) SQL UPDATE 실행 + FTS5 재인덱싱.

## A13

FTS 테이블 이름 정정하여 재인덱스 + 최종 검증.

## A14

잔존 `subagent-brief` 참조는 모두 의도된 것(rename 이력 기록 / 세션 로그 / BM25 backwards compat). 최종 검증.

## A15

모든 작업 완료. 최종 상태 요약:

**rename 완료 (subagent-brief → SDC):**
- `e:/DnT/DnT_WesangGoon/.claude/skills/SDC.md` (위상군 스킬, name 필드 추가)
- `E:/00_unrealAgent/.claude/skills/SDC.md` (리얼군 스킬)

**참조 갱신:**
- 위상군 [CLAUDE.md](CLAUDE.md) — 4개 참조
- 리얼군 [CLAUDE.md](E:/00_unrealAgent/CLAUDE.md) — 3개 참조
- [CURRENT_STATE.md](handover_doc/CURRENT_STATE.md) — 팀표·마일스톤·결정 테이블 전부 SDC로
- `memory/qmd_rules/rule_0113.md`, `rule_0115.md` — 트리거 키워드 + 태그
- TEMS DB `memory_logs` #113 본문/키워드/태그, #115 태그 (SQL UPDATE + FTS5 rebuild 완료)
- 리얼군 `tems/reclassify_20260420.py` 주석

**wiki 등록:**
- 신규: [docs/wiki/concepts/SDC.md](docs/wiki/concepts/SDC.md) — 정의(Design by Contract 구조적 동형), 5항목 슬롯 표, 분업 매트릭스, 실패 모드 3종
- [index.md](docs/wiki/index.md) Concepts 섹션 추가
- [log.md](docs/wiki/log.md) Ingest 엔트리 append (rename 근거 3점 명시)

**FTS 검증:** `SDC` 쿼리 → 규칙 #113 상위 히트 확인됨. preflight_hook에서 정상 주입 예상.

잔존하는 `subagent-brief` 문자열은 (1) rename 이력 기록 (2) 세션 로그/핸드오버 (append-only) (3) BM25 backwards-compat 키워드 — 모두 의도된 보존입니다.

## Q4

그리고 현재 위상군의 qmd 데이터는 어느경로에 저장되는가?

## A16

QMD 저장 경로 조사.

## A17

위상군 QMD 데이터는 **4개 레이어**로 분산 저장됩니다.

## 1. QMD 전역 인덱스 (BM25 FTS + Dense vectors)
- **`C:/Users/bluei/.cache/qmd/index.sqlite`** (53.3MB, 1500 files / 5004 vectors)
- 모든 collection이 이 단일 SQLite에 인덱싱됨 — 위상군 전용 아님

## 2. TEMS 규칙 embedding 소스 (`tems-wesanggoon` collection)
- **`E:\DnT\DnT_WesangGoon\memory\qmd_rules\`** (90 파일, `rule_NNNN.md`)
- preflight dense fallback이 여기서 조회: [memory/tems_engine.py:103](memory/tems_engine.py#L103) → `qmd vsearch -c tems-wesanggoon`
- 각 rule.md ↔ `memory/error_logs.db` memory_logs 테이블 1:1 대응 (rule #113 = rule_0113.md)

## 3. 세션 기록 (원본 소스 — QMD 미인덱싱 상태)
- **`~/.claude/projects/e--DnT-DnT-WesangGoon/*.jsonl`** — Claude Code native raw (wiki.config.json `sessions_jsonl` 참조)
- **`E:/DnT/DnT_WesangGoon/QMD_drive/sessions/`** — 과거 로컬 저장소 (collection 미등록, orphan)
- **`E:/DnT/DnT_WesangGoon/qmd_sessions/`** — session-lifecycle Step 3 저장 경로

## 4. ⚠️ Stale collection 발견
`qmd collection list` 결과 **`wesanggoon-sessions`** 이 `E:/AgentInterface/wesanggoon-sessions/` 를 가리키는데 **해당 경로 미존재** (0 files, updated never). `jaemi-sessions`도 동일 상태.

**S35 추가 task 후보:**
- `qmd collection remove wesanggoon-sessions` 후 실제 세션 경로(`QMD_drive/sessions/` 또는 `qmd_sessions/`)로 재등록
- 혹은 collection 정책 재정립 (raw jsonl은 `/recall`이 native JSONL로 처리하므로 중복 불필요할 수도)

정정·추가 설정 진행할까요?

## Q5

이제 모든 에이전트는 각자의 프로젝트 로컬폴더에 qmd 데이터를 관리하는 것으로 규칙을 정하고 위상군부터 기존 데이터를 현재 위상군의 로컬 폴더에 폴더를 만들고 데이터 이관. 이는 모든 에이전트에게 동일하게 적용될것. 일단은 위상군만 시작.

## A18

현재 세션 데이터 산개 상태 파악 후 통합 설계 시작.

## A19

산개 상태 확인 완료. 하드코딩된 참조 확인 후 이관 계획 실행.

## A20

이관 실행. 파일 이동 → QMD collection 재등록 → embed → 문서/규칙 업데이트 순.

## A21

대소문자 정규화 + QMD collection 재등록 + embed.

## A22

collection 파일 개수 불일치 확인.

## A23

데이터 이관 + QMD collection 정상 등록 완료 (91 files / 48 embedded). 이제 규칙/문서/wiki 업데이트.

## A24

session-lifecycle Read + 키워드 보강 + CLAUDE.md + CURRENT_STATE 업데이트.

## A25

최종 검증 + 정리.

## A26

이관 완료. 위상군 QMD 로컬 구조 확립.

## 실행 결과

**파일 이관 (91 files → 92 with README):**
| 이관 전 (산개) | → | 이관 후 |
|---|---|---|
| `QMD_drive/sessions/` (43) | → | `qmd_drive/sessions/` (45) |
| `Claude-Sessions/` (2) | → | `qmd_drive/sessions/` (merge) |
| `qmd_sessions/` (46) | → | `qmd_drive/recaps/` (46) |
| — | | `qmd_drive/README.md` (new, 정책 문서) |

**QMD Collection 재정리:**
- ❌ 제거: `wesanggoon-sessions` (broken, `E:/AgentInterface/wesanggoon-sessions/` 미존재)
- ✅ 신규: `wesanggoon-qmd-drive` → `E:\DnT\DnT_WesangGoon\qmd_drive` (92 files / 48 embedded / 63 chunks)
- ✅ 유지: `tems-wesanggoon` → `memory/qmd_rules` (91 files, rule_0116 포함)

**정책 등록:**
- **TCL #116** — "모든 에이전트는 QMD 데이터를 프로젝트 로컬 `qmd_drive/` 에서 관리. 외부 경로 collection 금지."
- [.claude/rules/session-lifecycle.md:20](.claude/rules/session-lifecycle.md#L20) Step 3 경로 수정
- [CLAUDE.md](CLAUDE.md) 조건부 규칙 테이블에 `qmd_drive/README.md` 행 추가
- [docs/wiki/principles/Per_Agent_Local_QMD.md](docs/wiki/principles/Per_Agent_Local_QMD.md) 신규 (모든 에이전트 공통 원리)
- [docs/wiki/index.md](docs/wiki/index.md) + [log.md](docs/wiki/log.md) 갱신
- [CURRENT_STATE.md](handover_doc/CURRENT_STATE.md) S35 성과 + S35 task 추가 (QMD-Local-Rollout / sync-claude-sessions-config)

**S35 남은 task:**
- 타 에이전트 6개 동일 이관 (리얼군/코드군/디니군/어플군/기록군/빌드군/위상군독립)
- `sync-claude-sessions` 글로벌 스킬이 `Claude-Sessions/` 로 쓰는 기본 동작 → `qmd_drive/sessions/` 리다이렉트 방안 검토 (P2)

## Q6

현재 TEMS는 스킬인가 시스템인가?

## A27

**TEMS는 시스템입니다.** (스킬이 아님)

## 근거

| 축 | TEMS | DVC | SDC |
|----|------|-----|-----|
| Skill 파일 존재? | ❌ `.claude/skills/TEMS.md` 없음 | ✅ 글로벌 `~/.claude/skills/dvc/` | ✅ `.claude/skills/SDC.md` |
| LLM이 `Skill` 도구로 호출? | ❌ 호출 안 함 | ✅ 수동 호출 | ✅ 수동 참조 |
| 런타임 발동 방식 | hook 자동 (SessionStart / UserPromptSubmit / Pre·PostToolUse / Stop) | 수동(`python -m checklist.runner`) | LLM 판단 시점 |
| 구성 요소 | `memory/tems_engine.py` + SQLite + FTS5 + QMD dense + hook 배선 | `src/checklist/cases.json` + `chk_*.py` | 5항목 템플릿(md) |

## 구분 기준 일반화

- **시스템** = hook/서비스로 *자동* 실행되는 인프라. LLM 판단 없이 런타임에 작동.
- **스킬** = LLM이 *의식적으로 호출하는* 프로시저/가이드. 호출 시점이 LLM 판단에 의존.

TEMS는 매 prompt의 preflight_hook이 무조건 돌면서 규칙을 주입·수집·검증 → **시스템**.
단, 그 사용 *프로토콜*(`.claude/rules/tems-protocol.md`)은 조건부 규칙으로 LLM이 읽는 문서 — 이건 "스킬스러운 레이어"지만 Skill 도구 호출 대상은 아닙니다.

## 애매한 경계

- **DVC**: `runner.py`는 시스템(자동화 가능), `dvc` 스킬은 사용법 가이드 — 하이브리드.
- **TEMS의 규칙 *등록* 동작**: 현재 `python memory/tems_commit.py` CLI 직접 호출 + `tems-protocol.md` 문서. 이걸 Skill로 승격하면 호출 일관성이 올라갈 수 있으나, 종일군이 지시할 때 자동 registration 자체는 본체가 판단해야 하는 분류 작업이라 스킬화 실익이 제한적.

위키에 TEMS vs DVC vs SDC 분류 대조표를 추가할까요? (시스템/스킬/하이브리드 경계를 문서화)

## Q7

그것도 좋은 방법이니 실행하고, 이런 분류작업은 sonnet이 가능하다면 앞으로도 SDC를 사용하라. 그리고 llm wiki는 스킬인가 시스템인가? 그리고 llm wiki도 fork 브랜치화 되었으니 TWK(TriadWiKi)로 명칭한다.

## A28

4개 액션: 분류표 wiki 추가 + TCL 등록 + llm-wiki 분류 판정 + TWK rename(SDC 위임). 먼저 llm-wiki 구조 + 참조 탐색.

## A29

Phase 1: 분류표 wiki + TCL 2개 등록 병렬. Phase 2: 분류 TCL 발동의 첫 케이스로 rename을 Sonnet에 SDC 위임.

## A30

Phase 2: Sonnet 서브에이전트에 SDC 계약으로 rename 위임.

## A31

Trust-but-verify (TCL #115): Sonnet 보고 실증.

## A32

모든 Sonnet 위임 주장 실증 완료. 최종 상태:

**Phase 1 (Opus 본체):**
- Wiki 신규 페이지: [concepts/System_vs_Skill.md](docs/wiki/concepts/System_vs_Skill.md) — System/Skill/Hybrid 3-way 분류표 (TEMS/DVC/SDC/TWK 각각 매핑)
- TCL #117 — 분류 작업은 Sonnet SDC 위임 (7-카테고리/needs_review/wiki 섹션 분류 등). 본체 전담은 구조적 판단만.
- TCL #118 — llm-wiki → TWK(TriadWiKi) 공식 명명.
- Wiki index/log 갱신.

**Phase 2 (SDC → Sonnet 위임, TCL #117의 첫 시범):**
- ✅ 글로벌 스킬 rename: `~/.claude/skills/llm-wiki/` → `~/.claude/skills/TWK/`
- ✅ SKILL.md `name: TWK`, description 갱신
- ✅ 6개 글로벌 파일 + 위상군 5개 파일 참조 치환
- ✅ TEMS DB #114 본문/키워드/태그 업데이트 + FTS5 rebuild
- ✅ lint.py/init_wiki.py 스크립트 동작 확인
- ✅ **Skill 로더 `TWK` 등록 확인** (상단 skills 리스트에 표시됨)

**질문 답변 — `llm-wiki`는 무엇인가:**
**Hybrid**입니다.
- Skill 레이어: `SKILL.md` + `Skill` 도구로 호출 → 3-Layer/3 Operations 가이드 참조
- System-ish 레이어: session-lifecycle Step 5-7에서 스크립트(`extract_session_raw.py` / `lint.py`) 수동 실행 — 자동 hook 아니지만 lifecycle에 배선
- TEMS와 달리 LLM 의식적 호출이 필요하므로 "스킬 우세 hybrid"

잔존 `llm-wiki` 참조는 모두 의도적 (backwards-compat 라벨 / trigger 키워드 / 역사 기록 / 이관 증거).

## Q8

TEMS와 TWK는 에이전트가 git원격레포에서 바로 설치가 가능한가? 그리고 TWK 명칭변경은 현재 리얼군에게도 적용이 되어야하는가? 또한 TEMS와 TWK는 둘다 QMD를 이용하고 있는데, 만약 각각의 독립된 원격레포에서 TEMS혹은 TWK를 설치할때 QMD에 대한 의존성은 어떻게하는게 좋겠는가? 그리고 마지막으로 TEMS와 TWK는 플러그인개념으로 봐도 되는것인가?

## A33

Q2 정확성 위해 리얼군 llm-wiki 참조 확인 + TEMS 레포 후보 실태 확인.

## A34

4개 질문 답변:

## Q1. TEMS / TWK 원격 레포 직접 설치?

| | 현재 상태 | 설치 가능성 |
|---|---|---|
| **TEMS** | `bobpullie/TEMS` repo 존재 (https://github.com/bobpullie/TEMS.git). `pyproject.toml` 정비 (hatchling, `pip install tems`, CLI `tems scaffold --agent-id X`). `src/tems/scaffold.py` 가 템플릿 배포. | ✅ **바로 가능** — `pip install git+https://github.com/bobpullie/TEMS.git` + `tems scaffold`. 단 현재 위상군 `memory/*.py` 에는 **self-contained Tier1** 사본이 있어 외부 pkg 없이도 돌아감 (TGL #92 근거). |
| **TWK** | `~/.claude/skills/TWK/` — **git 레포 아님** (not a git repository). 원격 오리진 없음. | ⚠️ **현재 불가** — 레포화 필요. 후속 작업: bobpullie/TWK repo 신설 + `install.sh`(또는 scripts/install.py)로 `~/.claude/skills/TWK/` 에 clone/copy. |

**권고:** TWK도 TEMS처럼 독립 GitHub repo 승격. 설치 스크립트는 "clone → `~/.claude/skills/TWK/` 심볼릭 또는 복사" 패턴.

## Q2. 리얼군에 TWK rename 적용?

**적용 필요 없음 (현 시점).** 근거:
- 리얼군은 Wave 1 (TEMS Phase 0-2) + SDC만 설치됨 — **wiki 미구축**. 
- `llm-wiki` / `docs/wiki/` / `wiki.config.json` 참조 전무 (S34 팀 현황표: 리얼군 llm-wiki 컬럼 "—").
- 추가로 `E:/00_unrealAgent/` 디렉토리가 현재 `.zip` 으로 아카이브된 상태 (E:/ 루트에 `00_unrealAgent.zip`만 보임).

**단**, S35 task 중 `TWK-Expand P1`로 리얼군에 TWK 배포 시 → 그때 이미 TWK 이름으로 설치하면 됨 (rename 이슈 없음).

## Q3. TEMS + TWK 공통 QMD 의존성 처리

QMD는 **시스템 CLI (npm 글로벌)** + **사용자 캐시 인덱스 (`~/.cache/qmd/index.sqlite`)** — Python 패키지가 아님.

**권장 전략 (3-layer):**

1. **하드 의존성 (바이너리):** 각 레포 README에 요구사항 명시.
   ```
   Requires:
     - Node.js ≥ 20
     - @tobilu/qmd (global): `npm install -g @tobilu/qmd`
     - (Optional) CUDA 12.8 for dense fallback
   ```

2. **소프트 런타임 폴백:** 설치 후 `import` 시 `shutil.which("qmd")` 체크 → 미설치시 경고 + BM25-only 모드. TEMS `HybridRetriever`는 이미 SEMANTIC_FALLBACK 스위치 있음.

3. **공통 bootstrap (선택):** 별도 `qmd-bootstrap` 패키지를 두지 말고, **TEMS init CLI 가 `qmd collection add tems-<agent>` 를 자동 등록**, TWK init이 `qmd collection add <agent>-qmd-drive` 등록. 각자 **자기 몫의 collection만 register**, QMD 바이너리 자체는 사용자 책임.

**의존 그래프:**
```
QMD binary (user-global, npm) ─── shared (1번 설치)
QMD index (user-cache)        ─── shared (자동)
tems-<agent> collection       ─── TEMS가 등록
<agent>-qmd-drive collection  ─── TWK가 등록
```

**핵심 원칙:** TEMS도 TWK도 QMD를 **번들링하지 않는다** (Python `git`·`curl` 의존과 동일 모델). "검증 후 경고, 없으면 degrade" 가 올바름.

## Q4. TEMS / TWK = 플러그인?

**예, 정확히 Claude Code Agent Plugin입니다** — 두 가지 plugin type:

| | Plugin type | Hosting mechanism | 없으면? |
|---|---|---|---|
| **TEMS** | Hook plugin | `settings.local.json` 의 SessionStart / UserPromptSubmit / Pre·PostToolUse / Stop 바인딩 | Claude Code 정상 작동 (기억만 사라짐) |
| **TWK** | Skill plugin | `~/.claude/skills/TWK/SKILL.md` frontmatter → `Skill` 도구로 호출 | Claude Code 정상 작동 (wiki 운영만 수동) |
| **SDC** | Skill plugin (project-local) | `.claude/skills/SDC.md` | 위임 템플릿이 없을 뿐 |
| **DVC** | Skill plugin + 프로젝트 runner | 글로벌 스킬 + `src/checklist/runner.py` | 빌드 검증 자동화만 없어짐 |

**플러그인으로 본 함의:**
- Plug-and-unplug 가능 — 프로젝트마다 선택 설치
- 버전 관리 가능 — 각 repo가 semver
- 독립 배포 가능 — 에이전트마다 설치 subset 다를 수 있음 (코드군 `fermion-wiki` 자체 운영처럼 TWK 대신 custom 가능)
- **분류**는 글자 그대로: 
  - TEMS = **Hook-based system plugin**
  - TWK/SDC/DVC = **Skill-based (toolcall) plugin**

이 모델을 확립하면 향후 "Triad Agent Plugin Registry" 같은 메타 관리(어느 에이전트에 어느 플러그인 버전이 설치됐나)가 자연스럽게 따라옵니다. 필요하면 wiki concept 페이지로 정식화할까요?

## Q9

https://github.com/bobpullie/TWK <-TWK 원격레포  https://github.com/bobpullie/DVC <-DVC원격레포 https://github.com/bobpullie/SDC <-원격레포 https://github.com/bobpullie/TEMS <-기존TEMS원격레포  각각의 원격레포를 만들었으니 각 플러그인과 스킬을 모두 각각의 레포에 커밋하고 푸시하라.

## A35

인증 + 각 레포 현황 병렬 확인 후 순차 push.

## A36

이해 완료. 실행 계획:
- **TEMS**: 이미 origin 동기화 상태 확인 후 push (in-sync면 no-op)
- **TWK**: `E:/bobpullie/TWK/` 복제 생성 → init/commit/push
- **DVC**: project-local(`E:/DnT/DnT_WesangGoon/.claude/skills/dvc/`) → `E:/bobpullie/DVC/` 복제 → init/commit/push  
- **SDC**: 위상군 canonical `.claude/skills/SDC.md` → `E:/bobpullie/SDC/` 복제 → init/commit/push

Phase A: 작업 디렉토리 생성 + 컨텐츠 복사 + README/LICENSE/.gitignore.

## A37

Phase B: git init + 첫 커밋 + remote add + push (3개 레포 순차 실행).

## A38

계정 불일치 (활성: blueitems-Mystic, 레포 오너: bobpullie). URL에 `bobpullie@` 명시하여 재시도 (TEMS가 이 패턴 사용).

## A39

3개 레포 푸시 성공. TEMS 동기화 확인 + 최종 검증.

## A40

모든 4개 레포 상태 최종 확인:

| 레포 | 상태 | 브랜치 | 커밋 내용 |
|------|------|--------|---------|
| **TEMS** | ✅ 이미 origin/master 동기화 (변경 없음, 2026-04-13 S31-33 commits 그대로) | `master` | 기존 (48586cc, 98a5e01, 8091c4e) |
| **TWK** | ✅ 신규 push 완료 | `main` | feat: initial TWK (TriadWiKi) — 20+ files (SKILL.md + scripts + templates + references + LICENSE + README + .gitignore) |
| **DVC** | ✅ 신규 push 완료 | `main` | feat: initial DVC — SKILL.md + ARCHITECTURE.md + GUIDE.md + init.py + templates + LICENSE + README |
| **SDC** | ✅ 신규 push 완료 | `main` | feat: initial SDC — SKILL.md (위상군 canonical) + README (per-agent 커스터마이제이션 가이드) + LICENSE |

**Auth 처리:** 활성 계정이 `blueitems-Mystic`이었으나 repos 오너는 `bobpullie` → `gh auth switch --user bobpullie` + `gh auth setup-git` 후 푸시 성공.

**노트:**
- LF → CRLF 경고는 Windows git 기본 동작 (기능 영향 없음, 원본 LF 유지됨)
- `main` branch (신규 3개) vs `master` branch (기존 TEMS) — 현재 GitHub 권장 `main` 따름
- TGL #77 준수: `--no-verify` · `amend` · 서명 변경 일체 미사용. 일반 커밋만 생성.

## Q10

그럼 이제 4개의 체계를 앞으로 위상군이 업데이트를 하거나 다른 에이전트가 업데이트하여 해당레포에 커밋푸시하면 서로 다른 에이전트들도 모두 원격레포를 통해 기능 업데이트가 가능한가? 그게 가능하도록 각 스킬과 플러그인데 해당 원격레포 주소를 첨부하라.

## A41

4개 레포 모두에 upstream URL 메타데이터 + 업데이트 instructions 추가 후 push → 설치 버전 동기화. 먼저 레포 측 업데이트.

## A42

커밋 + 푸시 4개 레포 + 설치 버전 동기화 + TCL 등록.

## A43

완료. 4개 플러그인 **remote-sync 체계** 구축.

## 실행 결과

### Repo 측 (push 완료)
| 레포 | frontmatter | README Updating | 커밋 |
|------|------------|----------------|-----|
| `bobpullie/TEMS` | — (Python pkg) | `pip install -U git+...` + `tems scaffold` | 73687f2 |
| `bobpullie/TWK` | `upstream` + `update_cmd` | `git -C .../TWK pull origin main` | 540809b |
| `bobpullie/DVC` | `upstream` + `update_cmd` | Option A(global)/B(project) + `git pull` | 25eb84b |
| `bobpullie/SDC` | `upstream` + `update_cmd` | curl (single file) 또는 clone | 861c73f |

### 설치 측 (메타데이터 sync)
- `~/.claude/skills/TWK/SKILL.md` — `upstream: https://github.com/bobpullie/TWK`
- `.claude/skills/dvc/SKILL.md` — `upstream: https://github.com/bobpullie/DVC`
- `.claude/skills/SDC.md` — `upstream: https://github.com/bobpullie/SDC`

### TCL #119 등록
"4개 원격레포 upstream URL + update_cmd frontmatter 필수. 위상군/타 에이전트가 push → 전체 에이전트 `git pull`/`pip -U`/`curl` 로 수신."

## 답변: 네, 업데이트 전파 가능

**작동 흐름:**
```
위상군(or any agent)        bobpullie 레포           타 에이전트
──────────────────          ─────────────           ──────────
local edit + commit  ──push──▶  main branch  ──pull──▶  local update
                                                        + 검증(trust-but-verify)
```

## ⚠️ 남은 한계 (차기 작업 추천)

현재 설치 버전은 **git clone이 아니라 파일 복사본** — 그래서 `git pull`이 바로 동작하지 않습니다:
- `~/.claude/skills/TWK/` — not a git repo
- `.claude/skills/dvc/` — not a git repo

**해결 옵션:**
1. **재설치 (권장, 간단):** `rm -rf ~/.claude/skills/TWK && git clone https://github.com/bobpullie/TWK.git ~/.claude/skills/TWK`
2. **기존 dir을 repo로 승격:** `cd <INSTALL>; git init; git remote add origin ...; git fetch; git reset --mixed origin/main`

지금 위상군/글로벌에 대해 clone 방식으로 converting 할까요? (현재 remote와 내용 일치하므로 충돌 없음.)

## Q11

지금 위상군/글로벌에 대해 clone 방식으로 converting 할까요? (현재 remote와 내용 일치하므로 충돌 없음.) < 이게 어떤의미인지 쉽고 자세하게 셜명

## A44

## 지금 설치 구조를 그림으로

```
[bobpullie/TWK 레포 on GitHub]   ←── 원본·최신
        │
        │ (S35 초기 push는 "E:/bobpullie/TWK"라는 별도 dir에서 했음)
        │
[위상군이 쓰는 ~/.claude/skills/TWK/]  ←── 단순 파일 복사본
   내용은 같지만, 이 폴더는 레포를 "모름"
   (.git/ 디렉토리 없음)
```

**비유:** 원본 책(`bobpullie/TWK`)을 **복사기로 한 번 찍어서** `~/.claude/skills/TWK/` 에 둔 상태.
복사본이 원본과 내용이 같지만, 복사본은 원본이 "어디 있는지" 모릅니다.

## 왜 `git pull` 이 지금 안 되나

`git pull`은 "내가 어느 레포에서 왔는지"를 아는 폴더에서만 작동합니다.
그 "어디서 왔는지"는 폴더 안의 숨겨진 `.git/` 디렉토리에 기록됩니다.

지금 `~/.claude/skills/TWK/` 에는 `.git/` 이 없어서 — `cd ~/.claude/skills/TWK && git pull` 하면
`fatal: not a git repository` 에러가 납니다.

## "Clone 방식으로 converting" = 이 폴더를 "살아있는 복사본"으로 바꾸기

살아있는 복사본 = `.git/` 이 들어 있어서 원격 레포와 **연결된** 폴더.
한 번 연결해두면 이후로는 `git pull` 한 줄로 최신 내용을 받아올 수 있습니다.

### 두 가지 변환 방법

**옵션 1: 싹 지우고 clone 새로 받기 (깔끔, 권장)**
```bash
rm -rf ~/.claude/skills/TWK                          # 복사본 제거
git clone https://github.com/bobpullie/TWK.git ~/.claude/skills/TWK   # 레포에서 새로 받아옴
```
결과: 내용은 그대로(원격과 일치). 이제 `.git/` 포함되어 `git pull` 가능.

**옵션 2: 기존 폴더에 `.git/` 만 덧붙이기 (내용 유지)**
```bash
cd ~/.claude/skills/TWK
git init -b main                                     # 빈 .git/ 만들기
git remote add origin https://github.com/bobpullie/TWK.git   # 원격 주소 기록
git fetch origin                                     # 원격 상태 받아오기
git reset --mixed origin/main                        # "나는 main 브랜치의 이 시점과 같음" 선언
```
결과: 파일 1바이트도 안 건드림. 폴더만 "레포 인식" 상태가 됨.

## "충돌 없음" 이 왜 중요한가

만약 **원격 레포와 내 로컬 파일이 다르다면**, 변환 시 문제가 생깁니다:
- 옵션 1로 지우면 → 내 로컬 수정사항이 날아감
- 옵션 2로 연결하면 → 첫 `git pull` 때 머지 충돌 발생

다행히 **지금은 원격과 로컬이 비트 단위로 동일**합니다. 왜냐:
- 원격 레포는 위상군의 `~/.claude/skills/TWK/` 내용을 방금(오늘 S35) 그대로 올린 것
- 그 이후로 아무도 수정 안 했음

그래서 어느 옵션으로 변환해도 **자료 손실 0, 충돌 0**.

## 변환 후 무엇이 달라지나

**변환 전 (지금):**
- TWK 레포에 새 기능 push됨 → 내 로컬은 구버전 유지 (수동 재다운로드 필요)
- `git pull` 한 줄로 업데이트 불가

**변환 후:**
- TWK 레포에 새 기능 push됨 → `git -C ~/.claude/skills/TWK pull` 한 줄로 최신 수신
- 다른 에이전트(리얼군·코드군 등)도 각자 한 번만 변환해두면 동일하게 업데이트 받음
- `SKILL.md` frontmatter의 `update_cmd:` 필드가 그대로 작동

## 한 줄 요약

> **"지금은 정지된 복사본 / 변환 후는 원격과 연동된 복사본. 내용은 그대로, 업데이트 받는 창구만 생기는 것."**

진행해도 되겠습니까? (위상군 TWK·DVC 2개 즉시 converting, SDC는 단일 파일이라 curl 방식 유지)

## Q12

진행하라.

## A45

옵션 2 (git init + attach) 실행. 내용 보존하면서 원격 연결. DVC는 프로젝트 로컬이라 같이 처리.

## A46

변환 성공. 위상군 프로젝트 nested repo 처리 + 업데이트 파이프라인 smoke test.

## A47

위상군 root가 아직 dvc 파일을 추적 중 (nested repo 경계 미인식). untrack + gitignore.

## A48

변환 완료. 파이프라인 smoke test 성공. CURRENT_STATE 갱신.

## A49

변환 완료.

## 최종 상태

| 플러그인 | 설치 위치 | .git 부착 | remote origin | 상태 |
|---------|----------|----------|-------------|------|
| **TWK** (global) | `~/.claude/skills/TWK/` | ✅ | bobpullie/TWK | `main...origin/main` clean |
| **DVC** (위상군 local) | `.claude/skills/dvc/` | ✅ | bobpullie/DVC | `main...origin/main` clean |
| **SDC** (위상군 local) | `.claude/skills/SDC.md` | — (단일 파일) | curl 방식 | upstream frontmatter만 |
| **TEMS** | `E:/bobpullie/TEMS/` (편집용), 각 에이전트 `memory/*.py` (복사본) | ✅ | bobpullie/TEMS | `master...origin/master` clean |

## nested repo 처리

- 위상군 root `.gitignore` 에 `.claude/skills/dvc/` 추가 → DVC 폴더는 위상군이 추적하지 않음 (플러그인은 자기 repo 소속)
- `git rm --cached` 로 기존 추적 파일 43개 staging 해제 (pending deletion in 위상군 next commit)

## 지금부터의 업데이트 플로우

```bash
# 위상군 또는 타 에이전트가 TWK 기능 추가
cd E:/bobpullie/TWK && <edit> && git add . && git commit -m "..." && git push

# 다른 에이전트는
git -C ~/.claude/skills/TWK pull origin main   # 한 줄로 최신 수신
```

같은 패턴이 DVC·TEMS·SDC(curl) 각각에 적용.

## 남은 pending (위상군 root commit 필요 시)

- `.gitignore` 추가 (플러그인 section 신규)
- `.claude/skills/dvc/` 파일들 staging "D" (git rm --cached 결과 — untrack)
- 기타 누적된 S35 변경분

커밋은 종일군 승인 패턴(TGL #77 정신) 따라 지시 대기 중.

## Q13

SDC의 경우 한가지 기능을 추가해서 업그레이드가 필요하다. 지금같이 git에 커밋&푸시&풀과 같이 추론판단이 필요없는 경우 무조건 sonnet 서브에이전트를 사용하면 좋겠다. 이부분은 에이전트가 특정수행명령을 받았을때 "이것이 sonnet이 하면 결과가 달라질 수 있는것인가?"라는 판단을 통해 매번 SDC를 해야하는 규칙을 적용하지 않아도 단순업무는 SDC가 발동될 수 있도록 하고 싶다. 나의 예시가 git에 한정되었고, 판단근거가 애매하기에 이부분을 보다 정밀하게 판단내릴 절차프롬프트를 설계해서 제시해달라.

## A50

## SDC Auto-Dispatch Check — 판단 절차 설계안

### 핵심 원리 (one-liner)

> **"이 작업의 결과물이 Opus↔Sonnet 교체로 의미 있게 달라지는가?"**
> NO → Sonnet 위임이 우월 / YES → Opus 본체 유지

이 질문을 매번 직감으로 묻기보다, **3-step 결정 게이트**로 형식화.

---

### 3-Question Gate

```
Task received
      │
      ▼
┌──────────────────────────────────┐
│ Q1. Invariance Test              │
│ "동일 spec·tools를 받은 5명의     │
│  구현자가 strictly 따른다면,      │
│  결과물이 의미적 동등인가?"       │
└──────────────────────────────────┘
      │
      ├─── NO (결과 편차 생김) ──▶ [KEEP Opus]
      │
      ▼ YES (결정론적)
┌──────────────────────────────────┐
│ Q2. Overhead Test                │
│ "SDC brief 작성이 직접 실행보다   │
│  더 많은 tool call을 요구하나?"   │
└──────────────────────────────────┘
      │
      ├─── YES (trivial, 1~2줄) ──▶ [KEEP direct]
      │
      ▼ NO (multi-step/file)
┌──────────────────────────────────┐
│ Q3. Reversibility Gate           │
│ "출력이 틀렸을 때 blast radius?"  │
└──────────────────────────────────┘
      │
      ├─── Local reversible ──▶ [DELEGATE full]
      ├─── Shared state     ──▶ [DELEGATE + STAGING] ★
      └─── Destructive      ──▶ [KEEP + user confirm]
```

**★ STAGING** = Sonnet 은 `git commit`·파일 준비까지만. `push`/`merge`/외부 POST는 Opus 본체가 검토 후 실행. TGL #77의 일반화.

---

### Signal Heuristics (문장 단서로 빠른 판정)

| Signal | 위치 | 판정 방향 |
|--------|------|---------|
| "이식 / 복사 / rename / migrate" | task 언어 | → DELEGATE |
| "대량 / N개 모두 / 반복" | task 언어 | → DELEGATE |
| "smoke test / 실증 / 확인" | task 언어 | → DELEGATE (readonly) |
| "아키텍처 / 설계 / 판정" | task 언어 | → KEEP |
| "best approach / trade-off / should we" | task 언어 | → KEEP |
| TEMS 7-카테고리 fallback 근거 서술 | task 내용 | → KEEP |
| 명확한 checklist로 변환 가능 | task 구조 | → DELEGATE |
| 동일 파일 2+ 편집 + 테스트 | task 구조 | → DELEGATE |

---

### 자동 트리거 (SDC skill 내부 감지)

아래 키워드·패턴이 task에 포함되면 **자동으로 3-question gate 실행**:

- Git 명령: `commit` · `push` · `pull` · `merge` · `cherry-pick` · `rebase` · `fetch`
- 파일 조작: `mv` · `cp` · `rename` · `refactor` (기계적 변환)
- 배치 동작: 동일 연산 ≥3회 반복 암시
- 분류: `classify` · `sort` · `재분류` · `needs_review`
- 검증: `verify` · `test` · `validate` · `smoke`
- 이식/배포: `Wave` · `이식` · `배포`

---

### 예시 적용

| 작업 | Q1 | Q2 | Q3 | 판정 |
|------|---|---|---|-----|
| "TWK repo에 commit+push" | YES (git 결정론) | NO (여러 step) | Shared | **DELEGATE + STAGING** |
| "CURRENT_STATE에 한 줄 추가" | YES | **YES** | Local | **KEEP direct** |
| "오타 한 글자 수정" | YES | **YES** | Local | **KEEP direct** |
| "4개 레포 README 에 upstream 추가·push" | YES | NO | Shared | **DELEGATE + STAGING** |
| "needs_review 22건 7-카테고리 분류" | 부분 YES (TCL #117 허용) | NO | Local | **DELEGATE + trust-but-verify** |
| "Phase 3 → Wave 2 승격 가부" | **NO** | - | - | **KEEP Opus** |
| "이 버그의 근본 원인 찾아라" | **NO** (탐색 중 가설 수정 발생) | - | - | **KEEP Opus** (단, 순수 Grep/ls는 Explore 위임 가능) |
| "rm -rf logs/checklist/" | YES | YES | **Destructive** | **KEEP + 사용자 확인** |

---

### Default Reversal (기본값 전환)

현재: "실행 작업은 Sonnet 위임 **권장**"
제안: "**Q1 통과 작업은 기본 DELEGATE**, KEEP 은 예외로 근거 명시"

→ 매번 "위임할까?" 묻지 않고, "위임하지 **않을** 근거"가 있을 때만 KEEP.
→ git push·rename·배치 같은 단순업무는 판단 기록 없이 자동 dispatch.

---

### SDC 스킬 통합 위치

`SKILL.md` 에 **새 섹션 #0** 삽입 (필수 5항목 위):

```markdown
## 0. Auto-Dispatch Check (task 수신 즉시 실행)

# 3-Question Gate
Q1 (Invariance): 결정론적? → NO=KEEP
Q2 (Overhead): brief > 실행? → YES=KEEP direct
Q3 (Reversibility): blast radius? 
  Local=DELEGATE / Shared=STAGING / Destructive=KEEP+confirm

# Auto triggers (키워드 감지 시 위 gate 자동 실행)
git{commit,push,pull,merge,rebase,cherry-pick,fetch}
mv · cp · rename · refactor · migrate
배치(N≥3 반복) · classify · sort · verify · test · 이식

# 기본값: Q1 PASS → DELEGATE. KEEP은 근거 명시 필수.
```

및 TCL 1건 신규 등록 (분류 TCL 아닌 *dispatch policy* TCL):

> "모든 실행 task 수신 시 SDC-DISPATCH-CHECK 3문항 gate 통과. Q1 통과(결정론) + Q2 통과(multi-step) 작업은 기본 DELEGATE. KEEP 판정은 근거 1줄 명시. Destructive operation은 사용자 명시 승인 후 실행."

---

### 나의 추천 진행

1. **이 절차 검토·승인** ← 지금 여기
2. 승인 시: SDC SKILL.md 에 Section 0 추가 → commit → push → 설치본 pull
3. TCL 등록
4. 위키 `System_vs_Skill` 또는 신규 `patterns/SDC_Dispatch_Policy` 페이지로 정식화
5. 첫 시범: 이 절차 자체의 커밋·푸시·설치본 업데이트 → **STAGING 패턴으로 Sonnet 위임** (live test)

이 절차로 진행할까요? 또는 수정할 조항이 있나요?

## Q14

이렇게 진행할시에 실제 세션당토큰사용량의 효율화가 가능한가? 그리고 사용자의 매 요청마다 트리거될 판단기준이 오히려 토큰효율과 시간지연을 얼마나 가져오게되는가 궁금하다.

## A51

좋은 질문. 정량적으로 분석해보겠습니다 (수치는 order-of-magnitude, 모델 정확한 단가는 추정치).

## 1. 게이트 자체의 오버헤드

3-question gate는 **tool call 없이 순수 추론**이라 tool-call overhead는 0.

| 구현 방식 | 1회 실행 비용 | 세션당 100회 기준 |
|----------|-------------|---------------|
| **내재화** (입/출력 비공개, 습관화) | ~0 tok | $0 |
| **Trigger-only** (키워드 감지 시만) | ~100-300 tok Opus out | 5-20회 → **$0.04-$0.45** |
| **Always-on explicit** (매 요청 Q1/Q2/Q3 verbalize) | ~300 tok Opus out | 100회 → **$2.25** |

**내 추천: Trigger-only + 내재화 하이브리드.** 게이트를 매 요청마다 명시 verbalize는 낭비입니다.

## 2. 위임 vs 직접실행 break-even

(Opus 4.7 ≈ 5x Sonnet 4.6 per token, 추정 단가 기준)

**Delegation 1회 고정비용 (task 크기 무관):**
- SDC brief 작성 (Opus out): ~1000 tok → $0.075
- Subagent 컨텍스트 로드 (Sonnet in): ~10000 tok → $0.03
- 결과 요약 + 본체 verify: ~500 tok → $0.02
- **고정비용 합계: ~$0.12**

**Task 실행 비용 (크기 비례):**
- Opus 직접: task_tokens × Opus 출력 단가
- Sonnet 위임: task_tokens × Sonnet 출력 단가 (≈1/5)

**Break-even point:**
$$\text{fixed overhead} = \text{task\_tokens} \times (\text{opus\_rate} - \text{sonnet\_rate})$$
→ 대략 **task ≥ 2000 tokens** 일 때 delegation이 이득.

| 작업 크기 (Sonnet 실행 토큰) | Opus 직접 | Sonnet 위임 (overhead 포함) | Net |
|----------|--------|-------------|------|
| 500 tok (한 줄 수정) | $0.04 | $0.12 + $0.008 | **위임 손실 −$0.09** |
| 2000 tok (한 파일 refactor) | $0.15 | $0.12 + $0.03 | ≈ 본전 |
| 10000 tok (multi-file 이식) | $0.75 | $0.12 + $0.15 | **위임 이득 +$0.48** (64% 절감) |
| 30000 tok (대형 작업) | $2.25 | $0.12 + $0.45 | **위임 이득 +$1.68** (75% 절감) |

## 3. 토큰보다 중요한 *컨텍스트 보존* 효과

Opus의 context window가 오염되지 않는 이점 — 수치화 어렵지만 실제로 더 큽니다:

- **tool output 격리**: grep 결과 100줄·파일 전체 읽기·bash 출력이 Opus에 쌓이지 않음
- **긴 세션 지속력**: auto-compact 빈도 감소 → compact 시 정보 손실 회피
- **판단력 유지**: 구현 디테일이 Opus의 "working memory" 점유하지 않아 아키텍처 판단 선명도 유지

**체감**: 이 세션(35)만 봐도 TWK rename을 Sonnet 위임했을 때 본체는 11k+ 토큰의 mechanical diff를 직접 안 봐서 남은 용량이 지금 이 메타 설계 대화로 쓰임.

## 4. 시간 지연

| 구분 | 직접 실행 | Delegation |
|------|---------|-----------|
| Gate 판정 | 0-1초 | 0-1초 |
| Brief 작성 | — | 5-15초 |
| Subagent warmup | — | 5-30초 |
| 실제 작업 | task time | task time × 0.6-0.8 (Sonnet 빠름) |
| 검증 | — | 10-30초 |

**짧은 작업:** delegation이 30-60초 더 느림.
**긴 작업(>2분):** Sonnet 실행 속도 + 병렬성으로 오히려 빠를 수 있음.

## 5. 세션당 실제 효율 예상

**보수적 가정 (세션당 평균):**
- 게이트 적용 가능 task: 10회
- 실제 위임 가능 (Q1 pass): 5-7회
- 그 중 break-even 초과 (≥2k tok): 2-4회

**절감 추정:**
- 토큰 절감: $0.5-$2.0 (Opus 단가 기준)
- 게이트 overhead: $0.05-$0.45
- **Net gain: $0.5-$1.5 / 세션**
- **Context 보존 이점: 정량화 어려우나 체감상 세션당 1-2회 compact 회피 ≈ 상당한 가치**

## 6. 반대 케이스 — 이 게이트가 *손해*가 되는 시나리오

1. **미세편집 위주 세션** (주석 수정·문구 손질만): 모든 task가 Q2에서 KEEP → 게이트 비용만 발생
2. **디자인 중심 세션** (아키텍처·브레인스토밍): 모든 task가 Q1에서 KEEP → 게이트 돌릴 이유조차 없음
3. **사용자와의 빠른 대화 세션** (Q&A): task 자체가 없는데 게이트 체크하면 낭비

**대응:** Trigger-based 설계 (git/mv/batch/classify/verify 키워드 감지 시만 게이트 실행) → 위 시나리오들에서 overhead 0.

## 7. 수정된 추천 설계

원안(매 요청 3-gate) → **하이브리드로 수정:**

```
사용자 요청 수신
      │
      ▼
[Trigger 매칭?]  ── NO ──▶ 정상 처리 (gate 없음)
      │
      YES (git·mv·cp·batch·verify·classify 등)
      ▼
[Q1 Invariance] → NO면 KEEP
      │ YES
      ▼
[내재화된 Q2·Q3] → 빠른 판정 (overhead 최소)
      ▼
DELEGATE / STAGING / KEEP
```

**효과:**
- 게이트 overhead: **trigger 없는 대다수 요청에서 0**
- trigger 매칭 시만 ~100 tok 비용 (세션당 <$0.2)
- Break-even 초과 작업만 delegation → 확실한 net gain

## 결론

**단기(1-2세션):** 오히려 약간의 overhead가 눈에 띌 수 있음 (게이트 적응기).
**중장기(5+세션):** trigger 기반 설계면 세션당 토큰 $0.5-$1.5 절감 + context 보존 이점 명확.
**진정한 가치:** 토큰보다 **Opus 판단력 유지**. 이건 돈으로 환산 어렵지만 종일군도 체감하실 것.

이 하이브리드 설계(trigger-based + 내재화)로 진행할까요?

## Q15

좋음 하이브리드모드가 좋겠음. 그럼 진행해서 커밋푸시까지 진행.

## A52

하이브리드 모드 실행. 이 task 자체 gate 판정: Q1 YES (결정론적 paste) + Q2 KEEP direct (5~10 tool call 규모, overhead 미달) + Q3 Shared state. 본체 직접 실행하되 push는 검토 후.

## A53

커밋 + 푸시.

## A54

푸시 완료 (121e3ee). CURRENT_STATE 갱신.

## A55

완료.

## 최종 상태

**bobpullie/SDC @ 121e3ee** 푸시됨.

- **SKILL.md Section 0 추가** (68 lines 삽입): Auto-Dispatch Check 완전 명세
- **TCL #120 등록**: dispatch policy 규칙 DB 반영
- **설치본 동기화**: `E:/DnT/DnT_WesangGoon/.claude/skills/SDC.md` 도 동일 Section 0 삽입됨
- **CURRENT_STATE 갱신**

## 이 작업에 적용된 gate 판정 (live test)

| 단계 | 판정 | 근거 |
|------|------|------|
| Auto-trigger 매칭 | ✅ | `commit`·`push` 키워드 감지 |
| Q1 Invariance | PASS | Section 0 내용은 확정된 텍스트, paste 결정론적 |
| Q2 Overhead | **KEEP direct** | brief 작성(~1000 tok) > 직접 Edit 5회 |
| Q3 Reversibility | Shared state | 푸시 전 확인 완료, STAGING 불필요 (Q2 KEEP이 우선) |

**결론:** 이 task는 **KEEP direct** 판정 — Opus 본체가 직접 수행. 향후 동일 규모+결정론 task도 같은 경로.

## 타 에이전트 업데이트 경로

이제 리얼군·코드군이 SDC 업데이트 받으려면:

```bash
# SDC.md 단일 파일 설치 (현재 위상군 구조)
curl -o .claude/skills/SDC.md https://raw.githubusercontent.com/bobpullie/SDC/main/SKILL.md
```

Section 0 포함 최신 SDC가 전파됨. TWK·DVC는 이미 clone 구조라 `git pull` 한 줄.

## Q16

세션종료

## A56

세션종료 프로토콜 실행. session-lifecycle.md Step 1~7 순차 수행.
