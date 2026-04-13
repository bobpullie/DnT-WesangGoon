# TPB 아키텍처 점검 보고서
## 현빌드 상태 + 구조적 진단 + 개선안

**작성일**: 2026-03-25
**작성자**: 위상군 (위상적 시스템 아키텍트)
**대상**: TPB v2.0 (TTMS 프로젝트, `E:\TriadChord\TTMS\`)
**방법론**: 설계 블루프린트 vs 실제 구현 비교 분석 (Topological Gap Analysis)

---

## I. 현빌드 상태 요약

### 전체 건강도

| 영역 | 상태 | 완성도 | 비고 |
|------|:----:|:------:|------|
| CAR Build Engine | ✅ | 90% | 핵심 파이프라인 작동, 다만 engine.py 비대화 심각 |
| 노드그래프 시각화 | ✅ | 85% | 커스텀 QGraphicsItem 기반, DAG 실행+렌더링 완성 |
| Quality Gate | ✅ | 90% | cm/user/cm+user 라우팅, 피드백 루프 완성 |
| 대시보드 UI | ✅ | 85% | VS Code 레이아웃, Activity Bar, 멤버 카드 |
| 회의실 (Meeting) | ✅ | 80% | PRECISE/ECONOMY 모드, 다중 참가자 |
| Plan Engine | ⚠️ | 40% | 백엔드 골격만 존재, UI 미연결, Blueprint 미구현 |
| PRISM/IRIS | ⚠️ | 50% | 체크리스트+필드지식 완성, 메타규칙/진화 미구현 |
| TEMS 진화계층 | ⚠️ | 25% | FTS5 BM25만 작동, Phase 2~4 선언만 |
| 워크스페이스 관리 | ✅ | 85% | ADR-002 Phase 1~2 완료 (54% 토큰 절감) |
| DB 스키마 | ✅ | 90% | v13까지 마이그레이션, chat/meeting 테이블 존재 |

### 정량 지표

- **코드베이스**: ~82 모듈, ~15K 라인
- **에이전트**: 7+1 (Build 4 + Plan 3 + CM)
- **UI 페이지**: 10개 (블루프린트 목표: 4개)
- **DB 테이블**: v13 스키마
- **최대 단일 파일**: engine.py ~14K 라인

---

## II. 구조적 모순 (Structural Contradictions)

### 모순 1: 블루프린트 "4페이지 통합" vs 현실 "10페이지 분산"

**블루프린트 설계**:
```
Dashboard → 개발실(DevRoom) → Timeline → Settings
(Command, Pipeline, Broadcast → DevRoom으로 통합)
```

**현실 구현**:
```
Dashboard, DevRoom, Pipeline, Timeline, Settings,
CAR Insights, Project, Persona, Trigger, Broadcast — 10개
```

**진단**: 블루프린트의 핵심 아이디어는 "대화+파이프라인을 한 화면에서 보는 개발실"인데, 실제로는 Pipeline이 별도 페이지로 남아있고, DevRoom이 아직 통합 허브로 기능하지 못함. CAR Insights, Persona, Trigger 등은 Settings 하위로 들어갈 수 있는 수준의 기능인데 독립 페이지로 분리되어 네비게이션 복잡도를 높이고 있음.

**심각도**: ★★★☆☆ (UX 비효율이지 기능적 결함은 아님)

---

### 모순 2: "노드그래프 = Source of Truth" vs 실제 engine.py가 실행 주도

**블루프린트 설계**:
```
노드그래프(JSON) → engine.py가 읽어서 실행
```

**현실 구현**:
```
engine.py가 내부 로직으로 파이프라인 생성 → 노드그래프는 시각화용
```

**진단**: pipeline_engine.py에 DAG 구조가 있고 topological sort도 구현되어 있지만, 실제 실행 흐름은 engine.py의 거대한 절차적 로직이 주도함. 노드그래프 JSON은 `orchestration/runs/` 에 저장되지만 "읽어서 실행"하는 구조가 아니라 "실행하면서 생성"하는 구조.

이는 **설계 방향과 구현 방향이 반대**라는 의미. 블루프린트가 "선언적(Declarative) 파이프라인"을 목표로 하는데, 현실은 "명령적(Imperative) 실행"에 머물러 있음.

**심각도**: ★★★★☆ (아키텍처 핵심 모순 — v2.0의 동적 Phase-Gate 구현을 위해 반드시 해결 필요)

---

### 모순 3: Plan Engine — 설계는 "대화형 멀티턴" vs 현실은 "원샷 분석"

**블루프린트 설계**:
```
PlanSession → 멀티턴 대화 → CM이 전문가 자동 소환 → Blueprint 점진적 발전 → Build 전달
```

**현실 구현**:
```
plan_engine.py → 목표 분석 → 멤버 선정 → 회의실 생성 (끝)
- Blueprint 데이터 모델 없음
- PlanSession 상태 머신 없음 (exploring → converging → finalized)
- 전문가 자동 소환 없음 (수동 선택)
```

**진단**: Plan Engine의 "뼈"는 있지만 "근육"이 없는 상태. 회의실은 작동하지만, Plan→Blueprint→Build로 이어지는 **워크플로우 체인**이 끊겨 있음. 이것이 TPB의 가장 큰 차별화 포인트("뭘 만들어야 하는지 함께 고민")인데, 현재는 Build만 작동하는 상태.

**심각도**: ★★★★★ (제품 정체성 관련 — TPB의 존재 이유)

---

### 모순 4: 이중 메모리 시스템의 역할 충돌

**현재 상태**:
```
1. ttms/car/memory.py     — CAR 엔진 내부 메모리 (BM25, scope 기반, 태스크 결과 저장)
2. ttms/tems/fts5_memory.py — TEMS 메모리 (TCL/TGL, 위상적 규칙)
```

**진단**: 두 시스템 모두 FTS5+BM25를 사용하지만 **DB가 다르고, 스키마가 다르고, 검색 인터페이스가 다름**.

- `car/memory.py`: `agent_memory` 테이블 (ttms.db), scope 기반
- `tems/fts5_memory.py`: `memory_logs` 테이블 (error_logs.db), category 기반

에이전트가 학습한 교훈(memory.py)과 시스템이 축적한 규칙(tems)이 서로 검색되지 않음. PRISM/IRIS가 두 시스템을 관통하는 "거버넌스 레이어"여야 하는데, 실제로는 각각 독립적으로 동작.

**심각도**: ★★★★☆ (장기적으로 지식이 분산되어 학습 효과 반감)

---

## III. 비합리적 설계 (Irrational Design Decisions)

### 비합리 1: engine.py — 14K 라인 God Object

하나의 파일이 다음을 모두 담당:
- Triage 호출
- Work Plan 생성
- Task 분배
- 에이전트 실행
- Artifact 추출
- Quality Gate 호출
- Phase-Gate 관리
- 토큰 관리
- 프로토콜 로딩
- 리뷰 라우팅

**왜 비합리적인가**: 이 파일을 수정하면 모든 것에 영향. 빌드군이 새 기능을 추가할 때마다 이 14K 라인 파일을 컨텍스트에 넣어야 함 → Claude API 토큰 낭비가 엄청남. 또한 단일 파일에서의 변경이 예측 불가능한 사이드 이펙트를 만들 수 있음.

**적정 구조**: 5~8개의 모듈로 분해 가능 (아래 개선안 참조)

---

### 비합리 2: TEMS __init__.py에 선언된 미구현 클래스들

```python
# ttms/tems/__init__.py에서 export하는 클래스들:
HybridRetriever, HealthScorer, AnomalyCertifier, MetaRuleEngine
# → 실제 구현: 없음
```

**왜 비합리적인가**: import 시 에러가 나지 않도록 처리되어 있겠지만, 코드베이스에 "있는 척 하는" 인터페이스가 존재하면 다른 에이전트가 "이건 이미 구현되어 있다"고 착각하고 호출을 시도할 수 있음. 미구현 코드는 stub이나 TODO가 아니라 아예 없어야 깨끗함.

---

### 비합리 3: Meeting 모드의 조기 최적화 (PRECISE/ECONOMY)

**현재**: 회의 시작 전에 PRECISE(개별 API 호출) vs ECONOMY(배치 호출) 모드를 선택해야 함.

**왜 비합리적인가**:
- 프로젝트 초기에 토큰 경제성은 중요하지만, 사용자가 회의 시작 전에 "이 회의의 품질 수준"을 예측해야 하는 것은 부자연스러움
- 회의 품질이 토큰 비용에 의해 제약받는 구조는 UX 관점에서 비합리적
- 적응형으로 전환 가능: 첫 라운드는 PRECISE, 대화가 길어지면 자동으로 ECONOMY로 전환하는 하이브리드가 더 합리적

---

## IV. 비효율적 구조 (Inefficiencies)

### 비효율 1: 에이전트 실행이 아직 `claude -p` (CLI 원샷)

**블루프린트**: Messages API 멀티턴
**현실**: `agent/executor.py` → `cli_chat.py` → `claude -p` (subprocess)

**토큰 낭비**: 매 호출마다 전체 시스템 프롬프트 + persona + field_knowledge를 처음부터 다시 전송. 멀티턴이면 한 번 전송하고 대화를 이어갈 수 있음.

**추정 절감**: 반복적인 컨텍스트 재전송만 줄여도 태스크당 30~50% 토큰 절감 가능

---

### 비효율 2: 10개 페이지의 네비게이션 과잉

사용자(종일군)의 일반적 워크플로우:
```
Dashboard(확인) → DevRoom(작업) → Pipeline(모니터링) → 가끔 Settings
```

나머지 6개 페이지(CAR, Project, Persona, Trigger, Broadcast, Timeline)는 사용 빈도가 낮거나 다른 페이지의 하위 기능으로 충분. 이들이 1차 네비게이션에 있으면 종일군이 "어디로 가야 하지?"라는 인지 부하를 겪게 됨.

---

### 비효율 3: field_knowledge 27개 파일의 로딩 전략 부재

`field_knowledge/` 에 27개의 도메인 지식 파일이 있지만, 에이전트에게 어떤 파일을 언제 로딩하는지의 전략이 명확하지 않음. 모두 로딩하면 토큰 폭발, 선택적 로딩이면 매칭 로직 필요 — 현재 이 부분이 모호한 상태.

---

## V. 위상적 구조 분석 (Topological Analysis)

### 모듈 의존성 그래프의 핵심 문제

```
현재 의존성 위상:

         engine.py (God Object)
        ╱    │    ╲      ╲
  triage  work_plan  distributor  quality_gate
      │               │
  plan_engine      meeting
      │
  chat_session

문제: engine.py가 모든 것의 허브(Hub) — 단일 장애점(Single Point of Failure)
     engine.py를 거치지 않고는 아무것도 실행할 수 없음
```

### 이상적 위상:

```
         orchestrator.py (경량 라우터)
        ╱         │         ╲
  PlanFlow    BuildFlow    ReviewFlow
     │            │            │
  plan_engine  phase_runner  quality_gate
     │            │
  meeting    task_executor
```

**핵심 차이**: 단일 허브 → 3개의 독립적 Flow로 분리. 각 Flow는 자체적으로 완결되며, orchestrator는 Flow 간 전환만 담당.

---

## VI. 개선안 (Improvement Proposals)

### 🔴 P0 — 긴급 (다음 1~2 세션)

#### P0-1: engine.py 분해 계획 수립

14K 라인을 한 번에 리팩토링하는 것은 위험. **점진적 분해 전략**:

```
engine.py (14K) →
├── orchestrator.py      (라우팅 + Flow 전환, ~500줄)
├── build_flow.py        (Triage → Plan → Execute → QG, ~3K줄)
├── phase_runner.py      (Phase-Gate 실행 루프, ~2K줄)
├── task_executor.py     (에이전트 호출 + artifact 추출, ~3K줄)
├── token_manager.py     (토큰 예산 관리, ~1K줄)
└── protocol_loader.py   (시스템 프롬프트 + persona 조합, ~1K줄)
```

**접근법**: Strangler Fig Pattern — 새 모듈을 하나씩 추출하고, engine.py에서 해당 부분을 새 모듈 호출로 교체. 기존 동작 깨지지 않음.

#### P0-2: 미구현 TEMS 클래스 정리

`__init__.py`에서 미구현 클래스 export를 제거하거나 `NotImplementedError`를 명시적으로 선언. 다른 에이전트의 혼동 방지.

---

### 🟡 P1 — 중요 (다음 3~5 세션)

#### P1-1: Plan Engine 실질화 — Blueprint 워크플로우 완성

현재 Plan Engine의 "뼈에 근육 붙이기":

```
Step 1: PlanSession 상태 머신 구현
        exploring → converging → finalized

Step 2: Blueprint 데이터 모델 + 저장
        YAML/JSON으로 persist → DB에 blueprint 테이블

Step 3: DevRoom UI에서 Plan 모드 진입
        "게임 만들고 싶어" → CM이 Plan 모드 감지 → 전문가 소환 제안

Step 4: Blueprint → Build 전환
        finalized Blueprint를 Build Engine에 전달 → Triage가 Blueprint 기반으로 더 정확한 분해
```

이것이 TPB의 **핵심 차별화**. Build만 있으면 CrewAI/AutoGen과 차이가 없음.

#### P1-2: 메모리 통합 아키텍처

```
현재: car/memory.py (ttms.db)  ←×→  tems/fts5_memory.py (error_logs.db)

목표: 단일 검색 인터페이스

  UnifiedMemory
  ├── search(query) → car_memory 결과 + tems 결과를 RRF로 결합
  ├── commit_lesson(source, content) → 적절한 DB에 자동 라우팅
  └── get_relevant_rules(context) → TCL/TGL + agent lessons 통합 반환
```

물리적 DB는 분리 유지해도 되지만, **검색 인터페이스는 하나**여야 함.

#### P1-3: 노드그래프 Source of Truth 전환 (점진적)

```
현재: engine.py 로직 → 노드그래프 생성 (시각화용)
목표: 노드그래프(JSON) → engine이 읽어서 실행

전환 전략:
Phase A: 노드그래프 JSON 스키마 표준화 (이미 pipeline_engine.py에 기반 있음)
Phase B: engine.py가 노드그래프 JSON을 "도 읽을 수 있도록" 입력 경로 추가
Phase C: UI에서 노드를 드래그해 재배치 → JSON 업데이트 → 재실행
Phase D: engine.py의 자체 파이프라인 생성 로직을 노드그래프 JSON 생성으로 교체
```

---

### 🟢 P2 — 개선 (여유가 있을 때)

#### P2-1: 페이지 통합 (10개 → 5개)

```
유지:  Dashboard, DevRoom, Timeline, Settings
통합:  Pipeline → DevRoom 우측 패널 (블루프린트 원안대로)
흡수:  CAR Insights → Dashboard 하위 탭
       Persona → Settings 하위 탭
       Trigger → Settings 하위 탭
       Broadcast → DevRoom 채널 타입
       Project → Dashboard 또는 Settings
```

#### P2-2: Messages API 전환 (claude -p → API 직접 호출)

에이전트 실행을 subprocess `claude -p`에서 Anthropic Messages API 직접 호출로 전환.

**이점**:
- 멀티턴 대화 가능 (컨텍스트 재전송 절감)
- 스트리밍 응답 (실시간 진행 표시)
- 에러 핸들링 정교화
- 토큰 사용량 정확한 추적

**주의**: `claude -p`는 Claude Code의 tool use, MCP 등을 자동 포함하므로, API 직접 호출 시 이 기능들을 수동으로 구성해야 함. 트레이드오프 평가 필요.

#### P2-3: Meeting 모드 적응형 전환

```
현재: 시작 전 PRECISE/ECONOMY 선택 (수동)
개선: 자동 적응

meeting_turn():
  if total_tokens < budget_80%:
    mode = PRECISE
  else:
    mode = ECONOMY
    notify_user("토큰 예산 80% 도달 — 경제 모드로 전환합니다")
```

#### P2-4: field_knowledge 선택적 로딩

```python
# 에이전트 역할 + 현재 태스크 키워드 기반으로 관련 파일만 로딩
def select_knowledge(agent_role: str, task_keywords: list[str]) -> list[str]:
    # BM25 or 키워드 매칭으로 27개 중 상위 3~5개만 선택
    ...
```

---

## VII. 우선순위 로드맵 요약

```
┌──────────────────────────────────────────────────────┐
│  P0 (긴급)                                           │
│  ├─ engine.py 분해 계획 수립 + 첫 모듈 추출          │
│  └─ TEMS 미구현 export 정리                          │
├──────────────────────────────────────────────────────┤
│  P1 (중요)                                           │
│  ├─ Plan Engine 실질화 (PlanSession + Blueprint)     │
│  ├─ 메모리 통합 검색 인터페이스                       │
│  └─ 노드그래프 Source of Truth 전환 시작              │
├──────────────────────────────────────────────────────┤
│  P2 (개선)                                           │
│  ├─ 페이지 통합 (10→5)                               │
│  ├─ Messages API 전환                                │
│  ├─ Meeting 적응형 모드                              │
│  └─ field_knowledge 선택적 로딩                      │
└──────────────────────────────────────────────────────┘
```

---

## VIII. 종합 평가

TPB는 **비전이 올바르고 기반이 탄탄한** 프로젝트입니다. "1인 CEO가 AI 팀과 기획부터 제작까지"라는 비전은 시장에 없는 것이며, Build Engine + 노드그래프 + Quality Gate + PRISM 등 핵심 인프라가 이미 작동하고 있습니다.

하지만 현재 **두 가지 구조적 위험**이 존재합니다:

1. **engine.py God Object**: 프로젝트가 커질수록 수정 비용이 기하급수적으로 증가. 지금 분해하지 않으면 나중에는 전면 재작성이 필요해질 수 있음.

2. **Plan Engine 미완성**: TPB의 결정적 차별화("뭘 만들어야 하는지 함께 고민")가 아직 작동하지 않음. Build만으로는 기존 AI 코딩 도구와의 차별성이 약함.

이 두 가지를 해결하면 TPB는 **진짜 다른 무언가**가 됩니다.

---

*작성: 위상군 | 2026-03-25 | TPB Architecture Review*
