"""
TEMS 규칙 등록 CLI v2026.4 (Phase 2 — 분류·템플릿·게이트 통합)
================================================================

기본 사용 (좁은 규칙 = TCL):
  python tems_commit.py --type TCL --rule "규칙 내용" --triggers "키워드들" --tags "tag1,tag2"

구조화 등록 (넓은 위상 패턴 = TGL):
  python tems_commit.py --type TGL \
      --classification TGL-D \
      --abstraction L2 \
      --topological-case "위상 케이스 본문" \
      --forbidden "NOT TO DO" \
      --required "TO DO INSTEAD" \
      --triggers "BM25 키워드들" \
      --semantic-intent "의미 매칭용 한 줄" \
      --failure-signature "ModuleNotFoundError" \
      --success-signal "..." --compliance-check "..." \
      --tags "..."

옵션:
  --dry-run        등록 안 함, 게이트 결과만 표시
  --json           결과 JSON
  --force-warn     C/D/E 경고를 무시하고 등록 (A/B 거부는 무시 불가)
"""

import argparse
import sqlite3
import os
import sys
import json
import re
from datetime import datetime
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_logs.db")
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))

# 상위 디렉토리를 sys.path에 추가
_parent = os.path.dirname(MEMORY_DIR)
if _parent not in sys.path:
    sys.path.insert(0, _parent)


# ═══════════════════════════════════════════════════════════
# 분류 (Classification)
# ═══════════════════════════════════════════════════════════

VALID_TGL_CLASSIFICATIONS = {"TGL-T", "TGL-S", "TGL-D", "TGL-P", "TGL-W", "TGL-C", "TGL-M"}
VALID_ABSTRACTION_LEVELS = {"L1", "L2", "L3"}

# 분류 자동 추론용 시그널
CLASSIFICATION_HINTS = {
    "TGL-T": ["rm -rf", "git push", "force", "delete", "삭제", "tool 호출"],
    "TGL-S": ["환경변수", "사전조건", "startup", "초기화", "설치", "패키지 미", "pre-condition"],
    "TGL-D": ["ModuleNotFoundError", "ImportError", "import", "의존성", "패키지", "version mismatch"],
    "TGL-P": ["useEffect", "deps", "stale closure", "코드 패턴", "anti-pattern"],
    "TGL-W": ["순서", "워크플로우", "단계 전환", "spec 없이", "verification 없이", "절차"],
    "TGL-C": ["명명규칙", "컨벤션", "전달", "보고", "위임", "subagent"],
    "TGL-M": ["TEMS", "preflight", "hook", "memory system", "scaffold", "자기"],
}


def auto_classify_tgl(rule_text: str, instance: str = "") -> str:
    """규칙 텍스트에서 7-카테고리 자동 추론. 가장 많은 hint 매칭하는 카테고리."""
    text = (rule_text + " " + (instance or "")).lower()
    scores = Counter()
    for cls, hints in CLASSIFICATION_HINTS.items():
        for h in hints:
            if h.lower() in text:
                scores[cls] += 1
    if not scores:
        return "TGL-M"  # 기본값 — 메타로 분류 후 위상군 검토
    return scores.most_common(1)[0][0]


# ═══════════════════════════════════════════════════════════
# 게이트 A — Schema 검증
# ═══════════════════════════════════════════════════════════

