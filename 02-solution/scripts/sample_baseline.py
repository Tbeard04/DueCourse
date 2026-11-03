"""Print a fresh random 12-company slice for a baseline Task-A timing run.

Part of the measurement protocol (04-measurement/measurement.md): each of the ten manual
timing runs checks a different random dozen, so run this once per timing run. Prints each
company's name, number, and register URL to open.

Run from 02-solution:  uv run python scripts/sample_baseline.py [run_number]
Passing the run number (1-10) makes the sample reproducible for the write-up.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REGISTER = "https://find-and-update.company-information.service.gov.uk/company"


def main() -> int:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(10_000)
    portfolio = json.loads(Path("portfolio.json").read_text(encoding="utf-8"))
    sample = random.Random(seed).sample(portfolio, 12)
    print(f"Task A sample (seed {seed}) — start the stopwatch, then for each company record")
    print("both due dates and your urgency call in your scratch spreadsheet:\n")
    for entry in sample:
        print(f"  {entry['name']}")
        print(f"    {REGISTER}/{entry['company_number']}")
    print("\nStop the clock when the twelfth row is written. Record mm:ss in measurement.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
