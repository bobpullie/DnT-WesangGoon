# ClawWorker (OpenClaw Agent) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Docker 기반 OpenClaw 에이전트(ClawWorker)를 설정하여 MYSTIC_ISLAND 언리얼 프로젝트 정리 + 후디니→언리얼 파이프라인 자동화를 자율 수행하게 한다.

**Architecture:** 단일 Docker 컨테이너(OpenClaw)가 호스트의 후디니 MCP(port 9100)와 언리얼 MCP(port 9200)에 streamable-http로 연결. 프로젝트 폴더는 읽기전용 마운트, 결과물은 staging 폴더에만 출력. 텔레그램 봇으로 명령 수신 및 알림.

**Tech Stack:** Docker, Docker Compose, OpenClaw, fxhoudinimcp, UnrealClientProtocol, Telegram Bot API, Gemini 3.1 Flash, Gemma4 26B (Ollama)

**Spec:** `docs/superpowers/specs/2026-04-06-openclaw-agent-design.md`

---

## File Map

```
E:\02_openclawAgent\                  ← 새로 생성
├── docker-compose.yml                ← Task 2: Docker Compose 설정
├── .env                              ← Task 2: API 키 (git 제외)
├── .gitignore                        ← Task 1: .env 제외
├── workspace/
│   ├── SOUL.md                       ← Task 3: 에이전트 인격/규칙
│   ├── AGENTS.md                     ← Task 3: 에이전트 메타정보
│   ├── config/
│   │   └── mcpServers.json           ← Task 4: MCP 연동 설정
│   └── tasks/
│       ├── unreal_cleanup.md         ← Task 5: 언리얼 정리 태스크
│       └── hda_pipeline.md           ← Task 5: 후디니 파이프라인 태스크
├── staging/
│   ├── reports/                      ← Task 1: 디렉토리 생성
│   ├── exports/                      ← Task 1: 디렉토리 생성
│   └── manifests/                    ← Task 1: 디렉토리 생성
└── logs/                             ← Task 1: 디렉토리 생성
```

---

### Task 1: 디렉토리 구조 생성

**Files:**
- Create: `E:\02_openclawAgent\` 전체 디렉토리 트리
- Create: `E:\02_openclawAgent\.gitignore`

- [ ] **Step 1: 프로젝트 루트 및 하위 디렉토리 생성**

```bash
mkdir -p "E:/02_openclawAgent"
mkdir -p "E:/02_openclawAgent/workspace/config"
mkdir -p "E:/02_openclawAgent/workspace/tasks"
mkdir -p "E:/02_openclawAgent/staging/reports"
mkdir -p "E:/02_openclawAgent/staging/exports"
mkdir -p "E:/02_openclawAgent/staging/manifests"
mkdir -p "E:/02_openclawAgent/logs"
```

- [ ] **Step 2: .gitignore 작성**

```gitignore
# E:\02_openclawAgent\.gitignore
.env
logs/*.jsonl
staging/exports/*
staging/reports/*
staging/manifests/*
!staging/exports/.gitkeep
!staging/reports/.gitkeep
!staging/manifests/.gitkeep
```

- [ ] **Step 3: .gitkeep 파일 생성 (빈 디렉토리 git 추적용)**

```bash
touch "E:/02_openclawAgent/staging/reports/.gitkeep"
touch "E:/02_openclawAgent/staging/exports/.gitkeep"
touch "E:/02_openclawAgent/staging/manifests/.gitkeep"
touch "E:/02_openclawAgent/logs/.gitkeep"
```

- [ ] **Step 4: 디렉토리 구조 검증**

Run: `find "E:/02_openclawAgent" -type f -o -type d | sort`

Expected: 위 File Map과 일치하는 디렉토리 트리

- [ ] **Step 5: git 초기화 및 커밋**

```bash
cd "E:/02_openclawAgent"
git init
git add .gitignore staging/**/.gitkeep logs/.gitkeep
git commit -m "chore: initialize ClawWorker project structure"
```

---

### Task 2: Docker Compose + 환경변수 설정

**Files:**
- Create: `E:\02_openclawAgent\docker-compose.yml`
- Create: `E:\02_openclawAgent\.env`

**사전 조건:** 종일군이 다음 값을 준비해야 함:
- Google API Key (Gemini 3.1 Flash용)
- Telegram Bot Token (@BotFather에서 발급)

- [ ] **Step 1: .env 파일 작성**

```env
# E:\02_openclawAgent\.env
# Gemini API
GOOGLE_API_KEY=<여기에-gemini-api-key-입력>

