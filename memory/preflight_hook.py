"""
위상군 Preflight Hook — UserPromptSubmit 자동 트리거
=====================================================
사용자 프롬프트가 제출될 때마다 Claude Code Hook에 의해 자동 실행됩니다.
프롬프트에서 키워드를 추출하여 FTS5 BM25 검색을 수행하고,
매칭된 TCL/TGL 규칙을 stdout으로 출력하여 위상군의 컨텍스트에 주입합니다.

stdin: { "prompt": "...", "session_id": "...", ... }
stdout: 매칭된 규칙 텍스트 (자동으로 위상군 컨텍스트에 주입됨)
"""

import sys
import json
import re
from pathlib import Path

# memory 디렉토리를 import path에 추가
MEMORY_DIR = Path(__file__).parent
sys.path.insert(0, str(MEMORY_DIR.parent))

from memory.fts5_memory import MemoryDB
from memory.tems_engine import EnhancedPreflight, RuleGraph


def strip_korean_suffix(word: str) -> str:
    """한국어 단어에서 조사/어미를 제거하여 어간을 추출.

    완벽한 형태소 분석은 아니지만, FTS5 prefix 매칭과 결합하여
    '퇴근할게요' → '퇴근', '마무리합시다' → '마무리' 등을 처리합니다.
    """
    # 흔한 어미/조사 패턴 (긴 것부터 매칭)
    suffixes = [
        # 종결어미
        "할게요", "합시다", "합니다", "했습니다", "하겠습니다",
        "할까요", "해주세요", "해볼게요", "해봅시다",
        "입니다", "습니다", "됩니다", "겠습니다",
        "할게", "할까", "하자", "해요", "해줘", "하죠",
        "인데요", "인데", "이에요", "이야",
        # 연결어미
        "하면서", "하면", "하고", "해서", "하니까", "하지만",
        "인데", "이라", "이면", "이고",
        # 관형형
        "하는", "했던", "할",
        # 조사
        "에서는", "에서", "에는", "에게", "까지", "부터",
        "으로", "에도", "이나", "이란",
        "에", "를", "을", "는", "은", "이", "가", "의", "와", "과",
        "도", "만", "로",
        # 보조용언
        "했어요", "했어", "했다", "해야",
        "됐어요", "됐어", "됐다",
        "시키", "하기", "되기",
        # 기타 활용형
        "할게요", "할까요", "합시다",
        "했는데", "하는데", "되는데",
        "거든요", "거든",
        "잖아요", "잖아",
        "네요", "군요",
    ]

    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            return word[: -len(suffix)]

    return word


def extract_keywords(prompt: str, max_tokens: int = 20) -> list[str]:
    """프롬프트에서 BM25 검색용 키워드를 추출.

    불용어를 제거하고, 한국어 어미를 정리한 뒤, 의미 있는 토큰만 남깁니다.
    반환값은 리스트 — 각 키워드로 개별 OR 검색을 수행합니다.
    """
    # 한국어/영어 불용어
    stopwords = {
        "은", "는", "이", "가", "을", "를", "에", "의", "로", "와", "과",
        "도", "만", "에서", "까지", "부터", "으로", "하고", "그리고",
        "또는", "및", "등", "것", "수", "때", "중", "후", "더",
        "좀", "잘", "한", "할", "해", "된", "되", "하는", "합니다",
        "해주세요", "부탁", "감사", "네", "예", "아니", "오늘", "내일",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall",
        "i", "you", "he", "she", "it", "we", "they",
        "my", "your", "his", "her", "its", "our", "their",
        "this", "that", "these", "those",
        "in", "on", "at", "to", "for", "of", "with", "by",
        "from", "up", "about", "into", "through", "during",
        "and", "but", "or", "not", "no", "so", "if", "then",
        "please", "thanks", "yes", "no",
        # Phase 0.5 generic noise words — 약매칭 차단
        "테스트", "확인", "체크", "진행", "시작", "마무리", "정리",
        "test", "check", "verify", "run", "start", "stop",
        "그래", "좋아", "맞아", "괜찮", "어때", "어떤",
    }

    tokens = []
    for word in prompt.split():
        cleaned = word.strip(".,!?;:\"'()[]{}~`@#$%^&*+=<>/\\|")
        if not cleaned or len(cleaned) <= 1:
            continue

        # 한국어 어미 제거
        stem = strip_korean_suffix(cleaned)

        if stem.lower() not in stopwords and len(stem) > 1:
            tokens.append(stem)

    # 중복 제거
    seen = set()
    unique = []
    for t in tokens:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)

    return unique[:max_tokens]


