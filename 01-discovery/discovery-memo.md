# Discovery memo — the as-is workflow

*Audience: the practice's partners. Author: engagement lead. Date: 2026-11-03.*

> **Honesty note:** this is a simulated engagement. The client below is a composite built from
> public practitioner accounts and official guidance — the sourced-vs-assumed table at the end
> says exactly which claims rest on evidence and which are modelling assumptions. The method
> (interview → map → quantify → scope) is the transferable part; at a real client, this memo
> would be built from interviews and timesheets.

## The client

A three-partner UK accountancy practice with ~60 limited-company clients (trades, hospitality,
consultancies, online retail — the real, public portfolio in `02-solution/portfolio.json`).
Compliance work — annual accounts, confirmation statements, company tax returns — is fixed-fee,
so every hour spent on administration around it comes straight out of margin.

## The as-is workflow

Deadline-chasing is owned by the **office manager**, with partner escalation for stubborn cases:

1. **Tracking.** A master spreadsheet lists each company's accounts and confirmation-statement
   due dates, keyed in by hand when a client is onboarded and updated when someone remembers.
   Vendors of deadline software describe exactly this pattern — dates spread across lists
   "owned by whoever last opened the file" ([FigsFlow](https://figsflow.com/uk/platform/hmrc-deadlines/)) —
   and it matches public practitioner discussion of pre-software practice.
2. **The weekly check.** Each Monday the office manager works down the spreadsheet, opening the
   [Companies House register](https://find-and-update.company-information.service.gov.uk/) for
   anything that looks close, to confirm the live due date (the spreadsheet drifts: extended
   accounting periods, shortened periods, and filings made directly by clients all move dates).
3. **Chasing.** For anything due soon or overdue, she writes a chasing email: look up the
   contact, check what records are still missing, get the tone right (a long-standing client
   who is three days late is not a strike-off case), and remember what was already promised.
4. **Escalation and the January problem.** Unanswered chases get a partner phone call.
   In January the same person is also drowning in Self Assessment — the online filing deadline
   is 31 January ([GOV.UK](https://www.gov.uk/self-assessment-tax-returns/deadlines)) — and
   practitioner guidance is blunt that the fix is chasing client information early
   ([AccountingWEB](https://www.accountingweb.co.uk/practice/general-practice/beat-the-january-self-assessment-panic)).
   Company deadlines that fall in or near January are the ones that get missed.

## Where the hours go

Industry evidence says this class of work is a real cost, though precise figures for
deadline-chasing alone don't exist — which is exactly why this engagement measures its own:

- A UK survey of 350 accountancy partners and staff found ~**1.2 hours per working day** lost
  to low-value tasks, including chasing clients and colleagues
  ([IT Brief UK, on the £5.3bn sector estimate](https://itbrief.co.uk/story/uk-accountancy-inefficiencies-cost-sector-gbp-5-3-billion)).
- In a US survey, **69% of accountants** said they spend too much time gathering client
  documents ([Canopy 2022, via Glasscubes](https://www.glasscubes.com/the-hidden-cost-of-chasing-clients/)).
- For this practice we model the workflow at **once a week**: a full deadline check across the
  60-company book plus ~8 chasing emails. The baseline time for those tasks is **measured, not
  assumed** — protocol and results in [04-measurement](../04-measurement/measurement.md).

## The cost of failure

This is a workflow where errors carry a price tag, which is what makes the measurement real:

- Late **annual accounts** incur an automatic penalty: **£150** (up to 1 month late), **£375**
  (1–3 months), **£750** (3–6 months), **£1,500** (over 6 months) for a private company —
  **doubled** if accounts are late two years running
  ([GOV.UK: penalties for late filing](https://www.gov.uk/annual-accounts/penalties-for-late-filing)).
- A late **confirmation statement** has no automatic fine, but the company and its directors
  can be prosecuted and the company **struck off the register**
  ([GOV.UK: confirmation statement guidance](https://www.gov.uk/guidance/filing-your-companys-confirmation-statement)).
- The practice's own portfolio shows the failure mode is real: two of its sixty companies are
  overdue *right now*, one of them already carrying a compulsory strike-off gazette notice.

## Alternatives considered

Practice-management suites (e.g. the deadline modules in Bright, Senta/Capium-class tools —
see [a survey of the category](https://www.accountingfirms.co.uk/blog/best-practice-management-software-for-accounting-firms/))
track deadlines, but they are subscription platforms that still leave the drafting and the
judgement to the office manager, and this practice has not adopted one. DueCourse is scoped
deliberately smaller: live register data, triage, *drafted* chases for human approval, and a
Monday digest — the pieces the spreadsheet workflow actually loses hours to. If the practice
later adopts a PM suite, the triage and drafting pattern ports.

## Sourced vs assumed

| Claim | Status | Source |
| --- | --- | --- |
| Penalty amounts and doubling rule | **Sourced** | [GOV.UK annual accounts](https://www.gov.uk/annual-accounts/penalties-for-late-filing) (also in the RAG corpus) |
| Confirmation-statement consequences (prosecution, strike-off) | **Sourced** | [GOV.UK CS guidance](https://www.gov.uk/guidance/filing-your-companys-confirmation-statement) |
| Spreadsheet-based deadline tracking is common and error-prone in small practices | **Sourced (vendor + practitioner accounts)** | [FigsFlow](https://figsflow.com/uk/platform/hmrc-deadlines/), AccountingWEB threads |
| Time lost to low-value/chasing work is material | **Sourced (adjacent surveys, not deadline-specific)** | [IT Brief UK](https://itbrief.co.uk/story/uk-accountancy-inefficiencies-cost-sector-gbp-5-3-billion), [Glasscubes/Canopy](https://www.glasscubes.com/the-hidden-cost-of-chasing-clients/) |
| January crunch displaces company-deadline work | **Sourced (practitioner guidance) + assumed (effect size)** | [AccountingWEB](https://www.accountingweb.co.uk/practice/general-practice/beat-the-january-self-assessment-panic) |
| The specific practice: 3 partners, 60 companies, office-manager-owned workflow, weekly cadence, ~8 chases/week | **Assumed** (composite client) | — |
| Baseline time per weekly run | **Measured** | [04-measurement](../04-measurement/measurement.md) |
