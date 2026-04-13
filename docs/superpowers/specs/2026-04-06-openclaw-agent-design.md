# OpenClaw Agent 설계 — ClawWorker (MYSTIC_ISLAND)

> 작성: 위상군 | 날짜: 2026-04-06 | 상태: 설계 승인 대기

## 1. 목적

`D:\MYSTIC_ISLAND` 언리얼 프로젝트를 대상으로 한 자율 정리/파이프라인 에이전트.
종일군이 자리를 비우거나 쉬는 시간에 텔레그램으로 명령을 내리거나, 태스크 목록 기반 자율 실행.

### 태스크 영역

| 영역 | 내용 |
|------|------|
| **언리얼 프로젝트 정리** | 미사용 에셋 스캔/리포트, 폴더 구조 분석, 네이밍 규칙 위반 탐지, 중복 에셋 탐지, 머티리얼/텍스처 레퍼런스 체인 분석 |
| **후디니→언리얼 파이프라인** | HDA 쿡 → FBX/USD 익스포트 → staging 저장, 익스포트 결과 검증 (폴리곤 수, UV, 노멀), 임포트 매니페스트 생성 |

## 2. 아키텍처

```
Host Machine (Windows 11)
├── D:\MYSTIC_ISLAND              ← 언리얼 프로젝트 (ro 마운트)
├── E:\00_unrealAgent              ← 언리얼 MCP 서버 (호스트 실행)
├── E:\01_houdiniAgent             ← 후디니 MCP 서버 (호스트 실행)
└── E:\02_openclawAgent            ← ClawWorker 홈
    ├── docker-compose.yml
    ├── .env
    ├── workspace/
    ├── staging/                   ← 결과물 출력 (rw)
    └── logs/                      ← 실행 로그 (rw)

Docker Container: openclaw-clawworker
├── /workspace     → E:\02_openclawAgent\workspace (rw)
├── /staging       → E:\02_openclawAgent\staging (rw)
├── /logs          → E:\02_openclawAgent\logs (rw)
├── /project       → D:\MYSTIC_ISLAND (ro)
└── MCP Connections (network via host.docker.internal)
    ├── :9100 → 후디니 MCP (streamable-http)
    └── :9200 → 언리얼 MCP (streamable-http)
```

### 핵심 원칙

- `D:\MYSTIC_ISLAND`은 읽기전용(ro) 마운트 — 원본 보호
- 모든 변경/출력은 `/staging`에만 기록
- MCP 서버는 호스트에서 실행, 컨테이너는 `host.docker.internal`로 접근
- 에디터 꺼져 있으면 MCP 연결 실패 → 파일시스템 태스크만 실행

## 3. Docker Compose

```yaml
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
      - OPENCLAW_MODEL_PROVIDER=google
      - OPENCLAW_MODEL=gemini-3.1-flash
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENCLAW_FALLBACK_PROVIDER=openai-compatible
      - OPENCLAW_FALLBACK_MODEL=gemma4-26b
      - OPENCLAW_FALLBACK_BASE_URL=http://host.docker.internal:11434/v1
      - OPENCLAW_FALLBACK_API_KEY=ollama
      - OPENCLAW_SANDBOX=1
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    mem_limit: 4g
```

### .env

```
GOOGLE_API_KEY=<gemini-api-key>
TELEGRAM_BOT_TOKEN=<botfather-token>
```

## 4. MCP 서버 연동

두 MCP 서버 모두 호스트에서 streamable-http 모드로 실행 필요 (Docker 컨테이너에서 stdio 불가).

### 후디니 MCP (fxhoudinimcp v1.0.0)

- 131개 도구 (SOPs, LOPs/USD, DOPs, PDG/TOPs, COPs, HDAs, 렌더링, VEX 등)
- 환경변수: `MCP_TRANSPORT=streamable-http`, `FXHOUDINIMCP_PORT=9100`
- 후디니 에디터와는 HTTP/JSON (port 8100)

### 언리얼 MCP (UnrealClientProtocol)

- 7개 스킬 도메인 (오브젝트, 액터, 에셋, 머티리얼, 블루프린트 등)
- Python 래퍼 → TCP/JSON → FUCPServer
- streamable-http 모드로 port 9200에서 실행

### 설정 파일

```json
// workspace/config/mcpServers.json
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

## 5. 실행 모드

### 사전 점검

매 세션 시작 시 MCP 헬스체크로 가용 모드 결정:

| 모드 | 조건 | 가용 태스크 |
|------|------|------------|
| FULL | 양쪽 MCP 연결 | 전체 (정리 + 파이프라인) |
| HOUDINI_ONLY | 후디니만 연결 | HDA 쿡/익스포트 + 파일시스템 |
| UNREAL_ONLY | 언리얼만 연결 | 에셋 분석/정리 + 파일시스템 |
| FILESYSTEM | 둘 다 꺼짐 | 파일시스템 레벨 태스크만 |

### 사용자 인터랙션

| 모드 | 트리거 | 동작 |
|------|--------|------|
| **명령 모드** | 종일군이 텔레그램으로 직접 지시 | 지시받은 태스크 즉시 실행, 완료 후 보고 |
| **자율 모드** | 종일군이 "자율 시작" + 태스크 목록 전달 | 태스크 목록 순회, 반복 실행, 완료 시 전체 리포트 |

## 6. SOUL.md (에이전트 인격)

```markdown
# ClawWorker — MYSTIC_ISLAND 자율 정리/파이프라인 에이전트