## Context Budget — 주입 상한 (Phase 0.5: "조용한 TEMS" 아키텍처)
## 종일군 지시(2026-04-19): 매 prompt 무차별 주입 금지. 키워드 강매칭 시에만 발동.
MAX_TCL = 2      # TCL 최대 주입 수
MAX_TGL = 2      # TGL 최대 주입 수
MAX_CASCADE = 1  # CASCADE 최대 주입 수
MAX_PREDICT = 1  # 예측 최대 주입 수
BM25_WEIGHT = 0.6
THS_WEIGHT = 0.4

# Phase 0.5: 매칭 임계값. final_score < 이 값이면 주입 안 함 (banner blindness 방지)
SCORE_THRESHOLD = 0.55       # 0.6*BM25(1위)=0.6 + 0.4*THS(0.5)=0.2 → 0.8 만점, 0.55 = 강매칭만
SEMANTIC_FALLBACK_ENABLED = True   # HybridRetriever (CUDA QMD dense) 폴백 활성 — BM25 키워드 한계 보완
                                   # 종일군 정정(2026-04-19): qmd-embed 스킬 + tems-wesanggoon 컬렉션 활용


def get_ths_scores() -> dict[int, tuple[float, str]]:
    """rule_health 테이블에서 (rule_id → (ths_score, status)) 매핑 로드"""
    import sqlite3
    db_path = MEMORY_DIR / "error_logs.db"
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT rule_id, ths_score, status FROM rule_health").fetchall()
        conn.close()
        return {r["rule_id"]: (r["ths_score"] or 0.5, r["status"] or "warm") for r in rows}
    except Exception:
        return {}


def record_fire(rule_ids: list[int]) -> None:
    """Phase 2A: 주입된 규칙의 fire_count++ + last_fired 갱신.

    매칭만으로는 부족 — 실제로 컨텍스트에 주입된 규칙만 카운트한다.
    rule_health에 row가 없으면 자동 생성.

    Phase 3B 확장: TGL 카테고리 규칙은 active_guards.json 에도 기록하여
    compliance_tracker 가 이후 도구 호출의 준수/위반을 자동 측정하도록 함.
    """
    if not rule_ids:
        return
    import sqlite3
    from datetime import datetime
    db_path = MEMORY_DIR / "error_logs.db"
    now = datetime.now().isoformat()
    try:
        conn = sqlite3.connect(str(db_path))
        # fire_count 갱신
        for rid in rule_ids:
            conn.execute("""
                INSERT INTO rule_health (rule_id, fire_count, last_fired, ths_score, status, created_at)
                VALUES (?, 1, ?, 0.5, 'warm', ?)
                ON CONFLICT(rule_id) DO UPDATE SET
                    fire_count = COALESCE(fire_count, 0) + 1,
                    last_fired = excluded.last_fired
            """, (rid, now, now))
        conn.commit()

        # Phase 3B: TGL 규칙만 active_guards에 push (compliance 추적 대상)
        placeholders = ",".join(["?"] * len(rule_ids))
        tgl_rows = conn.execute(
            f"SELECT id, category, context_tags FROM memory_logs WHERE id IN ({placeholders}) AND category = 'TGL'",
            rule_ids,
        ).fetchall()
        conn.close()

        if tgl_rows:
            _push_active_guards(tgl_rows, now)
    except Exception as e:
        # 카운팅 실패는 hook 동작을 막지 않음 — 단 진단 로그
        try:
            _log_diagnostic("record_fire_failure", e)
        except Exception:
            pass