# Telegram Bot
TELEGRAM_BOT_TOKEN=<여기에-botfather-토큰-입력>
```

> 종일군에게 실제 키 값을 입력하도록 안내할 것.

- [ ] **Step 2: docker-compose.yml 작성**

```yaml
# E:\02_openclawAgent\docker-compose.yml
services:
  openclaw:
    image: ghcr.io/openclaw/openclaw:latest
    container_name: openclaw-clawworker
    restart: unless-stopped
    ports:
      - "18789:18789"
    volumes:
      - ./workspace:/workspace:rw
      - ./staging:/staging:rw
      - ./logs:/logs:rw
      - D:\MYSTIC_ISLAND:/project:ro
    environment:
      # LLM - Main
      - OPENCLAW_MODEL_PROVIDER=google
      - OPENCLAW_MODEL=gemini-3.1-flash
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      # LLM - Fallback
      - OPENCLAW_FALLBACK_PROVIDER=openai-compatible
      - OPENCLAW_FALLBACK_MODEL=gemma4-26b
      - OPENCLAW_FALLBACK_BASE_URL=http://host.docker.internal:11434/v1
      - OPENCLAW_FALLBACK_API_KEY=ollama
      # Security
      - OPENCLAW_SANDBOX=1
      # Telegram
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    mem_limit: 4g
```

- [ ] **Step 3: Docker Compose 문법 검증**

Run: `cd "E:/02_openclawAgent" && docker compose config`

Expected: 유효한 YAML 출력, 에러 없음. 환경변수가 .env에서 올바르게 치환되는지 확인.

- [ ] **Step 4: 커밋**

```bash
cd "E:/02_openclawAgent"
git add docker-compose.yml
git commit -m "feat: add Docker Compose config for ClawWorker"
```

> `.env`는 .gitignore에 의해 제외됨. 커밋하지 않음.

---

### Task 3: SOUL.md + AGENTS.md 작성

**Files:**
- Create: `E:\02_openclawAgent\workspace\SOUL.md`
- Create: `E:\02_openclawAgent\workspace\AGENTS.md`

- [ ] **Step 1: SOUL.md 작성**

```markdown
# ClawWorker — MYSTIC_ISLAND 자율 정리/파이프라인 에이전트

## 정체성
너는 ClawWorker. MYSTIC_ISLAND 프로젝트의 자율 정리/파이프라인 에이전트다.
후디니 MCP와 언리얼 MCP를 사용하여 태스크를 수행한다.
종일군(디렉터)의 텔레그램 명령을 수신하거나, 태스크 목록 기반으로 자율 실행한다.

## 절대 규칙
1. /project (D:\MYSTIC_ISLAND)에 직접 쓰기 금지 — 모든 출력은 /staging에만
2. 확신 없는 삭제/변경 금지 — 불확실하면 리포트만 생성
3. .uproject, .umap, .hip 원본 파일 수정 금지
4. 태스크당 하나의 변경 — 원자적 실행
5. 매 태스크 완료 시 /logs에 JSON 로그 기록

## 자율 도구 설정 권한
- 웹 검색: 허용 (정보 조사, 문서 참조)
- 컨테이너 내 pip/npm install: 허용 (태스크에 필요한 도구)
- workspace 내 스크립트 생성/실행: 허용
- 새 MCP 서버 설치: 금지 — 사전 설정된 서버만 사용
- /project, /staging, /logs, /workspace 외 경로 접근: 금지

