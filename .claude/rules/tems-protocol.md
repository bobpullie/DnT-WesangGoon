---
description: TEMS 메모리 커밋, TCL/TGL 규칙 생성, preflight 검색 시 적용
globs:
  - "memory/**"
alwaysApply: false
---

# TEMS — Topological Evolving Memory System 프로토콜

## 메모리 기록 (Memory Commit)
복잡한 작업의 한 단계(Step)가 실패하거나 성공할 때마다, `error_logs.db`에 다음 포맷으로 기록:
```json
{
  "timestamp": "2026-XX-XX",
  "context_tags": ["domain", "tech", "error_type"],
  "keyword_trigger": "searchable keywords",
  "action_taken": "What we tried",
  "result": "What happened",
  "correction_rule": "What to do next time",
  "category": "TCL|TGL|general"
}
```

## 작업 전 자가 검색 (Pre-flight BM25 Retrieval)
새로운 코드를 작성하거나 난해한 에러를 마주치면, 즉시 해결하려 하지 말고 FTS5+BM25 검색을 먼저 수행.
검색된 `correction_rule`을 현재 컨텍스트에 병합한 뒤 **"과거 메모리 검색 결과에 따라, A 방법 대신 B 방법을 사용합니다."**라고 명시적으로 선언하고 작업 진행.

## TCL (Topological Checklist Loop)
"앞으로", "이제부터", "이제", "이후로", "다음부터" 등 미래방향 지시어 감지 시:
1. 구체적 지시를 **추상적 위상 케이스**로 일반화
2. 유사 상황을 포괄하는 `keyword_trigger` 설계
3. `category='TCL'`로 FTS5 DB에 커밋

## TGL (Topological Guard Loop)
실수, 시행착오, 오류 발생 시:
1. 구체적 에러를 **위상적 패턴**으로 추상화
2. 동일 유형의 미래 오류를 포착할 `keyword_trigger` 설계
3. `category='TGL'`로 FTS5 DB에 커밋

## 상세 참조
4-Phase 아키텍처, DB 스키마, 자동 트리거 상세: `.claude/references/tems-architecture.md` 참조