def _push_active_guards(tgl_rows: list, fired_at: str, remaining_checks: int = 8) -> None:
    """TGL 규칙 발동을 active_guards.json 에 기록.

    compliance_tracker 가 이후 PostToolUse 마다 읽어서 forbidden/failure_signature
    위반 여부를 측정한다. 같은 규칙이 이미 활성이면 window만 리셋.
    """
    import sqlite3
    guards_path = MEMORY_DIR / "active_guards.json"
    try:
        if guards_path.exists():
            data = json.loads(guards_path.read_text(encoding="utf-8"))
        else:
            data = {"guards": []}

        existing_by_id = {g.get("rule_id"): g for g in data.get("guards", []) if isinstance(g.get("rule_id"), int)}

        for row in tgl_rows:
            rid = row[0]
            tags_raw = row[2] or ""
            # slot 파싱
            tags = {}
            for part in tags_raw.split(","):
                part = part.strip()
                if ":" in part:
                    k, _, v = part.partition(":")
                    tags[k.strip()] = v.strip()

            if rid in existing_by_id:
                # 이미 활성 — 재발동. Phase 3 P1-a-follow 패치:
                #   .update() 는 had_violation 을 덮어쓰므로 사용 금지. 슬롯을 개별 보충한다.
                #   had_violation=True 인 guard 는 remaining_checks 도 리셋하지 않는다.
                existing = existing_by_id[rid]
                existing["fired_at"] = fired_at
                existing["source"] = "preflight"
                if not existing.get("had_violation"):
                    existing["remaining_checks"] = remaining_checks
                for slot, val in (
                    ("classification", tags.get("classification", "")),
                    ("tool_pattern", tags.get("tool_pattern", "")),
                    ("failure_signature", tags.get("failure_signature", "")),
                ):
                    if val and not existing.get(slot):
                        existing[slot] = val
            else:
                data.setdefault("guards", []).append({
                    "rule_id": rid,
                    "classification": tags.get("classification", ""),
                    "tool_pattern": tags.get("tool_pattern", ""),
                    "failure_signature": tags.get("failure_signature", ""),
                    "source": "preflight",
                    "fired_at": fired_at,
                    "remaining_checks": remaining_checks,
                })

        guards_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        try:
            _log_diagnostic("active_guards_push_failure", e)
        except Exception:
            pass


def rank_by_ths(hits: list[dict], ths_map: dict[int, tuple[float, str]]) -> list[dict]:
    """BM25 순위(리스트 순서)와 THS 점수를 결합하여 재정렬.

    archive 상태 규칙은 제외. SCORE_THRESHOLD 미만은 제외 (Phase 0.5).
    """
    scored = []
    for rank, hit in enumerate(hits):
        rid = hit.get("id")
        ths_score, status = ths_map.get(rid, (0.5, "warm"))

        # archive 상태 규칙은 주입에서 제외
        if status == "archive":
            continue

        # BM25 순위 점수: 1위=1.0, 이후 감소
        bm25_score = 1.0 / (1 + rank)
        final_score = BM25_WEIGHT * bm25_score + THS_WEIGHT * ths_score

        # Phase 0.5: 임계값 미만은 주입 안 함 (약매칭 차단)
        if final_score < SCORE_THRESHOLD:
            continue

        hit["_final_score"] = final_score
        hit["_ths"] = ths_score
        hit["_status"] = status
        scored.append(hit)

    scored.sort(key=lambda x: x["_final_score"], reverse=True)
    return scored


def _has_sdc_trigger_tag(hit: dict) -> bool:
    """Hit의 context_tags에 sdc_trigger 태그가 포함됐는지 확인.

    SDC 선택적 발동(TCL #120 확장, 2026-04-21 S38) — tags에 sdc_trigger가
    포함된 TCL이 매칭됐을 때만 SDC 3-question gate 수행.
    """
    return "sdc_trigger" in str(hit.get("context_tags", ""))


