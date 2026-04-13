# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-13 Session 27

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **메타 프로젝트:** Atlas /atlas 명령체계 구현 완료 (7/7 Tasks, 88 tests)
- **TEMS 독립 패키지:** **v0.1.0 구현 완료** (11/11 Tasks, 35 tests) + 위상군 마이그레이션 완료
- **ANKR 토큰 효율화:** Phase 1 (디니군 진행 중)

## 이번 세션 성과 (Session 27)
- **TEMS 패키지 구현:** `E:/bobpullie/TEMS` v0.1.0, 10 commits, 35 tests
- **위상군 마이그레이션:** preflight_hook.py + tems_commit.py → `from tems.` API 전환
- **env var 설정:** `TEMS_REGISTRY_PATH` in settings.local.json
- **검증:** preflight + commit + search cycle 전부 정상 동작 확인

## 다음 세션 부트 (S28)
```
목표: 나머지 에이전트 마이그레이션 또는 P0 태스크
작업 디렉토리: E:/DnT/DnT_WesangGoon + E:/bobpullie/TEMS
HEAD (TEMS): 98a5e01 (v0.1.0) — tems_commit.py 업데이트분 미커밋
HEAD (위상군): docs만 변경 (S26)
Tests (TEMS): 35 passed
pip: tems 0.1.0 editable installed
미커밋: bobpullie/TEMS의 tems_commit.py 템플릿 업데이트 (MemoryDB API 전환분)
```

## 대기 태스크 (우선순위)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| **TEMS-패키지커밋** | 위상군 | bobpullie/TEMS tems_commit.py 업데이트분 커밋 | **P0** |
| **Atlas-피드백** | 종일군 | 기록군 L2 키워드 보강 후 hint 품질 재테스트 | P0 |
| **ANKR-Phase1** | 디니군 | extract_and_dump + 하드코딩 제거 (진행 중) | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| **TEMS-마이그레이션** | 위상군 | 나머지 에이전트 import 전환 (기록군→디니군→빌드군→관리군→어플군) | P1 |
| **TEMS-GitHub** | 위상군 | bobpullie/TEMS remote 연결 + push | P1 |
| **TEMS-DOC** | 위상군 | tems-rebuild-howto.md 작성 | P1 |
| **KH-Phase2** | 위상군 | Phase 2 brainstorming | P1 |
| **CUDA-리랭커** | 가우스군 | qmd query CUDA 리랭커 크래시 확인 | P1 |
| **Atlas-minor** | 위상군 | rglob 성능 + .hdocs repair 테스트 보강 | P2 |
| **session_end hook 하드코딩** | 위상군 | session_end_check.py.tmpl 머신경로 제거 | P2 |
| **legacy tems/ 정리** | 위상군 | 코드군/리얼군/디니군/어플군의 tems/*.db 정리 | P2 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **tems_commit.py → MemoryDB API 전환** | 직접 sqlite3는 FTS5 트리거 우회 위험 | 4/13 S27 |
| **TEMS PyPI+Skill 듀얼 배포** | atlas-docs[tems] optional dep + 스킬 등록 | 4/13 S26 |
| **TEMS 점진 전환** | 12 에이전트 중 위상군 먼저 verified | 4/13 S27 |
| **scaffold in package, registry out** | registry=머신상태, TEMS_REGISTRY_PATH env var | 4/13 S26 |

## 팀 현황
| 에이전트 | 위치 | TEMS 상태 | 현재 태스크 |
|---------|------|-----------|------------|
| 위상군 | E:\DnT\DnT_WesangGoon | **마이그레이션 완료** | S27 완료 |
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
| **S27** | **TEMS 패키지 구현 + 위상군 마이그레이션** | **✅** | **v0.1.0, 35 tests, 마이그레이션 완료** |
| S28 | 나머지 에이전트 마이그레이션 | 대기 | — |
