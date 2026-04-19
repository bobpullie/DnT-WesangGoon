"""Migration: 기존 TGL 규칙의 classification + abstraction_level NULL → 자동 채움.

전략:
1. classification: auto_classify_tgl(rule_text) — 7-카테고리 힌트 매칭. 0 hit 시 TGL-M (기본값).
2. abstraction_level: gate_b 휴리스틱 변형.
   - specific_count >> abstract_count → L1
   - 균형 → L2
   - abstract_count >> specific_count → L3
   - 둘 다 0 → L1 (보수적, needs_review=1)
3. needs_review 플래그:
   - L1이면 needs_review=1 (위상군이 L2 승격 여부 검토)
   - TGL-T인데 context_tags에 tool_pattern 슬롯이 없으면 needs_review=1 (PreToolUse 매칭 불가)
   - TGL-D인데 failure_signature 슬롯이 없으면 needs_review=1

실행: python memory/_migrate_classification.py [--apply]
  기본은 dry-run (DB 미변경). --apply 시 UPDATE 수행.
"""
import argparse
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent
DB_PATH = MEMORY_DIR / "error_logs.db"

sys.path.insert(0, str(MEMORY_DIR))
from tems_commit import (
    CLASSIFICATION_HINTS,
    SPECIFIC_TOKENS_RE,
    ABSTRACT_NOUNS,
)


def classify_with_confidence(rule_text: str, instance: str = "") -> tuple[str, int]:
    """auto_classify_tgl 의 반환값에 top-score 를 함께 리턴.

    score=0 이면 어떤 hint 도 매칭되지 않은 fallback (TGL-M 기본값) — 신뢰도 낮음.
    """
    text = (rule_text + " " + (instance or "")).lower()
    scores = Counter()
    for cls, hints in CLASSIFICATION_HINTS.items():
        for h in hints:
            if h.lower() in text:
                scores[cls] += 1
    if not scores:
        return "TGL-M", 0
    top_cls, top_score = scores.most_common(1)[0]
    return top_cls, top_score


def estimate_abstraction(rule_text: str) -> tuple[str, str]:
    """gate_b 휴리스틱 변형. (level, reason) 반환."""
    text = rule_text.lower()
    specific_count = len(SPECIFIC_TOKENS_RE.findall(rule_text))
    abstract_count = sum(1 for w in ABSTRACT_NOUNS if w in text)

    if specific_count == 0 and abstract_count == 0:
        return "L1", "signals=0/0 (default L1, needs_review)"
    if specific_count >= 3 and abstract_count <= 1:
        return "L1", f"specific={specific_count} > abstract={abstract_count}"
    if abstract_count >= 3 and specific_count <= 1:
        return "L3", f"abstract={abstract_count} > specific={specific_count}"
    return "L2", f"balanced specific={specific_count} abstract={abstract_count}"


def parse_tags(context_tags: str) -> dict:
    out = {}
    for part in (context_tags or "").split(","):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            out[k.strip()] = v.strip()
    return out


def decide_needs_review(classification: str, abstraction: str, tags: dict, cls_score: int) -> tuple[int, list[str]]:
    reasons = []
    if classification == "TGL-M" and cls_score == 0:
        reasons.append("classifier fallback — 힌트 0매칭, TGL-M 기본값 (재분류 필요)")
    if abstraction == "L1":
        reasons.append("L1 — L2 승격 검토 필요")
    if classification == "TGL-T" and not tags.get("tool_pattern"):
        reasons.append("TGL-T 이지만 tool_pattern 슬롯 부재 — PreToolUse 매칭 불가")
    if classification == "TGL-D" and not tags.get("failure_signature"):
        reasons.append("TGL-D 이지만 failure_signature 슬롯 부재 — PostToolUse 매칭 불가")
    needs_review = 1 if reasons else 0
    return needs_review, reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 UPDATE 수행 (기본은 dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="처리 규칙 수 제한 (0 = 전체)")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT m.id, m.correction_rule, m.context_tags, m.category,
               rh.classification, rh.abstraction_level, rh.needs_review
        FROM memory_logs m
        LEFT JOIN rule_health rh ON rh.rule_id = m.id
        WHERE m.category = 'TGL'
          AND (rh.classification IS NULL OR rh.classification = '')
        ORDER BY m.id
    """).fetchall()

    if args.limit:
        rows = rows[: args.limit]

    print(f"=== Migration target: {len(rows)} TGL rules (classification NULL) ===\n")

    summary = Counter()
    abs_summary = Counter()
    review_flagged = 0
    updates = []

    fallback_count = 0
    for r in rows:
        body = r["correction_rule"] or ""
        tags = parse_tags(r["context_tags"])
        cls, cls_score = classify_with_confidence(body)
        abs_lvl, abs_reason = estimate_abstraction(body)
        review, review_reasons = decide_needs_review(cls, abs_lvl, tags, cls_score)

        summary[cls] += 1
        abs_summary[abs_lvl] += 1
        if review:
            review_flagged += 1
        if cls == "TGL-M" and cls_score == 0:
            fallback_count += 1

        updates.append({
            "rule_id": r["id"],
            "classification": cls,
            "classification_score": cls_score,
            "abstraction_level": abs_lvl,
            "needs_review": review,
            "review_reasons": review_reasons,
            "abs_reason": abs_reason,
            "body_preview": body[:60].replace("\n", " "),
        })

    # Dry-run 보고서
    print("=== 전체 추론 결과 ===")
    for u in updates:
        flag = "⚠" if u["needs_review"] else " "
        score_str = f"score={u['classification_score']}"
        print(f"  {flag} #{u['rule_id']:3d} [{u['classification']}/{u['abstraction_level']}, {score_str}] {u['body_preview']}")
        if u["review_reasons"]:
            for reason in u["review_reasons"]:
                print(f"       ↳ {reason}")

    print(f"\n=== classification 집계 ===")
    for cls, count in summary.most_common():
        print(f"  {cls:8s} {count}")

    print(f"\n=== abstraction 집계 ===")
    for lvl, count in abs_summary.most_common():
        print(f"  {lvl:4s} {count}")

    print(f"\n=== needs_review 플래그: {review_flagged}/{len(rows)} 건 ===")
    print(f"=== TGL-M fallback (힌트 0매칭): {fallback_count}/{len(rows)} 건 — 실제 카테고리 불명 ===")

    if not args.apply:
        print("\n[DRY-RUN] DB 변경 없음. 실제 적용하려면 --apply 옵션 사용.")
        conn.close()
        return

    # Apply
    now = datetime.now().isoformat()
    applied = 0
    for u in updates:
        try:
            # rule_health 레코드가 아직 없으면 INSERT, 있으면 UPDATE
            existing = conn.execute(
                "SELECT 1 FROM rule_health WHERE rule_id = ?", (u["rule_id"],)
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE rule_health
                    SET classification = ?, abstraction_level = ?, needs_review = ?
                    WHERE rule_id = ?
                """, (u["classification"], u["abstraction_level"], u["needs_review"], u["rule_id"]))
            else:
                conn.execute("""
                    INSERT INTO rule_health
                      (rule_id, classification, abstraction_level, needs_review, ths_score, status, created_at)
                    VALUES (?, ?, ?, ?, 0.5, 'warm', ?)
                """, (u["rule_id"], u["classification"], u["abstraction_level"], u["needs_review"], now))
            applied += 1
        except Exception as e:
            print(f"  !! #{u['rule_id']} UPDATE failed: {e}")

    conn.commit()
    conn.close()
    print(f"\n[APPLIED] {applied}/{len(updates)} rows updated.")


if __name__ == "__main__":
    main()
