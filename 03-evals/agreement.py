"""Judge-vs-human agreement on the hand-scored drafts.

Joins hand_scores.csv with results/judge_scores.json on draft_id and reports per-criterion
percent agreement and Cohen's kappa. If agreement is poor, the judge is distrusted — that is
the point of measuring it.

hand_scores.csv columns: draft_id, model, <criterion columns with 1/0>, notes.

Run from 02-solution:  uv run python ../03-evals/agreement.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from _common import CRITERIA, RESULTS_DIR, write_results

HAND_SCORES = Path(__file__).resolve().parent / "hand_scores.csv"


def cohens_kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    """Binary Cohen's kappa; None when undefined (chance agreement is 1)."""
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    p_judge = sum(a for a, _ in pairs) / n
    p_human = sum(b for _, b in pairs) / n
    expected = p_judge * p_human + (1 - p_judge) * (1 - p_human)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def main() -> int:
    judge_path = RESULTS_DIR / "judge_scores.json"
    if not judge_path.exists():
        sys.exit("results/judge_scores.json missing — run judge.py first")
    judge_rows = {row["draft_id"]: row for row in json.loads(judge_path.read_text())["rows"]}

    with HAND_SCORES.open(encoding="utf-8") as fh:
        hand_rows = [row for row in csv.DictReader(fh) if row.get("draft_id")]
    if not hand_rows:
        sys.exit("hand_scores.csv is empty — hand-score ~30 drafts first (see draft_rubric.md)")

    joined = [(h, judge_rows[h["draft_id"]]) for h in hand_rows if h["draft_id"] in judge_rows]
    skipped = len(hand_rows) - len(joined)

    report: dict = {"n": len(joined), "skipped_unjudged": skipped, "criteria": {}}
    print(f"Agreement on {len(joined)} drafts ({skipped} hand-scored but not judged — skipped)")
    for criterion in CRITERIA:
        pairs = [
            (bool(judge[criterion]), hand[criterion].strip() in ("1", "true", "True", "pass"))
            for hand, judge in joined
        ]
        agreement = sum(a == b for a, b in pairs) / len(pairs)
        kappa = cohens_kappa(pairs)
        report["criteria"][criterion] = {
            "percent_agreement": round(agreement, 4),
            "cohens_kappa": round(kappa, 4) if kappa is not None else None,
        }
        kappa_str = f"{kappa:.2f}" if kappa is not None else "n/a"
        print(f"  {criterion:<22} agreement {agreement:.0%}   kappa {kappa_str}")

    path = write_results("agreement.json", report)
    print(f"Full results -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