## 정체성
너는 ClawWorker. MYSTIC_ISLAND 프로젝트의 자율 정리/파이프라인 에이전트다.
후디니 MCP와 언리얼 MCP를 사용하여 태스크를 수행한다.

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
1. 후디니 MCP 헬스체크 → 응답 여부 기록
2. 언리얼 MCP 헬스체크 → 응답 여부 기록
3. 가용 모드 결정: FULL / HOUDINI_ONLY / UNREAL_ONLY / FILESYSTEM

### 태스크: 언리얼 프로젝트 정리
- 미사용 에셋 스캔 → 리포트 생성 (/staging/reports/)
- 폴더 구조 분석 → 네이밍 규칙 위반 리포트
- 중복 에셋 탐지 → 리포트
- 머티리얼/텍스처 레퍼런스 체인 분석
- 에디터 ON: AssetRegistry 쿼리로 정확한 의존성 분석
- 에디터 OFF: .uasset 파일 메타데이터 기반 추론

### 태스크: 후디니→언리얼 파이프라인
- HDA 쿡 → FBX/USD 익스포트 → /staging/exports/에 저장
- 익스포트 결과 검증 (폴리곤 수, UV, 노멀 체크)
- 임포트 매니페스트 생성 (JSON)

## 결과물 구조
/staging/
├── reports/          ← 분석 리포트 (마크다운)
├── exports/          ← HDA 쿡 결과물 (FBX/USD)
├── manifests/        ← 임포트 매니페스트 (JSON)
└── session_summary.md ← 이번 세션 요약

## 알림 (텔레그램)
- 태스크 완료 시 요약 전송
- 에러 발생 시 즉시 알림
- 전체 세션 종료 시 최종 리포트

## LLM
- 기본: Gemini 3.1 Flash
- 폴백: 로컬 Gemma4 26B (http://host.docker.internal:11434/v1)
```

## 7. 디렉토리 구조

```
E:\02_openclawAgent\
├── docker-compose.yml
├── .env                              ← API 키 (git 제외)
├── workspace/
│   ├── SOUL.md                       ← 에이전트 인격/규칙
│   ├── config/
│   │   └── mcpServers.json           ← MCP 연동 설정
│   └── tasks/
│       ├── unreal_cleanup.md         ← 언리얼 정리 태스크 정의
│       └── hda_pipeline.md           ← 후디니→언리얼 파이프라인 정의
├── staging/
│   ├── reports/
│   ├── exports/
│   └── manifests/
└── logs/
```

## 8. 보안

| 레이어 | 조치 |
|--------|------|
| Docker 격리 | 4개 볼륨만 마운트, MYSTIC_ISLAND는 ro, OPENCLAW_SANDBOX=1 |
| 네트워크 | MCP 포트(9100, 9200) + Ollama(11434)만 호스트 접근, 외부 인바운드 없음 |
| 텔레그램 인증 | 페어링된 종일군 계정만 명령 수신 |
| LLM API 키 | .env 파일 분리, 환경변수로만 주입 |
| 메모리 제한 | mem_limit: 4g |
| 쓰기 제한 | staging, logs, workspace만 쓰기 가능 |
| 자율 도구 | 웹 검색/pip install 허용, 새 MCP 서버 설치 금지 |

## 9. 에러 처리

```
태스크 실행
├── 성공 → /staging에 저장 → 텔레그램 보고
├── MCP 연결 실패 → 해당 도메인 스킵 → 텔레그램 알림
├── LLM 메인 실패 → Gemma4 폴백 자동 전환 → 계속 실행
├── LLM 양쪽 실패 → 세션 중단 → 텔레그램 긴급 알림
└── 태스크 3회 연속 실패 → 해당 태스크 스킵 → 다음 태스크로
```

## 10. 로그 포맷

```json
// logs/YYYY-MM-DD_sessionN.jsonl
{
  "timestamp": "2026-04-06T14:31:15Z",
  "task": "unreal_unused_asset_scan",
  "mode": "FILESYSTEM",
  "status": "success",
  "duration_sec": 45,
  "output": "/staging/reports/unused_assets_20260406.md",
  "llm_used": "gemini-3.1-flash"
}
```

## 11. 텔레그램 연동

1. @BotFather에서 봇 생성 → 토큰 → .env에 저장
2. 컨테이너 시작 → Control UI (http://localhost:18789) 접속
3. 텔레그램 봇에 /start → 페어링 코드 입력 → 인증 완료
4. 종일군 계정만 명령 가능

### 명령 예시

| 메시지 | 동작 |
|--------|------|
| "Content 폴더 미사용 에셋 분석해" | 명령 모드: 즉시 분석 → 리포트 → 회신 |
| "이 HDA 쿡해서 staging에 넣어" | 명령 모드: HDA 쿡 → 익스포트 → 회신 |
| "자율 시작: 전체 정리 태스크" | 자율 모드: 태스크 목록 순차 실행 → 최종 리포트 |

## 12. MCP 서버 실행 (호스트 측 사전 준비)

컨테이너 시작 전, 호스트에서 두 MCP 서버를 streamable-http 모드로 실행:

```bash
# 후디니 MCP (port 9100)
cd E:\01_houdiniAgent\fxhoudinimcp_repo
MCP_TRANSPORT=streamable-http FXHOUDINIMCP_PORT=9100 python -m fxhoudinimcp

# 언리얼 MCP (port 9200) — UCP Python 래퍼를 streamable-http로
cd E:\00_unrealAgent
# UCP 서버 실행 방법은 UnrealClientProtocol 문서 참조
```
