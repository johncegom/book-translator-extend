# Task Ledger

Current status: Phases 0 and 1 done and merged (PR #2, #3, #4). Phase 2 DoD is drafted (PR #5) with all open questions decided; it waits for your final approval, then the Advise call for the new fields.

Plan and rationale: `docs/plans/2026-11-11-vietnamese-language-profile.md`. This ledger tracks status only; a phase's DoD, test plan and notes live in its detail doc.

| # | Phase | Status | Evidence | Detail |
|---|-------|--------|----------|--------|
| 0 | Baseline | done 2026-11-11 | PR #2 (CI green: ubuntu py3.10/3.12, windows py3.12); `runs/alice/` extracts, 14 spine items | `docs/tasks/00-baseline/TASK.md` |
| 1 | Profile with zh-tw only | done 2026-11-11 (PR #4 still draft and unmerged) | PR #4; CI run 42961118515 green on ubuntu 3.10/3.12 and windows 3.12, 472 passed / 269 skipped | `docs/tasks/01-profile-zh-tw/TASK.md` |
| 2 | Vietnamese profile | not started (DoD drafted 2026-11-11, questions decided, awaiting final DoD approval) | | `docs/tasks/02-profile-vi/TASK.md` |
| 3 | Detector and audits | not started | | created when Phase 2 is done |
| 4 | Skill file | not started | | created when Phase 3 is done |
| 5 | One full book | not started | | created when Phase 4 is done |

Status values: not started / in progress / blocked / done. A phase is `done` only when its detail doc's Definition of Done is fully checked, and the Evidence cell links the PR or commit.

Resume checklist for a new session:
1. Read `CLAUDE.md`, then this ledger.
2. Open only the detail doc of the phase marked in progress (or the next one).
3. For code that is being moved or ported against existing behaviour, follow the Ground-truth TDD rule in `CLAUDE.md`.
4. Skim `docs/DECISIONS.md` and `docs/BUGS.md` before touching detector or audit code.
