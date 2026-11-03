# Draft-quality rubric

Five criteria, each pass/fail. Scored by the LLM judge (`judge.py`) on every draft, and by hand
on 30 samples (`hand_scores.csv`); judge–human agreement reported by `agreement.py`.

| # | Criterion | Pass means |
| --- | --- | --- |
| 1 | **Correct facts** | Every date, day count and company detail matches the injected structured data exactly |
| 2 | **Correct tone** | Professional and warm; appropriate for a practice writing to its own client |
| 3 | **One clear ask** | Exactly one action requested, stated unambiguously (not a list of maybes) |
| 4 | **No invented details** | Nothing claimed that isn't in the tool outputs — no made-up penalties, dates, history |
| 5 | **Appropriate urgency** | Urgency proportionate to days-until-due; overdue ≠ 30-days-out in register |

Scoring notes: judge returns pass/fail + one-line justification per criterion. A draft "passes
the rubric" only at 5/5.