def detect_sdc_mode() -> str:
    """SDC 모드 감지. 활성 TCL 중 sdc_auto_trigger_enabled 태그 보유 규칙이 있으면
    'rule+auto', 없으면 'rule-based' (기본).

    SDC.md §0 선택적 발동 체계 — 2026-04-21 S38 도입.
    """
    import sqlite3
    db_path = MEMORY_DIR / "error_logs.db"
    if not db_path.exists():
        return "rule-based"
    try:
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            """
            SELECT m.id FROM memory_logs m
            LEFT JOIN rule_health rh ON rh.rule_id = m.id
            WHERE m.context_tags LIKE '%sdc_auto_trigger_enabled%'
              AND (rh.status IS NULL OR rh.status != 'archive')
            LIMIT 1
            """
        ).fetchone()
        conn.close()
        return "rule+auto" if row else "rule-based"
    except Exception:
        return "rule-based"


def format_rules(preflight_result: dict, compact: bool = True) -> tuple[str, list[int]]:
    """preflight 결과를 위상군 컨텍스트 주입용 텍스트로 포맷.

    compact=True: summary만 출력 (컨텍스트 절약)
    compact=False: correction_rule 전문 출력 (기존 방식)

    Phase 2A: 반환 (output_text, fired_ids) — 실제 주입된 규칙 ID만 카운팅 대상
    """
    # THS 점수 로드
    ths_map = get_ths_scores()

    # THS 기반 재정렬 + archive 제외
    tcl_hits = rank_by_ths(preflight_result.get("tcl_hits", []), ths_map)[:MAX_TCL]
    tgl_hits = rank_by_ths(preflight_result.get("tgl_hits", []), ths_map)[:MAX_TGL]
    cascade_hits = rank_by_ths(preflight_result.get("cascade_hits", []), ths_map)[:MAX_CASCADE]
    predictions = preflight_result.get("predictions", [])[:MAX_PREDICT]

    if not tcl_hits and not tgl_hits and not cascade_hits and not predictions:
        return "", []

    fired_ids: list[int] = []
    lines = []
    lines.append("<preflight-memory-check>")

    if tcl_hits:
        lines.append("[TCL]")
        for r in tcl_hits:
            text = r.get("summary") or r.get("correction_rule", "") if compact else r.get("correction_rule", "")
            rid = r.get('id', '?')
            sdc_mark = " [SDC]" if _has_sdc_trigger_tag(r) else ""
            lines.append(f"  #{rid}{sdc_mark}: {text}")
            if isinstance(rid, int):
                fired_ids.append(rid)

    # Phase 0 T2.2: TGL은 항상 풀텍스트로 주입 (가드 행동이 잘리지 않도록)
    if tgl_hits:
        lines.append("[TGL]")
        for r in tgl_hits:
            text = r.get("correction_rule", "") or r.get("summary", "")
            rid = r.get('id', '?')
            lines.append(f"  #{rid}: {text}")
            if isinstance(rid, int):
                fired_ids.append(rid)

    if cascade_hits:
        lines.append("[CASCADE]")
        for r in cascade_hits:
            cat = r.get('category', '?')
            if cat == "TGL":
                text = r.get("correction_rule", "") or r.get("summary", "")
            else:
                text = r.get("summary") or r.get("correction_rule", "") if compact else r.get("correction_rule", "")
            rid = r.get('id', '?')
            lines.append(f"  #{rid}: [{cat}] {text}")
            if isinstance(rid, int):
                fired_ids.append(rid)

    if predictions:
        lines.append("[PREDICT]")
        for p in predictions:
            conf = p.get("confidence", 0)
            lines.append(f"  ({conf:.0%}) {p.get('predicted_error', '')[:40]}")

    lines.append("</preflight-memory-check>")
    return "\n".join(lines), fired_ids


def detect_project_scope(cwd: str) -> list[str]:
    """현재 작업 디렉토리에서 프로젝트명을 감지하여 허용할 project 태그 목록 반환.

    v2026.3.29: 관리군 도입 — 프로젝트 스코핑으로 무관한 규칙 주입 방지
    """
    cwd_lower = cwd.lower().replace("\\", "/")

    scopes = ["project:meta", "project:all"]  # 메타/범용 규칙은 항상 허용

    if "mrv" in cwd_lower or "dnt" in cwd_lower or "agentinterface" in cwd_lower:
        scopes.append("project:dnt")
        scopes.append("project:mrv")

    # 태그가 없는 레거시 규칙도 허용 (점진적 마이그레이션)
    scopes.append("")

    return scopes