def gate_a_schema(args, category: str) -> tuple[bool, list[str]]:
    """필수 슬롯 검증. 통과 못 하면 거부."""
    errors = []

    if not args.rule or len(args.rule.strip()) < 10:
        errors.append("rule이 너무 짧음 (최소 10자)")

    if not args.triggers or len(args.triggers.strip().split()) < 2:
        errors.append("triggers가 너무 적음 (최소 2개 키워드)")

    if category == "TGL":
        # TGL 필수 슬롯 (Phase 2D)
        if not args.classification:
            errors.append("TGL 등록 시 --classification 필수 (TGL-T/S/D/P/W/C/M)")
        elif args.classification not in VALID_TGL_CLASSIFICATIONS:
            errors.append(f"--classification 값 잘못됨: {args.classification}. 허용: {sorted(VALID_TGL_CLASSIFICATIONS)}")

        if not args.abstraction:
            errors.append("TGL 등록 시 --abstraction 필수 (L1/L2/L3, L2 권장)")
        elif args.abstraction not in VALID_ABSTRACTION_LEVELS:
            errors.append(f"--abstraction 값 잘못됨: {args.abstraction}. 허용: L1/L2/L3 (L0/L4 거부)")

        if not args.forbidden:
            errors.append("TGL 등록 시 --forbidden 필수 (NOT TO DO)")

        if not args.required:
            errors.append("TGL 등록 시 --required 필수 (TO DO INSTEAD)")

        # 카테고리별 추가 슬롯
        if args.classification == "TGL-D" and not args.failure_signature:
            errors.append("TGL-D는 --failure-signature 권장 (PostToolUse 매칭용)")
        if args.classification == "TGL-T" and not args.tool_pattern:
            errors.append("TGL-T는 --tool-pattern 권장 (PreToolUse 매칭용)")

    return (len(errors) == 0), errors


# ═══════════════════════════════════════════════════════════
# 게이트 B — 추상화 점수 (TGL만 적용)
# ═══════════════════════════════════════════════════════════

# 도메인 고유명사 (구체적 신호)
SPECIFIC_TOKENS_RE = re.compile(r"[A-Z][a-zA-Z0-9_]{4,}|[\w_]+\.(py|md|js|ts|json|sql)|#\d+|0x[0-9a-fA-F]+")
# 위상 카테고리 명사 (추상적 신호)
ABSTRACT_NOUNS = {
    "패턴", "구조", "관계", "위상", "시스템", "메커니즘", "원리", "프로토콜",
    "사이클", "변환", "사상", "동형", "공간", "케이스", "차원",
    "pattern", "structure", "topology", "system", "mechanism", "principle",
}


def gate_b_abstraction(rule_text: str, declared_level: str) -> tuple[bool, list[str]]:
    """추상화 점수 휴리스틱. L0/L4 자동 거부."""
    warnings = []

    text = rule_text.lower()
    specific_count = len(SPECIFIC_TOKENS_RE.findall(rule_text))
    abstract_count = sum(1 for w in ABSTRACT_NOUNS if w in text)

    # L0: 도메인 명사 매우 많음 (구체적), 추상 명사 거의 없음
    # L4: 추상 명사 매우 많고 구체 변수 0개 (적용 시점 모호)
    if specific_count >= 3 and abstract_count == 0:
        warnings.append(f"L0 의심 (specific={specific_count}, abstract=0): 너무 구체적 — 일반화 보강 필요")
    if abstract_count >= 4 and specific_count == 0:
        warnings.append(f"L4 의심 (abstract={abstract_count}, specific=0): 너무 추상적 — 적용 시점 명시 필요")

    # 선언된 level과 휴리스틱 불일치 경고
    if declared_level == "L2":
        if specific_count > 5:
            warnings.append(f"declared L2이나 specific 토큰 {specific_count}개 — L1에 가까움")
        if abstract_count > 5 and specific_count == 0:
            warnings.append(f"declared L2이나 abstract 토큰만 {abstract_count}개 — L3에 가까움")

    # L0/L4 의심 시 거부 (확신할 때만)
    rejected = (specific_count >= 5 and abstract_count == 0) or \
               (abstract_count >= 6 and specific_count == 0)

    return (not rejected), warnings


# ═══════════════════════════════════════════════════════════
# 게이트 C — 중복/모순 검사 (경고)
# ═══════════════════════════════════════════════════════════

def gate_c_duplication(category: str, rule: str, triggers: str) -> tuple[bool, list[str]]:
    """완전 중복은 차단, 유사도 0.8+는 경고."""
    warnings = []
    conn = sqlite3.connect(DB_PATH)

    try:
        # 완전 중복은 차단 (legacy 동작 유지)
        row = conn.execute("SELECT id FROM memory_logs WHERE correction_rule = ?", (rule,)).fetchone()
        if row:
            conn.close()
            return False, [f"완전 중복: rule_id={row[0]}"]

        # trigger 키워드 overlap 검사
        rows = conn.execute("SELECT id, keyword_trigger, correction_rule FROM memory_logs WHERE category = ?", (category,)).fetchall()
        new_kw = set(triggers.split())
        for r in rows:
            existing_kw = set((r[1] or "").split())
            if existing_kw and new_kw:
                overlap = len(existing_kw & new_kw) / max(len(existing_kw), len(new_kw))
                if overlap >= 0.85:
                    warnings.append(f"trigger 유사도 {overlap:.0%} — id={r[0]}: {(r[2] or '')[:60]}... (merge 검토)")
    finally:
        conn.close()

    return True, warnings


