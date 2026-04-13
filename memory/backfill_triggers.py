"""
위상군 keyword_trigger 백필 스크립트
====================================
벤치마크(2026-03-28)에서 발견된 미매칭 케이스를 기반으로
기존 규칙의 keyword_trigger에 누락된 키워드를 보강합니다.

실행 방법 (위상군 세션에서):
    python memory/backfill_triggers.py --dry-run   # 변경 미리보기
    python memory/backfill_triggers.py              # 실제 적용

원칙:
  - 기존 trigger는 절대 삭제하지 않음 (추가만)
  - correction_rule 본문에서 핵심 키워드를 추출하여 trigger에 추가
  - 범용 단어(에러, 실패 등)는 이미 있으므로 도메인 특화 키워드만 추가
"""

import sys
from pathlib import Path

from tems.fts5_memory import MemoryDB


# ═══════════════════════════════════════════════════════════════
# 백필 대상: (rule_id, 추가할 키워드들, 근거)
# ═══════════════════════════════════════════════════════════════

BACKFILL_MAP = [
    # 벤치마크 미스 케이스에서 발견
    (9, [
        "CUDA", "OOM", "Out of Memory", "GPU", "메모리부족",
        "RuntimeError", "torch", "python",
    ], "CUDA OOM 프롬프트에서 미매칭 — trigger가 subprocess/cp949에만 특화"),

    # #3은 위상군 DB에 없음 (다른 에이전트 규칙) — 스킵

    (29, [
        "유니버스", "universe", "시총", "market_cap", "백테스트",
        "backtest", "survivorship", "종목", "필터",
    ], "종목 유니버스/백테스트 프롬프트에서 미매칭 — 보고서/산출물 trigger만 있었음"),

    # #2는 3DGS 규칙 — 수익률/포맷 키워드는 부적절, 스킵
    # #47은 스크린샷 피드백 규칙 — 세션시작 키워드 넣으면 오히려 노이즈, 스킵

    (28, [
        "감정", "emotion", "몰입", "engagement", "재미", "fun",
        "유저심리", "player_psychology",
    ], "유저 감정 프롬프트에서 미매칭 — 기존 trigger가 너무 구체적"),

    (35, [
        "오버레이", "overlay", "좌표", "coordinate", "position",
        "차트위", "on_chart",
    ], "오버레이 좌표 프롬프트에서 미매칭"),

    (40, [
        "좌표", "coordinate", "width", "너비", "차트크기",
        "overlay", "오버레이",
    ], "오버레이 좌표 프롬프트에서 미매칭"),

    # 추가: 벤치마크에서 노이즈 주범으로 발견된 범용 규칙들은
    # trigger를 더 specific하게 만들어야 하지만, 그건 축소 작업이므로
    # 이 스크립트에서는 다루지 않음 (별도 정밀화 작업 필요)
]


def run_backfill(dry_run: bool = False):
    db = MemoryDB()
    results = []

    for rule_id, new_keywords, reason in BACKFILL_MAP:
        with db._conn() as conn:
            rule = conn.execute(
                "SELECT id, category, keyword_trigger, correction_rule FROM memory_logs WHERE id = ?",
                (rule_id,),
            ).fetchone()

            if not rule:
                results.append({"id": rule_id, "status": "NOT_FOUND"})
                continue

            current_trigger = (rule["keyword_trigger"] or "").strip()
            current_set = set(current_trigger.lower().split())

            # 중복 제거: 이미 있는 키워드는 추가하지 않음
            genuinely_new = [
                kw for kw in new_keywords
                if kw.lower() not in current_set
            ]

            if not genuinely_new:
                results.append({
                    "id": rule_id,
                    "status": "SKIP",
                    "reason": "모든 키워드가 이미 존재",
                })
                continue

            updated_trigger = (current_trigger + " " + " ".join(genuinely_new)).strip()

            result = {
                "id": rule_id,
                "category": rule["category"],
                "before": current_trigger[:60],
                "added": genuinely_new,
                "after_len": len(updated_trigger.split()),
                "reason": reason,
            }

            if not dry_run:
                conn.execute(
                    "UPDATE memory_logs SET keyword_trigger = ? WHERE id = ?",
                    (updated_trigger, rule_id),
                )
                conn.commit()
                result["status"] = "APPLIED"
            else:
                result["status"] = "DRY_RUN"

            results.append(result)

    # FTS5 인덱스 재구축 (trigger가 변경되었으므로)
    if not dry_run:
        with db._conn() as conn:
            conn.execute("INSERT INTO memory_fts(memory_fts) VALUES('rebuild')")
            conn.commit()
        print("\n[FTS5 인덱스 재구축 완료]")

    return results


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"{'='*60}")
    print(f"  위상군 keyword_trigger 백필 {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"{'='*60}\n")

    results = run_backfill(dry_run=dry_run)

    for r in results:
        status = r["status"]
        rid = r["id"]

        if status == "NOT_FOUND":
            print(f"  #{rid:>3} — 규칙 없음 (삭제됨?)")
        elif status == "SKIP":
            print(f"  #{rid:>3} — SKIP: {r['reason']}")
        else:
            print(f"  #{rid:>3} [{r.get('category','')}] {status}")
            print(f"        before: {r.get('before','')}")
            print(f"        added:  {r['added']}")
            print(f"        total:  {r['after_len']} words")
            print(f"        reason: {r['reason']}")
            print()

    applied = sum(1 for r in results if r["status"] in ("APPLIED", "DRY_RUN"))
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    print(f"\n총 {applied}개 규칙 {'미리보기' if dry_run else '적용'}, {skipped}개 스킵")

    if dry_run:
        print("\n실제 적용하려면: python memory/backfill_triggers.py")


if __name__ == "__main__":
    main()
