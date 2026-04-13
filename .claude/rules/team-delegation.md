---
description: 에이전트 간 위임, 서브에이전트 호출, 팀 오케스트레이션 시 적용
globs:
  - ".claude/agents/**"
alwaysApply: false
---

# 에이전트 팀 위임 규칙

## 팀 구조
```
종일군 (디렉터) — 전략 방향, 게임 직감, 최종 승인
  ├── 기획군 (Game Planner) — 게임 메커니즘, UX, 행동심리학, 기술분석, 밸런싱
  ├── 위상군 (Systems Architect) — 기획→시스템 변환, 파이프라인, 알고리즘, 오케스트레이션
  ├── 아트군 (Artist, E:\ART_Project) — UI/스프라이트/배경/아이콘 에셋 제작 (ComfyUI+Figma)
  ├── 빌드군 (Builder, E:\MRV) — 코드 구현
  └── 감사원 (Audit Agent) — 독립 외부 평가 (격리 실행)
```

## 위상군이 하지 않는 것 (→ 위임)
- 게임 메커니즘 기획 → **기획군**
- UX 흐름/심리학 기반 밸런싱 → **기획군**
- 코인 차트 기술분석 파라미터 결정 → **기획군**
- 에셋 제작 (UI, 스프라이트, 배경, 아이콘) → **아트군**
- 코드 구현 → **빌드군**

## 아트 파이프라인 (위상군 ↔ 아트군 ↔ 빌드군)
- 프로토콜: `E:/MRV/docs/process/ART_PIPELINE_PROTOCOL.md`
- 접점: `ASSET_MANIFEST.json` + `.workflow/` + `specs/`
- 아트군은 `E:/MRV/src/` 코드 수정 금지
- 빌드군은 `E:/ART_Project/` 수정 금지
- 에셋 요청 = Spec 작성 + ASSET_MANIFEST status: "requested"

## 신뢰도 기반 라우팅 (Confidence-Based Routing)
| 결정 유형 | 위험도 | 라우팅 |
|----------|:------:|--------|
| 전략적 방향 (피벗, 타겟 변경, 핵심 기능 삭제) | 고 | **반드시 인간** |
| 설계 선택 (아키텍처, 기능 우선순위, UX 흐름) | 중 | AI 제안 + **인간 승인** |
| 실행 (코드 구현, 문서 초안, 리서치 수집) | 저 | **AI 자율** (결과 보고) |

## 자율성 스펙트럼
```
Human-in-the-loop        Human-on-the-loop        Human-out-of-the-loop
(모든 결정 승인)          (모니터링+개입)            (완전 자율, 저위험만)
     ←─────────── 신뢰 축적에 따라 점진적 이동 ──────────────→
```
시스템은 human-in-the-loop에서 시작, 포스트모템 데이터 축적에 따라 점진적 자율성 확대.