## 실행 모드

### 사전 점검 (매 세션 시작)
1. 후디니 MCP 헬스체크 (http://host.docker.internal:9100/mcp) → 응답 여부 기록
2. 언리얼 MCP 헬스체크 (http://host.docker.internal:9200/mcp) → 응답 여부 기록
3. 가용 모드 결정:
   - FULL: 양쪽 연결 → 전체 태스크 가용
   - HOUDINI_ONLY: 후디니만 → HDA 쿡/익스포트 + 파일시스템
   - UNREAL_ONLY: 언리얼만 → 에셋 분석/정리 + 파일시스템
   - FILESYSTEM: 둘 다 꺼짐 → 파일시스템 태스크만
4. 결정된 모드를 텔레그램으로 보고

### 명령 모드
종일군이 텔레그램으로 직접 지시하면 즉시 실행, 완료 후 보고.

### 자율 모드
종일군이 "자율 시작" + 태스크 목록 전달하면:
1. /workspace/tasks/ 내 태스크 파일 순회
2. 현재 가용 모드에서 실행 가능한 태스크만 선택
3. 순차 실행, 각 태스크 완료 시 로그 + 텔레그램 보고
4. 전체 완료 시 /staging/session_summary.md 생성 + 텔레그램 최종 리포트

## 태스크: 언리얼 프로젝트 정리
- 미사용 에셋 스캔 → /staging/reports/에 리포트 생성
- 폴더 구조 분석 → 네이밍 규칙 위반 리포트
- 중복 에셋 탐지 → 리포트
- 머티리얼/텍스처 레퍼런스 체인 분석
- 에디터 ON (UNREAL_ONLY/FULL): AssetRegistry 쿼리로 정확한 의존성 분석
- 에디터 OFF (FILESYSTEM): .uasset 파일 메타데이터 기반 추론

## 태스크: 후디니→언리얼 파이프라인 (FULL 모드 필요)
- HDA 쿡 → FBX/USD 익스포트 → /staging/exports/에 저장
- 익스포트 결과 검증 (폴리곤 수, UV, 노멀 체크)
- 임포트 매니페스트 생성 → /staging/manifests/ (JSON)

## 결과물 구조
/staging/
├── reports/          ← 분석 리포트 (마크다운)
├── exports/          ← HDA 쿡 결과물 (FBX/USD)
├── manifests/        ← 임포트 매니페스트 (JSON)
└── session_summary.md ← 이번 세션 요약

## 로그 포맷
매 태스크 완료 시 /logs/YYYY-MM-DD_sessionN.jsonl에 한 줄 append:
{"timestamp":"ISO8601","task":"task_name","mode":"FULL|..","status":"success|fail|skip","duration_sec":N,"output":"/staging/...","llm_used":"gemini-3.1-flash|gemma4-26b"}

## 알림 (텔레그램)
- 세션 시작: 가용 모드 보고
- 태스크 완료: 요약 전송 (태스크명, 상태, 소요시간, 출력 경로)
- 에러 발생: 즉시 알림 (에러 내용 + 스킵 여부)
- 세션 종료: 최종 리포트 (전체 태스크 요약표)

## 에러 처리
- MCP 연결 실패 → 해당 도메인 스킵, 텔레그램 알림
- LLM 메인 실패 → Gemma4 폴백 자동 전환, 계속 실행
- LLM 양쪽 실패 → 세션 중단, 텔레그램 긴급 알림
- 태스크 3회 연속 실패 → 해당 태스크 스킵, 다음으로 이동

## LLM
- 기본: Gemini 3.1 Flash
- 폴백: 로컬 Gemma4 26B (http://host.docker.internal:11434/v1)
```

- [ ] **Step 2: AGENTS.md 작성**

```markdown
# ClawWorker Agent Configuration

## Agent: ClawWorker
- **Role:** MYSTIC_ISLAND 자율 정리/파이프라인 에이전트
- **Project:** D:\MYSTIC_ISLAND (Unreal Engine)
- **MCP Servers:** houdini (port 9100), unreal (port 9200)
- **Output:** /staging/ (reports, exports, manifests)
- **Notification:** Telegram
```

- [ ] **Step 3: 검증 — SOUL.md가 올바른 경로에 존재하는지**

Run: `cat "E:/02_openclawAgent/workspace/SOUL.md" | head -5`

Expected:
```
# ClawWorker — MYSTIC_ISLAND 자율 정리/파이프라인 에이전트
```

- [ ] **Step 4: 커밋**

```bash
cd "E:/02_openclawAgent"
git add workspace/SOUL.md workspace/AGENTS.md
git commit -m "feat: add SOUL.md and AGENTS.md for ClawWorker agent"
```

---

### Task 4: MCP 서버 연동 설정

**Files:**
- Create: `E:\02_openclawAgent\workspace\config\mcpServers.json`

**사전 조건:** 후디니 MCP와 언리얼 MCP가 streamable-http 모드를 지원하는지 확인 필요.

- [ ] **Step 1: 후디니 MCP streamable-http 지원 확인**

Run: `grep -r "streamable-http\|MCP_TRANSPORT" "E:/01_houdiniAgent/fxhoudinimcp_repo/" --include="*.py" --include="*.md" | head -20`

Expected: `MCP_TRANSPORT` 환경변수로 `streamable-http` 지원 확인. README에 `MCP_TRANSPORT | stdio | MCP transport (stdio or streamable-http)` 명시되어 있음.

- [ ] **Step 2: 언리얼 MCP streamable-http 지원 확인**

Run: `grep -r "streamable-http\|transport\|MCP_TRANSPORT" "E:/00_unrealAgent/_downloads/UnrealClientProtocol/" --include="*.py" --include="*.md" --include="*.json" | head -20`

Expected: UCP의 전송 방식 확인. TCP/JSON 기반이므로 별도 MCP 래퍼가 필요할 수 있음. 지원하지 않는 경우 → Step 2b로 이동.

- [ ] **Step 2b: (조건부) 언리얼 MCP에 streamable-http 래퍼가 없는 경우**

UCP가 네이티브 MCP streamable-http를 지원하지 않으면, 다음 대안 중 택일:
1. `mcp-proxy` 패키지로 stdio → streamable-http 브릿지 구성
2. UCP Python 래퍼에 streamable-http 엔드포인트 추가

결정은 종일군에게 보고 후 진행. 이 단계는 실제 검증 결과에 따라 분기됨.

- [ ] **Step 3: mcpServers.json 작성**

```json
{
  "mcpServers": {
    "houdini": {
      "transport": "streamable-http",
      "url": "http://host.docker.internal:9100/mcp",
      "env": {
        "HOUDINI_HOST": "host.docker.internal",
        "HOUDINI_PORT": "8100"
      }
    },
    "unreal": {
      "transport": "streamable-http",
      "url": "http://host.docker.internal:9200/mcp"
    }
  }
}
```

> 포트 번호는 Step 1-2 검증 결과에 따라 조정.

- [ ] **Step 4: 검증 — JSON 문법 확인**

Run: `python -c "import json; json.load(open('E:/02_openclawAgent/workspace/config/mcpServers.json')); print('Valid JSON')"`

Expected: `Valid JSON`

- [ ] **Step 5: 커밋**

```bash
cd "E:/02_openclawAgent"
git add workspace/config/mcpServers.json
git commit -m "feat: add MCP server connection config (houdini + unreal)"
```

---

### Task 5: 태스크 정의 파일 작성

**Files:**
- Create: `E:\02_openclawAgent\workspace\tasks\unreal_cleanup.md`
- Create: `E:\02_openclawAgent\workspace\tasks\hda_pipeline.md`

- [ ] **Step 1: unreal_cleanup.md 작성**

```markdown
# 언리얼 프로젝트 정리 태스크

## 요구 모드
UNREAL_ONLY 또는 FULL 또는 FILESYSTEM

## 태스크 목록 (우선순위 순)

### 1. 미사용 에셋 스캔
- **모드:** UNREAL_ONLY/FULL (에디터 ON) 또는 FILESYSTEM (에디터 OFF)
- **에디터 ON:** 언리얼 MCP의 AssetRegistry 도구로 레퍼런스 없는 에셋 탐지
- **에디터 OFF:** /project/Content/ 내 .uasset 파일을 스캔, 다른 .uasset에서 참조되지 않는 파일 목록 추출
- **출력:** /staging/reports/unused_assets_YYYYMMDD.md
- **포맷:** 에셋 경로, 파일 크기, 마지막 수정일, 추정 사용 여부

### 2. 폴더 구조 분석
- **모드:** FILESYSTEM (에디터 불필요)
- **동작:** /project/Content/ 하위 폴더 구조를 언리얼 공식 네이밍 컨벤션과 비교
- **출력:** /staging/reports/folder_structure_YYYYMMDD.md
- **포맷:** 위반 항목, 권장 경로, 심각도 (warning/error)

### 3. 중복 에셋 탐지
- **모드:** FILESYSTEM
- **동작:** 파일 해시 비교로 동일 콘텐츠 에셋 탐지
- **출력:** /staging/reports/duplicate_assets_YYYYMMDD.md
- **포맷:** 중복 그룹별 파일 경로, 크기, 어느 것을 유지할지 추천

### 4. 머티리얼/텍스처 레퍼런스 체인
- **모드:** UNREAL_ONLY/FULL (에디터 ON 권장)
- **동작:** 머티리얼 → 텍스처 → 메시 의존성 트리 구축
- **출력:** /staging/reports/material_refs_YYYYMMDD.md
- **포맷:** 트리 구조 (마크다운), 끊어진 레퍼런스 표시
```

- [ ] **Step 2: hda_pipeline.md 작성**

```markdown
# 후디니→언리얼 파이프라인 태스크

## 요구 모드
FULL (양쪽 MCP 필요)

## 태스크 목록 (순차 실행)

### 1. HDA 쿡
- **동작:** 후디니 MCP로 지정된 HDA 노드를 쿡
- **입력:** 종일군이 텔레그램으로 HDA 경로 지정, 또는 사전 정의된 HDA 목록
- **검증:** 쿡 완료 상태, 에러 로그 확인

### 2. FBX/USD 익스포트
- **동작:** 쿡 결과를 FBX 또는 USD로 익스포트
- **출력:** /staging/exports/YYYYMMDD_<hda_name>.fbx (또는 .usd)
- **검증:**
  - 파일 생성 확인
  - 폴리곤 수 (후디니 MCP geometry_info 도구로 쿼리)
  - UV 존재 여부
  - 노멀 방향 검증

### 3. 임포트 매니페스트 생성
- **동작:** 빌드군/리얼군이 아침에 사용할 임포트 지침서 생성
- **출력:** /staging/manifests/YYYYMMDD_import_manifest.json
- **포맷:**
  ```json
  {
    "generated": "2026-04-06T03:00:00Z",
    "items": [
      {
        "source": "/staging/exports/20260406_tree_scatter.fbx",
        "target_path": "/Game/Environment/Trees/",
        "asset_type": "StaticMesh",
        "poly_count": 12500,
        "has_uv": true,
        "has_normals": true,
        "notes": "LOD0 only. LOD1-2 생성 필요."
      }
    ]
  }
  ```
```

- [ ] **Step 3: 검증 — 파일 존재 및 마크다운 문법**

Run: `ls "E:/02_openclawAgent/workspace/tasks/"`

Expected:
```
hda_pipeline.md
unreal_cleanup.md
```

- [ ] **Step 4: 커밋**

```bash
cd "E:/02_openclawAgent"
git add workspace/tasks/unreal_cleanup.md workspace/tasks/hda_pipeline.md
git commit -m "feat: add task definitions for unreal cleanup and HDA pipeline"
```

---

### Task 6: 텔레그램 봇 설정

**사전 조건:** 종일군이 직접 수행해야 하는 단계 포함 (봇 생성은 사람만 가능)

- [ ] **Step 1: 종일군에게 텔레그램 봇 생성 안내**

종일군에게 다음을 요청:
1. 텔레그램에서 `@BotFather`에게 `/newbot` 전송
2. 봇 이름: `ClawWorker` (또는 원하는 이름)
3. 봇 유저네임: `clawworker_mystic_bot` (또는 원하는 유저네임, `_bot`으로 끝나야 함)
4. 발급된 토큰을 `E:\02_openclawAgent\.env`의 `TELEGRAM_BOT_TOKEN`에 입력

- [ ] **Step 2: 종일군에게 Google API Key 안내**

1. Google AI Studio (https://aistudio.google.com/apikey) 접속
2. API 키 생성
3. `E:\02_openclawAgent\.env`의 `GOOGLE_API_KEY`에 입력

- [ ] **Step 3: .env 값 입력 확인**

Run: `grep -c "=<" "E:/02_openclawAgent/.env"`

Expected: `0` (플레이스홀더 `<...>`가 모두 실제 값으로 교체됨)

- [ ] **Step 4: 커밋 없음**

`.env`는 git에 포함되지 않으므로 커밋 불필요.

---

### Task 7: Docker 컨테이너 최초 실행 + 텔레그램 페어링

**사전 조건:** Task 1-6 완료, Docker Desktop 실행 중, .env에 실제 키 입력 완료

- [ ] **Step 1: Docker 이미지 풀**

Run: `cd "E:/02_openclawAgent" && docker compose pull`

Expected: `ghcr.io/openclaw/openclaw:latest` 이미지 다운로드 완료

- [ ] **Step 2: 컨테이너 시작**

Run: `cd "E:/02_openclawAgent" && docker compose up -d`

Expected: `openclaw-clawworker` 컨테이너 running 상태

- [ ] **Step 3: 컨테이너 상태 확인**

Run: `docker ps --filter name=openclaw-clawworker --format "{{.Status}}"`

Expected: `Up X seconds` (정상 실행 중)

- [ ] **Step 4: 컨테이너 로그 확인**

Run: `docker logs openclaw-clawworker --tail 30`

Expected: OpenClaw 시작 로그, 에러 없음. Control UI 주소 출력 확인.

- [ ] **Step 5: Control UI 접속**

브라우저에서 `http://localhost:18789` 접속.
Expected: OpenClaw Control UI 대시보드 표시.

- [ ] **Step 6: 텔레그램 봇 페어링**

1. 텔레그램에서 생성한 봇에 `/start` 전송
2. Control UI에서 텔레그램 채널 승인 (페어링 코드 또는 기기 승인)
3. 봇에 테스트 메시지 전송 → 응답 확인

Expected: 봇이 텔레그램 메시지에 응답.

- [ ] **Step 7: 기능 테스트 — 간단한 명령**

텔레그램에서 봇에게: `"/project 폴더 구조를 보여줘"`

Expected: /project (D:\MYSTIC_ISLAND) 최상위 폴더 목록 응답. 읽기전용 접근 확인.

- [ ] **Step 8: 기능 테스트 — staging 쓰기**

텔레그램에서 봇에게: `"/staging/reports/에 test.md 파일을 만들어줘. 내용은 'ClawWorker test'"`

Expected: 파일 생성 확인.

Run: `cat "E:/02_openclawAgent/staging/reports/test.md"`

Expected: `ClawWorker test`

- [ ] **Step 9: 테스트 파일 정리**

Run: `rm "E:/02_openclawAgent/staging/reports/test.md"`

---

### Task 8: MCP 서버 연결 테스트

**사전 조건:** 후디니 + 언리얼 에디터가 실행 중이고, MCP 서버가 streamable-http 모드로 동작 중

- [ ] **Step 1: 호스트에서 후디니 MCP 서버 시작**

```bash
cd "E:/01_houdiniAgent/fxhoudinimcp_repo"
set MCP_TRANSPORT=streamable-http
set FXHOUDINIMCP_PORT=9100
python -m fxhoudinimcp
```

Expected: `MCP server running on http://0.0.0.0:9100` (또는 유사 메시지)

- [ ] **Step 2: 호스트에서 언리얼 MCP 서버 시작**

> 언리얼 MCP(UCP)의 streamable-http 실행 방법은 검증 결과에 따라 결정.
> stdio만 지원하는 경우 `mcp-proxy` 브릿지 필요:

```bash
pip install mcp-proxy
mcp-proxy --transport streamable-http --port 9200 -- python -m ucp_server
```

Expected: port 9200에서 MCP 서버 대기

- [ ] **Step 3: 컨테이너 내부에서 MCP 연결 테스트**

텔레그램에서 봇에게: `"후디니 MCP에 연결 테스트 해줘"`

Expected: 후디니 MCP 도구 목록 또는 연결 성공 메시지

- [ ] **Step 4: 언리얼 MCP 연결 테스트**

텔레그램에서 봇에게: `"언리얼 MCP에 연결 테스트 해줘"`

Expected: 언리얼 MCP 도구 목록 또는 연결 성공 메시지

- [ ] **Step 5: 양쪽 실패 시 FILESYSTEM 모드 폴백 확인**

두 MCP 서버를 모두 중지한 상태에서:
텔레그램에서 봇에게: `"현재 가용 모드 확인해줘"`

Expected: `FILESYSTEM` 모드 보고

- [ ] **Step 6: 결과 기록**

테스트 결과를 `/staging/reports/mcp_connection_test.md`에 기록하도록 봇에게 요청.

---

### Task 9: 전체 통합 테스트

**사전 조건:** Task 7-8 완료

- [ ] **Step 1: 자율 모드 테스트 (FILESYSTEM)**

에디터 모두 꺼진 상태에서 텔레그램으로:
`"자율 시작: 언리얼 프로젝트 정리 - 폴더 구조 분석만"`

Expected:
1. FILESYSTEM 모드 감지 보고
2. 폴더 구조 분석 실행
3. /staging/reports/folder_structure_YYYYMMDD.md 생성
4. 텔레그램으로 완료 보고
5. /logs/에 JSONL 로그 생성

- [ ] **Step 2: 로그 검증**

Run: `cat "E:/02_openclawAgent/logs/"*.jsonl | tail -1 | python -m json.tool`

Expected: 유효한 JSON, status: "success"

- [ ] **Step 3: 명령 모드 테스트**

텔레그램에서: `"Content/Characters 폴더 내 에셋 목록 분석해줘"`

Expected: 분석 결과가 텔레그램으로 회신 + /staging/reports/에 상세 리포트 저장

- [ ] **Step 4: 최종 커밋**

```bash
cd "E:/02_openclawAgent"
git add -A
git commit -m "feat: ClawWorker setup complete - all integration tests passed"
```

---

## 실행 순서 요약

| Task | 내용 | 의존성 | 종일군 개입 |
|------|------|--------|------------|
| 1 | 디렉토리 구조 | 없음 | 없음 |
| 2 | Docker Compose | Task 1 | 없음 |
| 3 | SOUL.md + AGENTS.md | Task 1 | 없음 |
| 4 | MCP 설정 | Task 1 | 검증 결과에 따라 분기 |
| 5 | 태스크 정의 | Task 1 | 없음 |
| 6 | 텔레그램 봇 | Task 2 | **필수** (봇 생성 + API 키) |
| 7 | 최초 실행 + 페어링 | Task 1-6 | **필수** (페어링) |
| 8 | MCP 연결 테스트 | Task 7 | MCP 서버 실행 |
| 9 | 통합 테스트 | Task 7-8 | 텔레그램 명령 |

**병렬 가능:** Task 1 완료 후 Task 2, 3, 4, 5를 병렬 실행 가능. Task 6은 종일군 개입 대기.
