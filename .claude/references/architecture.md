---
description: 시스템 아키텍처 설계, 나선형 파이프라인, Claude Code 확장 설계 시 적용
globs:
  - "docs/decisions/**"
  - "docs/planning/**"
  - "spiral/**"
  - ".claude/agents/**"
  - ".claude/skills/**"
---

# 시스템 아키텍처 & 나선형 설계

## 프로덕트 나선 설계학 (Product Spiral Design)
프로젝트의 가치 실현을 위한 반복적 개발 루프를 설계할 때, 다음 5개 프레임워크의 위상적 동형(isomorphism)을 활용하십시오.

*   **Spiral Model (Boehm):** 매 반복마다 4사분면(계획→리스크분석→구현→평가)을 순환. **리스크 분석이 매 사이클마다 재실행**되는 것이 핵심 — 한 번에 전체를 설계하지 않음. 나선의 반경 = 누적 비용, 각도 = 진행 단계.
*   **Lean Startup (Build-Measure-Learn):** MVP로 가설 검증 → 측정 → 학습 → 피벗/지속 결정. **검증된 학습(Validated Learning)**이 진보의 척도. 사이클 시간 단축이 경쟁 우위.
*   **OODA Loop (Boyd):** Observe(관찰)→Orient(판단)→Decide(결정)→Act(실행). **Orient가 가장 중요** — 편향, 멘탈 모델, 과거 경험이 수렴하는 곳. AI는 Observe/Act를 가속, 인간은 Orient/Decide를 소유.
*   **Double Diamond:** 발산→수렴을 2회 반복 (문제 공간 + 해결 공간). **AI는 발산(Diverge)의 증폭기, 인간은 수렴(Converge)의 결정자.** 다이아몬드 사이의 전환점(명확한 문제 정의)이 가장 중요한 산출물.
*   **Design Thinking:** Empathize→Define→Ideate→Prototype→Test. 각 단계에서 AI 에이전트 역할 매핑: 공감(리서치)→정의(인간)→발상(AI 발산)→프로토타입(AI 구현)→테스트(AI 실행+인간 해석).

**위상적 통합 원리:** 이 5개 프레임워크는 모두 **"탐색→수렴→실행→학습→재탐색" 나선**의 변주(variation)다. 시스템 설계 시 각 단계에서 "인간이 수렴/결정하는 곳"과 "AI가 발산/실행하는 곳"을 명확히 구분하십시오.

## Claude Code 확장 아키텍처 (Extension Architecture)

### 확장 메커니즘
| 메커니즘 | 용도 | 핵심 속성 |
|---------|------|----------|
| **Subagents** (`.claude/agents/*.md`) | 전문화된 에이전트 정의 | model, tools, permissions, memory, isolation(worktree) 지정 가능. 병렬 background 실행 가능 |
| **Skills** (`.claude/skills/*.md`) | 커스텀 /슬래시커맨드 | `context:fork`로 격리 실행, `agent:` 필드로 subagent 타입 지정, `!command` 동적 컨텍스트 |
| **Hooks** (settings.json) | 자동화 트리거 | 22종 이벤트. UserPromptSubmit(컨텍스트 주입), PostToolUse(자동 검증), Stop(세션 종료 처리) |
| **Agent Teams** (실험적) | 팀 기반 병렬 협업 | 리드+팀원, P2P 메시징, 공유 태스크 리스트. 팀원 간 직접 통신 가능 |
| **MCP** | 외부 도구 연결 | 에이전트별 mcpServers 스코핑 가능. 상태 관리는 불가(도구 제공만) |

### 하드 제약 (Hard Constraints)
*   서브에이전트는 다른 서브에이전트를 실행할 수 **없음** (1단계 깊이만)
*   결정론적 "A완료→B시작" 파이프라인은 Claude의 자율 판단에 의존 (외부 상태 파일로 보완 가능)
*   서브에이전트 간 직접 통신 불가 (메인 세션 경유만. Agent Teams에서는 P2P 가능)
*   백그라운드 서브에이전트 완료 이벤트 콜백 없음
*   Agent Teams 세션 재개(`/resume`) 불가
*   Skills가 다른 Skills를 직접 호출 불가

### 설계 패턴
*   **메인 세션 = 오케스트레이터**: 메인 Claude가 CM 역할, subagent를 순차/병렬 호출하여 결과 수합
*   **Skills + context:fork**: 복잡한 워크플로우를 /커맨드로 캡슐화, 격리 실행
*   **Subagent에 skills 프리로딩**: `skills:` 필드로 도메인 지식을 에이전트에 주입
*   **공유 파일 시스템 상태**: 서브에이전트 간 조율은 마크다운/YAML 파일을 통한 비동기 상태 공유
*   **Hooks 기반 자동 QG**: PostToolUse/Stop hooks로 결과물 자동 검증
