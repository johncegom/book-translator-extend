# Task Ledger

Current status: Phase 0 done. Phase 1 (profile, zh-tw only) in progress: DoD approved, sub-task 1.1a done (frozen fixture), 1.1b (golden tests) is next.

Plan and rationale: `docs/plans/2026-11-11-vietnamese-language-profile.md`. This ledger tracks status only; a phase's DoD, test plan and notes live in its detail doc.

| # | Phase | Status | Evidence | Detail |
|---|-------|--------|----------|--------|
| 0 | Baseline | done 2026-11-11 | PR #2 (CI green: ubuntu py3.10/3.12, windows py3.12); `runs/alice/` extracts, 14 spine items | `docs/tasks/00-baseline/TASK.md` |
| 1 | Profile with zh-tw only | in progress (DoD approved 2026-11-11; 1.1a done) | | `docs/tasks/01-profile-zh-tw/TASK.md` |
| 2 | Vietnamese profile | not started | | created when Phase 1 is done |
| 3 | Detector and audits | not started | | created when Phase 2 is done |
| 4 | Skill file | not started | | created when Phase 3 is done |
| 5 | One full book | not started | | created when Phase 4 is done |

Status values: not started / in progress / blocked / done. A phase is `done` only when its detail doc's Definition of Done is fully checked, and the Evidence cell links the PR or commit.

Resume checklist for a new session:
1. Read `CLAUDE.md`, then this ledger.
2. Open only the detail doc of the phase marked in progress (or the next one).
3. For code that is being moved or ported against existing behaviour, follow the Ground-truth TDD rule in `CLAUDE.md`.
4. Skim `docs/DECISIONS.md` and `docs/BUGS.md` before touching detector or audit code.
