# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-13 Session 29

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **메타 프로젝트:** Atlas /atlas 명령체계 구현 완료 (7/7 Tasks, 88 tests)
- **TEMS 독립 패키지:** **v0.1.0 구현 완료** (11/11 Tasks, 35 tests) + 위상군 마이그레이션 완료
- **Atlas GitHub:** bobpullie/atlas push 완료
- **ANKR 토큰 효율화:** Phase 1 (디니군 진행 중)

## 이번 세션 성과 (Session 29)
- **TEMS 마이그레이션 완료:** 8 에이전트 import 전환 (tems_core → tems), 잔류 0건
- **GitHub push:** bobpullie/TEMS (48586cc), bobpullie/DnT-WesangGoon (6eb1202)
- **미니PC 가이드:** docs/migration/ubuntu-server-migration.md
- **독립 위상군 Spec+Plan 완료:** wesanggoon-indie, 11 Tasks, 28 규칙 이식 예정

## 다음 세션 부트 (S30 — 독립 위상군 구현)
```
목표: E:\WesangGoon 독립 위상군 11 Tasks 구현
Plan: docs/superpowers/plans/2026-04-13-independent-wesanggoon.md
작업 디렉토리: E:\WesangGoon (신규, 미생성)
실행 방식: Subagent-Driven Development
소스:
  - DnT 스킬: E:/DnT/DnT_WesangGoon/.claude/skills/
  - DnT TEMS DB: E:/DnT/DnT_WesangGoon/memory/error_logs.db (28개 추출)
HEAD (DnT-WesangGoon): 6eb1202
HEAD (TEMS): 48586cc
```

## 대기 태스크 (우선순위)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| **TEMS-패키지커밋** | 위상군 | bobpullie/TEMS tems_commit.py 업데이트분 커밋 | **P0** |
| **Atlas-피드백** | 종일군 | 기록군 L2 키워드 보강 후 hint 품질 재테스트 | P0 |
| **ANKR-Phase1** | 디니군 | extract_and_dump + 하드코딩 제거 (진행 중) | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| **TEMS-마이그레이션** | 위상군 | 나머지 에이전트 import 전환 (기록군→디니군→빌드군→관리군→어플군) | P1 |
| **TEMS-DOC** | 위상군 | tems-rebuild-howto.md 작성 | P1 |
| **KH-Phase2** | 위상군 | Phase 2 brainstorming | P1 |
| **CUDA-리랭커** | 가우스군 | qmd query CUDA 리랭커 크래시 확인 | P1 |
| **Atlas-minor** | 위상군 | rglob 성능 + .hdocs repair 테스트 보강 | P2 |
| **session_end hook 하드코딩** | 위상군 | session_end_check.py.tmpl 머신경로 제거 | P2 |
| **legacy tems/ 정리** | 위상군 | 코드군/리얼군/디니군/어플군의 tems/*.db 정리 | P2 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **Atlas → bobpullie/atlas push** | 미니PC 위상군 배포용 (git clone + pip install -e .) | 4/13 S28 |
| **tems_commit.py → MemoryDB API 전환** | 직접 sqlite3는 FTS5 트리거 우회 위험 | 4/13 S27 |
| **TEMS PyPI+Skill 듀얼 배포** | atlas-docs[tems] optional dep + 스킬 등록 | 4/13 S26 |
| **TEMS 점진 전환** | 12 에이전트 중 위상군 먼저 verified | 4/13 S27 |

## 팀 현황
| 에이전트 | 위치 | TEMS 상태 | 현재 태스크 |
|---------|------|-----------|------------|
| 위상군 | E:\DnT\DnT_WesangGoon | **마이그레이션 완료** | S28 완료 |
| 기록군 | E:\KnowledgeHub | 구버전 (tems_core) | L2 키워드 보강 대기 |
| 디니군 | E:\01_houdiniAgent | 구버전 (tems_core) | ANKR Phase 1 |
| 빌드군 | E:\DnT\MRV_DnT | 구버전 (tems_core) | 대기 (Q-002) |
| 아트군 | E:\DnT\DnT_ArtGoon | 구버전 (tems_core) | HO-011 대기 |
| 포폴군 | E:\KJI_Portfolio | 구버전 (tems_core) | 온보딩 완료 |
| 코드군 | E:\QuantProject\DnT_Fermion | 구버전 (tems_core) | 마이그레이션 완료 |
| 관리군 | E:\TCAS_BUILDER | 구버전 (tems_core) | TEMS 초기화 완료 |
| 어플군 | E:\ChildSchedule | 구버전 (tems_core) | scaffold 완료 |

## Atlas 구현 + TEMS 로드맵
| 세션 | 내용 | 상태 | 산출물 |
|------|------|------|------|
| S22 | Atlas 피드백 패치 | ✅ | 3-section + hint → 69 tests |
| S23 | src-layout + CLI | ✅ | 표준 패키지 + 73 tests |
| S24 | /atlas 명령체계 설계 | ✅ | spec + plan |
| S25 | /atlas 7-Task 구현 | ✅ | scan + repair + hook → 88 tests |
| S26 | TEMS 독립 패키지 설계 | ✅ | spec + plan (코드변경 없음) |
| S27 | TEMS 패키지 구현 + 위상군 마이그레이션 | ✅ | v0.1.0, 35 tests, 마이그레이션 완료 |
| **S28** | **Atlas GitHub push** | **✅** | **bobpullie/atlas remote push** |
| S29 | P0 태스크 또는 에이전트 마이그레이션 | 대기 | — |