# ═══════════════════════════════════════════════════════════
# 게이트 D — Replay 시뮬레이션 (TGL-D/S만, 경고)
# ═══════════════════════════════════════════════════════════

def gate_d_replay(classification: str, triggers: str, failure_signature: str = "") -> tuple[bool, list[str]]:
    """과거 jsonl에서 trigger가 매칭됐을지 시뮬레이션."""
    warnings = []
    if classification not in ("TGL-D", "TGL-S"):
        return True, []

    log_path = os.path.join(MEMORY_DIR, "tool_failures.jsonl")
    if not os.path.exists(log_path):
        return True, ["tool_failures.jsonl 없음 — replay 시뮬레이션 skip"]

    try:
        lines = open(log_path, encoding="utf-8").read().strip().split("\n")
    except Exception:
        return True, ["jsonl 읽기 실패 — replay skip"]

    if not lines:
        return True, []

    matched = 0
    sig = failure_signature.lower() if failure_signature else ""
    trig_words = set(triggers.lower().split())
    for line in lines[-200:]:
        try:
            entry = json.loads(line)
        except Exception:
            continue
        text = (entry.get("response_excerpt", "") + " " + entry.get("cmd_summary", "")).lower()
        # signature 매칭
        if sig and sig in text:
            matched += 1
            continue
        # trigger 단어 매칭 (≥2개)
        hit = sum(1 for w in trig_words if w in text)
        if hit >= 2:
            matched += 1

    total = min(len(lines), 200)
    rate = matched / total if total else 0

    if matched == 0:
        warnings.append(f"replay 0건 매칭 (전체 {total}건) — trigger 약함 또는 새 패턴")
    elif rate > 0.3:
        warnings.append(f"replay {matched}/{total}건 ({rate:.0%}) 매칭 — overfit 의심")
    else:
        warnings.append(f"replay {matched}/{total}건 매칭 — 적절")

    return True, warnings


# ═══════════════════════════════════════════════════════════
# 게이트 E — Verifiability (경고)
# ═══════════════════════════════════════════════════════════

def gate_e_verifiability(category: str, success_signal: str, compliance_check: str) -> tuple[bool, list[str]]:
    """success_signal/compliance_check가 측정 가능한 신호인가."""
    warnings = []
    if category != "TGL":
        return True, []
    if not success_signal:
        warnings.append("success_signal 미정의 — 발동 효과 측정 불가")
    elif len(success_signal) < 15:
        warnings.append(f"success_signal 너무 짧음 ({len(success_signal)}자) — 구체화 권장")
    if not compliance_check:
        warnings.append("compliance_check 미정의 — 위상군 컴플라이언스 추적 불가")
    return True, warnings


# ═══════════════════════════════════════════════════════════
# 키워드 다양성 검사 (TCL 전용 게이트)
# ═══════════════════════════════════════════════════════════

NOUN_RE = re.compile(r"[가-힣]{2,}|[A-Za-z][\w-]{2,}")
TCL_STOPWORDS = {
    "있다", "없다", "되다", "하다", "이것", "그것", "저것", "이거", "그거",
    "is", "are", "the", "and", "or", "to", "for", "of", "in", "on",
    "이제부터", "앞으로", "항상", "반드시", "매번",
}


