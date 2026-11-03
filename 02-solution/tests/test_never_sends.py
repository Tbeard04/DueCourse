"""The never-sends design rule, enforced as a test.

Walks the AST of every Python file in the solution and fails if any mail-sending module is
imported anywhere. If this test is red, the architecture has been broken.
"""

import ast
from pathlib import Path

FORBIDDEN = {
    "smtplib",
    "imaplib",
    "poplib",
    "mailbox",
    "yagmail",
    "sendgrid",
    "mailgun",
    "postmarker",
    "resend",
    "mailjet_rest",
    "exchangelib",
}

SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [SOLUTION_ROOT / "src", SOLUTION_ROOT / "review_app", SOLUTION_ROOT / "scripts"]


def imported_modules(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split(".")[0]


def test_no_mail_sending_imports() -> None:
    offenders = []
    for scan_dir in SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            offenders += [
                f"{path.relative_to(SOLUTION_ROOT)}: imports {module}"
                for module in imported_modules(tree)
                if module in FORBIDDEN
            ]
    assert not offenders, "the system must never be able to send email:\n" + "\n".join(offenders)