def filter_by_project(hits: list[dict], allowed_scopes: list[str]) -> list[dict]:
    """규칙의 context_tags에서 project: 태그를 확인하고 스코프 밖 규칙을 제거."""
    filtered = []
    for hit in hits:
        tags = str(hit.get("context_tags", ""))

        # 스킬로 전환된 규칙은 preflight에서 제외
        rule = str(hit.get("correction_rule", ""))
        if rule.startswith("/") and "스킬로" in rule:
            continue

        # project 태그 추출
        project_tag = ""
        for part in tags.split(","):
            part = part.strip()
            if part.startswith("project:"):
                project_tag = part
                break

        # 허용된 스코프에 포함되면 통과
        if project_tag in allowed_scopes:
            filtered.append(hit)

    return filtered


## 규칙성 패턴 감지 — TEMS 자동 등록 유도 (1차 방어선)
TCL_PATTERNS = [
    r"이제부터\s", r"앞으로\s", r"항상\s", r"매번\s", r"반드시\s",
    r"from\s+now\s+on", r"always\s", r"every\s+time", r"규칙으로\s", r"원칙으로\s",
]
TGL_PATTERNS = [
    r"하지\s*마", r"금지", r"절대\s", r"하면\s*안", r"never\s",
    r"don'?t\s", r"do\s+not\s", r"prohibited", r"사용하지\s", r"쓰지\s*마",
]


def detect_rule_intent(prompt: str) -> str | None:
    """사용자 프롬프트에서 규칙성 의도를 감지.

    Returns: "TCL", "TGL", or None
    """
    for pat in TGL_PATTERNS:
        if re.search(pat, prompt, re.IGNORECASE):
            return "TGL"
    for pat in TCL_PATTERNS:
        if re.search(pat, prompt, re.IGNORECASE):
            return "TCL"
    return None