def check_keyword_diversity(rule: str, triggers: str) -> list[str]:
    """rule 본문 핵심 명사가 triggers에 충분히 들어갔는가."""
    warnings = []
    nouns = [n for n in NOUN_RE.findall(rule) if n.lower() not in TCL_STOPWORDS]
    if not nouns:
        return []
    noun_set = set(n.lower() for n in nouns)
    trigger_set = set(t.lower() for t in triggers.split())
    coverage = len(noun_set & trigger_set) / len(noun_set) if noun_set else 1.0
    if coverage < 0.5:
        warnings.append(
            f"trigger가 rule 본문 명사의 {coverage:.0%}만 커버 (총 {len(noun_set)}개 중 {len(noun_set & trigger_set)}개)."
            f" 누락 추천: {sorted(noun_set - trigger_set)[:8]}"
        )
    if len(trigger_set) < 5:
        warnings.append(f"triggers {len(trigger_set)}개 — 동의어 포함 5개 이상 권장")
    return warnings


# ═══════════════════════════════════════════════════════════
# 등록
# ═══════════════════════════════════════════════════════════

def commit_rule(args, source: str = "agent-auto") -> dict:
    """게이트 A~E 통과 후 DB 적재."""
    if not os.path.exists(DB_PATH):
        return {"ok": False, "error": f"DB not found: {DB_PATH}"}

    category = args.type
    rule = args.rule
    triggers = args.triggers
    tags = args.tags or ""

    # TGL 자동 분류 (--classification 미지정 시)
    classification = args.classification
    if category == "TGL" and not classification:
        classification = auto_classify_tgl(rule, args.topological_case or "")
        args.classification = classification

    # TGL: rule을 topological_case로 보강
    if category == "TGL" and args.topological_case:
        # 본문이 topological_case면 rule에 합치기 (단일 컬럼)
        rule_for_db = (
            f"[{classification} / {args.abstraction or 'L?'}] {args.topological_case}\n"
            f"FORBIDDEN: {args.forbidden or '(미정)'}\n"
            f"REQUIRED: {args.required or '(미정)'}"
        )
    else:
        rule_for_db = rule

    # ─── 게이트 ───
    gate_results = {}

    ok, errs = gate_a_schema(args, category)
    gate_results["A_schema"] = {"ok": ok, "messages": errs}
    if not ok:
        return {"ok": False, "error": "Gate A (schema) 거부", "gates": gate_results}

    if category == "TGL":
        ok, warns = gate_b_abstraction(rule, args.abstraction or "L2")
        gate_results["B_abstraction"] = {"ok": ok, "messages": warns}
        if not ok:
            return {"ok": False, "error": "Gate B (abstraction) 거부 (L0/L4 의심)", "gates": gate_results}
    else:
        # TCL: 키워드 다양성 검사
        warns = check_keyword_diversity(rule, triggers)
        gate_results["A2_keyword_diversity"] = {"ok": True, "messages": warns}

    ok, warns = gate_c_duplication(category, rule_for_db, triggers)
    gate_results["C_duplication"] = {"ok": ok, "messages": warns}
    if not ok:
        return {"ok": False, "error": "Gate C: 완전 중복", "gates": gate_results}

    if category == "TGL":
        ok, warns = gate_d_replay(classification, triggers, args.failure_signature or "")
        gate_results["D_replay"] = {"ok": ok, "messages": warns}

        ok, warns = gate_e_verifiability(category, args.success_signal or "", args.compliance_check or "")
        gate_results["E_verifiability"] = {"ok": ok, "messages": warns}

    # ─── DRY-RUN ───
    if args.dry_run:
        return {"ok": True, "dry_run": True, "would_register": {
            "category": category,
            "classification": classification,
            "abstraction": args.abstraction,
            "rule_preview": rule_for_db[:200],
        }, "gates": gate_results}

    # ─── DB 적재 ───
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now().isoformat()

    # tags 보강
    tag_parts = [t.strip() for t in tags.split(",") if t.strip()]
    tag_parts.append(f"source:{source}")
    if classification:
        tag_parts.append(f"classification:{classification}")
    if args.abstraction:
        tag_parts.append(f"abstraction:{args.abstraction}")
    if args.semantic_intent:
        tag_parts.append(f"semantic_intent:{args.semantic_intent[:80]}")
    if args.failure_signature:
        tag_parts.append(f"failure_signature:{args.failure_signature}")
    if args.tool_pattern:
        tag_parts.append(f"tool_pattern:{args.tool_pattern}")
    full_tags = ",".join(tag_parts)

    cur.execute("""
        INSERT INTO memory_logs (timestamp, category, context_tags, keyword_trigger, correction_rule, action_taken, result, severity, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, category, full_tags, triggers, rule_for_db, "registered-via-cli-v2", "pending", "info", rule_for_db[:120]))
    rule_id = cur.lastrowid

    # rule_health에 분류·추상화·needs_review 함께 기록
    needs_review = 1 if (category == "TGL" and args.abstraction == "L1") or args.needs_review else 0
    cur.execute("""
        INSERT INTO rule_health (rule_id, ths_score, status, classification, abstraction_level, needs_review, created_at, fire_count)
        VALUES (?, 0.5, 'warm', ?, ?, ?, ?, 0)
    """, (rule_id, classification, args.abstraction, needs_review, now))

    conn.commit()
    conn.close()

    # QMD 자동 동기화
    try:
        from memory.tems_engine import sync_single_rule_to_qmd
        sync_single_rule_to_qmd(rule_id)
    except Exception:
        pass

    return {
        "ok": True, "rule_id": rule_id, "category": category,
        "classification": classification, "abstraction": args.abstraction,
        "needs_review": bool(needs_review), "rule": rule_for_db[:80],
        "gates": gate_results,
    }


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="TEMS 규칙 등록 CLI v2026.4 (Phase 2)")
    parser.add_argument("--type", required=True, choices=["TCL", "TGL"])
    parser.add_argument("--rule", required=True)
    parser.add_argument("--triggers", required=True)
    parser.add_argument("--tags", default="")
    parser.add_argument("--source", default="agent-auto")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-warn", action="store_true", help="C/D/E 경고 무시 (A/B 거부는 무시 불가)")

    # TGL 전용 슬롯 (Phase 2D)
    parser.add_argument("--classification", choices=sorted(VALID_TGL_CLASSIFICATIONS), help="TGL 7-카테고리. 미지정 시 자동 추론")
    parser.add_argument("--abstraction", choices=sorted(VALID_ABSTRACTION_LEVELS), help="L1/L2/L3 (L2 권장, L0/L4 거부)")
    parser.add_argument("--topological-case", default="", help="L2 위상 케이스 본문")
    parser.add_argument("--forbidden", default="", help="NOT TO DO")
    parser.add_argument("--required", default="", help="TO DO INSTEAD")
    parser.add_argument("--semantic-intent", default="", help="dense 매칭용 의미 의도 한 줄")
    parser.add_argument("--failure-signature", default="", help="TGL-D/S 실패 시그니처 (PostToolUse 매칭)")
    parser.add_argument("--tool-pattern", default="", help="TGL-T 도구 패턴 (PreToolUse 매칭)")
    parser.add_argument("--success-signal", default="", help="이 규칙 작동 시 어떤 신호")
    parser.add_argument("--compliance-check", default="", help="컴플라이언스 측정 방법")
    parser.add_argument("--needs-review", action="store_true")

    args = parser.parse_args()
    result = commit_rule(args, source=args.source)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result.get("ok"):
            print(f"[TEMS] FAILED: {result.get('error')}", file=sys.stderr)
            for gname, gres in (result.get("gates") or {}).items():
                for m in gres.get("messages", []):
                    print(f"  - {gname}: {m}", file=sys.stderr)
            sys.exit(1)

        if result.get("dry_run"):
            print(f"[TEMS DRY-RUN] would register: {json.dumps(result['would_register'], ensure_ascii=False)}")
        else:
            extra = ""
            if result.get("classification"):
                extra += f" cls={result['classification']}"
            if result.get("abstraction"):
                extra += f" L={result['abstraction']}"
            if result.get("needs_review"):
                extra += " [needs_review]"
            print(f"[TEMS] {result['category']} #{result['rule_id']} registered:{extra} {result['rule']}")

        # 경고 표시
        for gname, gres in (result.get("gates") or {}).items():
            for m in gres.get("messages", []):
                print(f"  [{gname}] {m}", file=sys.stderr)


if __name__ == "__main__":
    main()
