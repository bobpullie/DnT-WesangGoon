---
date: 2026-04-21
type: raw
cssclass: twk-raw
tags: [session, raw, L2]
session: S4
---

# Session 4 — 2026-04-21

> Source: `63663133-91fb-4e06-a2dd-9349a30969ca.jsonl`
> Generated: 2026-04-21 17:21:50

## Q1

위상군 https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f 원래 Karpathy의 LLM위키는 옵시디언이  IDE역할을 한다고 하는데 어떻게 사용해야 옵시디언이 IDE처럼 사용할 수 있는거야?  그리고 Obsidian Web Clipper 이건 지금 기본 작동하는거지? 이미지를 로컬에 다운로드하세요. Obsidian 설정 < 이건 어떻게 하는걸 말하는거지? Marp 는 마크다운 기반 슬라이드 데크 형식입니다. Obsidian에는 이를 위한 플러그인이 있습니다. 위키 콘텐츠에서 직접 프레젠테이션을 생성하는 데 유용합니다.<  이건 어떤 플러그인이야?

## A1

Karpathy 원문과 위상군 TWK 스킬을 교차 확인하겠습니다.

## A2

Karpathy 원문에서 Obsidian 관련 언급을 정확히 파악하겠습니다.

## A3

Marp 플러그인 정확한 이름을 확인하겠습니다.

## A4

Karpathy 원문 raw를 한 번 더 확인하여 정확도를 높이겠습니다.

## A5

Karpathy 원문 verbatim과 교차 확인해 답변합니다.

## 1. Obsidian을 IDE처럼 쓴다는 의미

Karpathy 원문:
> "In practice, I have the LLM agent open on one side and Obsidian open on the other. The LLM makes edits based on our conversation, and I browse the results in real time."

즉 **별도 IDE가 아니라 split-screen 셋업**입니다:

- **왼쪽** — Claude Code (또는 터미널 에이전트) — LLM이 `docs/wiki/*.md`를 직접 편집
- **오른쪽** — Obsidian — 같은 폴더를 vault로 열어 실시간 렌더링

Obsidian이 "IDE 기능"을 하는 핵심 요소:
| 기능 | 역할 |
|------|------|
| **Graph view** | "what's connected, what's a hub, what's orphan" — wiki 구조 실시간 파악 |
| **wikilink 백링크 패널** | `[[…]]` 역참조 — 페이지 간 연결성 시각화 |
| **Dataview 렌더** | frontmatter를 읽어 index.md의 동적 테이블 자동 생성 |
| **Live preview / split pane** | 한쪽은 편집, 다른 쪽은 graph/index 열어놓고 탐색 |

