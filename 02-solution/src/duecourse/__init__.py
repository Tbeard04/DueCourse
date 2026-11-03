"""DueCourse: filing-deadline triage and human-approved chasing-email drafts.

Design rules (see 05-handover/risk-register.md):
- Deadlines and urgency are deterministic, computed from Companies House data — never by an LLM.
- The system never sends email. There is no mail library in this codebase; a test enforces it.
"""

__version__ = "0.1.0"