def main():
    try:
        # stdin에서 hook 데이터 읽기
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
        prompt = data.get("prompt", "")
        cwd = data.get("cwd", "")

        if not prompt.strip():
            sys.exit(0)

        # 프로젝트 스코프 감지 (v2026.3.29 관리군)
        allowed_scopes = detect_project_scope(cwd)

        # 키워드 추출
        keywords = extract_keywords(prompt)
        if not keywords:
            sys.exit(0)

        db = MemoryDB()

        # FTS5 prefix 쿼리 구성
        fts_query = " OR ".join(f'"{kw}"*' for kw in keywords)

        # 1단계: FTS5 BM25 기본 검색
        try:
            base_result = db.preflight(fts_query, limit=5)
        except Exception:
            base_result = {"tcl_hits": [], "tgl_hits": [], "general_hits": []}
            seen_ids = set()
            for kw in keywords[:5]:
                try:
                    partial = db.preflight(f'"{kw}"*', limit=3)
                    for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                        for hit in partial.get(cat, []):
                            if hit["id"] not in seen_ids:
                                seen_ids.add(hit["id"])
                                base_result[cat].append(hit)
                except Exception:
                    continue

        # 1-b단계: BM25가 빈약하면 HybridRetriever 시맨틱 폴백 (Phase 0.5: 기본 비활성)
        # 시맨틱 폴백은 약매칭을 만들어내는 주범 — 종일군 지시로 비활성화
        total_bm25 = sum(len(base_result.get(c, [])) for c in ("tcl_hits", "tgl_hits"))
        if SEMANTIC_FALLBACK_ENABLED and total_bm25 < 2:
            try:
                from memory.tems_engine import HybridRetriever
                hybrid = HybridRetriever(db)
                hybrid_result = hybrid.preflight(" ".join(keywords), limit=5)
                existing_ids = set()
                for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                    for hit in base_result.get(cat, []):
                        existing_ids.add(hit.get("id"))
                for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                    for hit in hybrid_result.get(cat, []):
                        if hit.get("id") not in existing_ids:
                            base_result[cat].append(hit)
                            existing_ids.add(hit.get("id"))
            except Exception:
                pass

        # 2단계: Rule Graph 캐스케이드 — 직접 매칭된 규칙의 이웃도 포함
        direct_ids = []
        for cat in ("tcl_hits", "tgl_hits", "general_hits"):
            for hit in base_result.get(cat, []):
                if isinstance(hit.get("id"), int):
                    direct_ids.append(hit["id"])

        cascade_hits = []
        predictions = []

        if direct_ids:
            try:
                graph = RuleGraph(db)
                cascade_hits = graph.get_cascade_rules(direct_ids, threshold=0.3)
                # co-activation 기록 (그래프 학습)
                graph.record_co_activation(prompt, direct_ids)
            except Exception:
                pass

            # 3단계: Predictive TGL — TGL이 매칭되었으면 후속 에러 예측
            try:
                from memory.tems_engine import PredictiveTGL
                predictor = PredictiveTGL(db)
                for tgl in base_result.get("tgl_hits", []):
                    if isinstance(tgl.get("id"), int):
                        preds = predictor.predict_next_errors(tgl["id"], min_confidence=0.3)
                        for p in preds:
                            predictions.append({
                                "predicted_error": p.get("correction_rule", ""),
                                "confidence": p.get("confidence", 0),
                            })
            except Exception:
                pass

        # 프로젝트 스코핑 필터 적용 (v2026.3.29 관리군)
        filtered_tcl = filter_by_project(base_result.get("tcl_hits", []), allowed_scopes)
        filtered_tgl = filter_by_project(base_result.get("tgl_hits", []), allowed_scopes)
        filtered_cascade = filter_by_project(cascade_hits, allowed_scopes)
        filtered_general = filter_by_project(base_result.get("general_hits", []), allowed_scopes)

        # 통합 결과
        result = {
            "tcl_hits": filtered_tcl,
            "tgl_hits": filtered_tgl,
            "cascade_hits": filtered_cascade,
            "predictions": predictions,
            "general_hits": filtered_general,
        }

        # 규칙성 패턴 감지 — TEMS 등록 유도 힌트 주입
        rule_type = detect_rule_intent(prompt)
        if rule_type:
            print(f"<rule-detected type=\"{rule_type}\">")
            print(f"종일군의 지시에 규칙성 패턴이 감지되었습니다. AutoMemory가 아닌 TEMS에 등록하세요:")
            print(f'python memory/tems_commit.py --type {rule_type} --rule "규칙 내용" --triggers "키워드" --tags "태그"')
            print(f"</rule-detected>")

        # 매칭 결과 포맷
        output, fired_ids = format_rules(result)
        if output:
            print(output)
            # Phase 2A: 실제로 주입된 규칙의 fire_count 갱신 (cap 후 ID만)
            record_fire(fired_ids)

        # SDC 모드 신호 — 확장 모드(rule+auto)일 때만 출력. 기본(rule-based)은 침묵.
        # 확장 모드 활성화: sdc_auto_trigger_enabled 태그 TCL 1건 등록 (SDC.md §0 참조).
        if detect_sdc_mode() == "rule+auto":
            print("<sdc-mode>rule+auto</sdc-mode>")

    except Exception as e:
        # Phase 0 T1.1: silent fail 금지. 구조화 로깅 + degraded 신호 출력
        _log_diagnostic("preflight_failure", e)
        try:
            print(f"<preflight-degraded reason=\"{type(e).__name__}: {str(e)[:120]}\"/>")
        except Exception:
            pass

    sys.exit(0)


def _log_diagnostic(event_type: str, exc: Exception) -> None:
    """Phase 0 T1.1: preflight 실패를 jsonl로 영속화. 자기관찰 채널."""
    import traceback
    from datetime import datetime
    try:
        log_path = MEMORY_DIR / "tems_diagnostics.jsonl"
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "exc_type": type(exc).__name__,
            "exc_msg": str(exc)[:300],
            "traceback": traceback.format_exc()[-800:],
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 로깅 실패는 hook을 막지 않음 (단, 이중 fail 시에만)


if __name__ == "__main__":
    main()