**위상군 현재 상태로 체감하려면:**
1. Obsidian에서 `E:\DnT\DnT_WesangGoon` 을 vault로 열기 (이미 `.obsidian/` 있음)
2. 새 탭에서 `docs/wiki/index.md` 열기 → 또 다른 탭에서 graph view (`Ctrl+G`) 열기
3. 두 탭을 좌우 분할 (`Ctrl+\`)
4. Claude가 [docs/wiki/](docs/wiki/) 파일을 수정하면 Obsidian이 실시간 반영

이미 [.obsidian/snippets/twk.css](.obsidian/snippets/twk.css)와 Dataview가 S39에 세팅돼 있으므로, Obsidian 창만 띄워놓으면 IDE 모드는 즉시 가동됩니다.

## 2. Obsidian Web Clipper — 기본 작동 여부

**아니요, 기본 내장이 아닙니다.** 별도로 브라우저 확장을 설치해야 합니다.

- 공식 확장: [obsidianmd/obsidian-clipper](https://github.com/obsidianmd/obsidian-clipper) (Anthropic 아닌 Obsidian 공식팀)
- 설치처: [Chrome Web Store](https://chromewebstore.google.com/detail/obsidian-web-clipper/cnjifjpddelmedmihgijeibhnjfabmlf) / [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/web-clipper-obsidian/)
- **기본 설정만으로 바로 쓸 수 있음** — 설치 후 아티클 페이지에서 확장 아이콘 클릭 → vault 폴더 지정 → markdown으로 저장
- 위상군 vault에서는 Mode B(session-extract) 중심이라 raw 수집 빈도가 낮지만, 외부 아티클을 `raw/` 또는 L1 소스로 흡수할 때 유용

## 3. "Obsidian 설정" (이미지 로컬 다운로드) — 정확한 경로

Karpathy 원문 그대로:
> "Download images locally. In Obsidian Settings → Files and links, set "Attachment folder path" to a fixed directory (e.g. `raw/assets/`). Then in Settings → Hotkeys, search for "Download" to find "Download attachments for current file" and bind it to a hotkey (e.g. Ctrl+Shift+D). After clipping an article, hit the hotkey and all images get downloaded to local disk."

구체 절차:
1. Obsidian 좌하단 ⚙️ (Settings) 열기
2. **Files and links** 탭 → `Attachment folder path` → `raw/assets/` 입력
3. **Hotkeys** 탭 → 검색창에 `Download` 입력 → `Download attachments for current file` 명령 옆 `+` 클릭 → `Ctrl+Shift+D` 지정
4. Web Clipper로 아티클 클리핑 후, 해당 파일에서 `Ctrl+Shift+D` → 모든 원격 이미지 URL이 `raw/assets/`로 저장되고 본문 링크가 로컬 경로로 치환됨

**의도:** URL이 끊겨도 이미지가 살아있게 — L1 raw source의 immutability 원칙과 연결.

**주의:** "Download attachments for current file" 명령은 Obsidian 기본 기능이지만 버전/플랫폼에 따라 커뮤니티 플러그인(`Local images plus` 등)이 필요한 경우도 있음. 먼저 Hotkeys 검색에서 나오는지 확인 → 없으면 Community plugin 설치.

## 4. Marp 플러그인 — 정확한 이름

Karpathy는 "Obsidian has a plugin for it"이라고만 언급. 2026년 4월 기준 주류는:

| 플러그인 | 저장소 | 특징 |
|---------|--------|------|
| **Marp Slides** (추천) | [samuele-cozzi/obsidian-marp-slides](https://github.com/samuele-cozzi/obsidian-marp-slides) | 가장 활발. HTML/PDF/PPTX/PNG export, 커스텀 CSS 테마 지원 |
| Marp Presentations | [bjesuiter/obsidian-marp-presentations](https://github.com/bjesuiter/obsidian-marp-presentations) | marp-core npm 얇은 래퍼 |
| Marp Plugin | [JichouP/obsidian-marp-plugin](https://github.com/JichouP/obsidian-marp-plugin) | 단순 구현 |

Community Plugins → Browse → `Marp Slides` 검색 → Install → Enable 하면 됨. wiki 페이지 상단 frontmatter에 `marp: true` 만 추가하면 그 페이지를 슬라이드로 export 가능. 위상군에서는 decisions/postmortems 발표용으로 활용 여지가 있습니다.

---

**위상군 맥락 정리:** Karpathy 셋업 4요소 중 — Web Clipper와 Marp는 아직 미설치(임의), 이미지 다운로드 설정은 vault 설정 1회 작업, "IDE로서의 Obsidian"은 이미 [docs/wiki/](docs/wiki/) + Dataview + twk.css로 준비 완료. S40의 P2 `Wiki-Visual-Audit` 작업 시 Obsidian 창 띄워놓고 진행하면 그 자체가 Karpathy식 워크플로우입니다.

Sources:
- [Karpathy llm.wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [obsidianmd/obsidian-clipper (official)](https://github.com/obsidianmd/obsidian-clipper)
- [Obsidian Web Clipper product page](https://obsidian.md/clipper)
- [samuele-cozzi/obsidian-marp-slides](https://github.com/samuele-cozzi/obsidian-marp-slides)
- [bjesuiter/obsidian-marp-presentations](https://github.com/bjesuiter/obsidian-marp-presentations)

## Q2

내가 이해하기로는 옵시디언에 글을 적으면 마치 프롬프트 입력하듯 에이전트가 읽어서 해당 글을 프롬프트로 가져간다는 것처럼 이해했어. 그래서 글을작성한다음에 특정 명령을 하면 에이전트가 해당 글을 읽고 마치 프롬프트입력받은 거처럼 동작한다는거 같은데 아닌가?

## A6

방향이 반대입니다. 정확한 흐름을 정리할게요.

## Karpathy 원문의 실제 방향

> "The LLM makes edits based on **our conversation**, and I browse the results in real time."

즉:

```
[대화 (CLI/터미널)]  →  LLM이 wiki/*.md 편집  →  [Obsidian 뷰어]
     ↑                                                ↓
   사용자 입력                              사용자가 실시간 읽음
```

- **프롬프트는 여전히 터미널/CLI에서 입력** — Claude Code 채팅창이 그 역할
- **Obsidian 역할은 "쓰기"가 아니라 "읽기/검토"** — LLM이 업데이트한 결과를 graph view·백링크·Dataview로 실시간 확인
- **인간의 Obsidian 편집**도 가능하지만, 그건 "프롬프트 입력"이 아니라 **curation (인간 큐레이션)** — Karpathy 원칙 #3 "Humans do curation and direction, LLMs do the bookkeeping"

## 그럼 사용자가 이해한 방향은 왜 그럴듯하게 보이는가

사실 **간접적으로는 맞습니다.** Karpathy의 "Compilation > RAG" 원칙 때문에:

1. 사용자가 Obsidian에서 `docs/wiki/concepts/SDC.md`에 한 줄 추가
2. 다음 세션에 Claude한테 "SDC가 뭔지 참고해서 답해줘"라고 요청
3. Claude가 `Read` 툴로 그 파일을 읽음 → **방금 쓴 줄이 프롬프트 컨텍스트로 들어옴**

이건 "Obsidian = 프롬프트 입력창"이 아니라 **"Obsidian = 누적 지식 저장소, 그 파일을 LLM이 읽음"**의 결과입니다. 결과만 보면 비슷해 보이지만 메커니즘이 다릅니다:
- **프롬프트 직접 주입**: 사용자가 채팅창에 타이핑 → 즉시 컨텍스트 진입
- **Karpathy 방식**: 파일 편집 → LLM이 다음 요청 처리 시 `Read`로 가져옴 (인간이 "이 파일 봐줘" 하거나 에이전트가 스스로 탐색)

## "Obsidian에 쓰면 자동으로 프롬프트가 된다" 는 구현하려면

Karpathy 기본 셋업에는 없지만, **별도 훅/플러그인으로 가능**합니다:

| 방식 | 메커니즘 |
|------|----------|
| **UserPromptSubmit hook** | 위상군은 이미 사용 중 — 매 prompt마다 `preflight-memory-check`로 TCL/TGL 주입. Obsidian 특정 파일을 자동 주입하도록 커스터마이징 가능 |
| **Obsidian plugin (Copilot/Smart Composer)** | Obsidian 안에서 직접 Claude API 호출. 선택 텍스트를 프롬프트로 전송 |
| **Watcher 스크립트** | `docs/wiki/inbox.md` 같은 파일 변경 감지 → Claude Code CLI로 pipe |
| **File include 규칙** | `handover_doc/CURRENT_STATE.md`가 SessionStart hook으로 자동 주입되는 것과 동일 원리 — 위상군은 이미 이 방식 사용 중 |

실제로 위상군 셋업은 이미 **하이브리드**에 가깝습니다:
- [handover_doc/CURRENT_STATE.md](handover_doc/CURRENT_STATE.md) 는 세션 시작 시 자동 주입 → "Obsidian에서 편집하면 다음 세션 프롬프트로 들어감"과 동일 효과
- [memory/](memory/) 의 TCL/TGL은 매 prompt preflight로 주입
- [docs/wiki/](docs/wiki/) 는 명시적 `Read` 요청 시에만 진입 (Karpathy 표준 방식)

## 정리

| 사용자 이해 | 실제 Karpathy 방식 |
|-------------|---------------------|
| Obsidian에 쓰기 → 명령어 → LLM이 프롬프트로 받음 | 대화로 요청 → LLM이 쓰기 → 사용자가 Obsidian에서 읽기 |
| Obsidian = **입력 창** | Obsidian = **출력 뷰어 + 인간 큐레이션 창** |
| 능동 트리거 필요 | 단순 split-screen 배치만 필요 |

**그런데 사용자 방향도 유효한 패턴**입니다 — 위상군 `CURRENT_STATE.md` 자동 주입이 이미 그것의 축약판. Obsidian `inbox.md`를 SessionStart hook에 추가하면 "Obsidian → 프롬프트 자동 주입" 워크플로우 즉시 구축 가능합니다. 원하시면 설계해드릴 수 있어요.

## Q3

일단 여기서 이 사안은 잘 정리해줘 조만간 실제 프로젝트로 승격할 수 있으니.

## A7

Wiki 구조 확인 후 적절한 섹션에 정리하겠습니다.

## A8

새 concept 페이지를 생성하고 log.md에 기록하겠습니다.

## A9

정리 완료했습니다.

## 산출물

| 파일 | 내용 |
|------|------|
| [docs/wiki/concepts/Obsidian_as_IDE.md](docs/wiki/concepts/Obsidian_as_IDE.md) | 신규 concept 페이지 (Draft) — Karpathy verbatim 인용 2건, 4축 구성요소(Viewer/Navigator/Query/Ingestion), 위상군 현재 상태 매트릭스, 양방향 파이프 변형 문서화, 승격 트리거 3종 |
| [docs/wiki/log.md](docs/wiki/log.md) | append-only 항목 추가 — Ingest 기록 + 페이지 수 18→19 |

## 핵심 기록 포인트 (승격 시 재활용할 수 있도록)

1. **단방향 vs 양방향 구분** — Karpathy 원문은 단방향 (대화 → LLM 편집 → Obsidian 뷰어), 위상군은 이미 SessionStart/UserPromptSubmit hook 으로 **부분 양방향** 구현 중
2. **승격 트리거 3종 명시** — 외부 ingest 수요 / 발표 수요 / `inbox.md` 감시 hook 중 하나가 발생하면 Draft → Active 전환
3. **도구 별도 설치 목록** — Web Clipper · 이미지 다운로드 설정 · Marp Slides 전부 미설치 상태 명시 (승격 시 체크리스트로 사용)
4. **TGL #58 원칙 적용** — "Download attachments for current file" 명령은 Obsidian 버전에 따라 community plugin 필요할 수 있음을 주의점에 기록 (웹 문서 예시 무조건 신뢰 금지)
5. **관련 개념 wikilink** — SDC / TEMS / Self_Containment / Per_Agent_Local_QMD 와 연결 — Obsidian graph view 에서 자동 표시됨

[index.md](docs/wiki/index.md) 의 Dataview 쿼리가 자동으로 이 페이지를 "Concepts" 테이블에 포함시키므로 별도 편집 불필요. 다음 세션에 Obsidian 열면 graph view 에 노드가 생성돼 있을 겁니다.

## Q4

그럼 여기서 세셔종료

## A10

세션 종료 프로토콜 실행. 기존 S39 핸드오버 스타일 참조 후 S40 산출물 작성하겠습니다.

## A11

S40 세션 산출물 3종 작성 + L2 extract 실행.
