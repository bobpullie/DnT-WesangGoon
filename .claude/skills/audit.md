---
name: audit
description: 독립 외부 감사 에이전트를 실행하여 프로젝트 산출물을 냉정하게 평가합니다.
user_invocable: true
context: fork
---

# /audit — Independent External Audit

## Usage
```
/audit [project_path] [stage]
```

**Examples:**
- `/audit E:\MRV design` — MRV 프로젝트 DESIGN 단계 감사
- `/audit E:\MRV build` — MRV 프로젝트 BUILD 단계 감사
- `/audit` — 기본값: E:\MRV, 현재 단계 자동 감지

## Execution Steps

### 1. Parse Arguments
- `project_path`: 감사 대상 프로젝트 경로 (기본: E:\MRV)
- `stage`: 감사 단계 — analyze, plan, design, build, test (기본: 자동 감지)

### 2. Detect Current Stage
프로젝트의 `spiral/state.yaml`을 읽어 현재 단계를 파악합니다.

### 3. Prepare Audit Directories
감사 에이전트에 전달할 `--add-dir` 디렉토리를 결정합니다:

| Stage | Directories |
|-------|------------|
| analyze | `docs/`, `spiral/` |
| plan | `docs/`, `spiral/`, `MODULE.md` |
| design | `docs/`, `src/packages/shared/`, `MODULE.md`, 각 모듈의 `MODULE.md` |
| build | `src/`, `docs/`, `MODULE.md` |
| test | `src/`, `docs/`, `spiral/` |

### 4. Create Temp Execution Directory
```bash
AUDIT_DIR=$(mktemp -d /tmp/audit_XXXXXXXXXX)
cd "$AUDIT_DIR" && git init
```

### 5. Build Audit Prompt
`E:\AgentInterface\.claude\audit\audit_prompt_template.md`를 읽고 변수를 치환합니다:
- `{PROJECT_NAME}`: 프로젝트명 (예: "DnT v3")
- `{STAGE}`: 감사 단계
- `{BRIEF_DESCRIPTION}`: 프로젝트 설명 (MODULE.md 또는 CLAUDE.md에서 추출)
- `{REPORT_PATH}`: 보고서 저장 경로 (`{project_path}/spiral/audit/YYYY-MM-DD_{stage}.md`)
- `{FOCUS_AREAS}`: 단계별 중점 평가 영역

### 6. Execute Isolated Audit Agent
```bash
# System prompt 파일 읽기
SYSTEM_PROMPT=$(cat "E:/AgentInterface/.claude/audit/system_prompt.md")

# 감사 프롬프트 파일 읽기
AUDIT_PROMPT=$(cat "$AUDIT_DIR/audit_prompt.md")

# 격리된 외부 디렉토리에서 실행
cd "$AUDIT_DIR"
claude -p \
  --system-prompt "$SYSTEM_PROMPT" \
  --add-dir "{add_dir_1}" \
  --add-dir "{add_dir_2}" \
  --allowedTools "Read,Glob,Grep,Write,Bash(ls:*),Bash(wc:*)" \
  "$AUDIT_PROMPT"
```

### 7. Collect Results
- 보고서가 `{project_path}/spiral/audit/` 에 저장되었는지 확인
- 보고서 Executive Summary를 사용자에게 표시
- temp 디렉토리 정리: `rm -rf "$AUDIT_DIR"`

### 8. Post-Audit
사용자에게 보고서 경로와 Executive Summary를 전달합니다.
감사 결과에 대한 논의는 위상군(메인 세션)에서 진행합니다.

## Important Notes
- 감사 에이전트는 프로젝트의 CLAUDE.md, TEMS, 핸드오버 문서에 접근할 수 없습니다
- 매 실행마다 완전히 새로운 인스턴스입니다 (이전 감사 결과를 기억하지 않음)
- `--system-prompt`로 Claude Code 기본 시스템 프롬프트를 경량화하여 토큰 절감
- 외부 temp 디렉토리에서 실행하여 Project CLAUDE.md 차단
