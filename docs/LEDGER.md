# Task Ledger

Current status: Phases 0-5 done and merged. The `vi` pipeline ran end to end on *Subtract* (EN to VI) and on a fresh-session smoke book; no phase is open.

Plan and rationale: `docs/plans/2026-11-11-vietnamese-language-profile.md`. This ledger tracks status only; a phase's DoD, test plan and notes live in its detail doc.

| # | Phase | Status | Evidence | Detail |
|---|-------|--------|----------|--------|
| 0 | Baseline | done 2026-11-11 | PR #2 (CI green: ubuntu py3.10/3.12, windows py3.12); `runs/alice/` extracts, 14 spine items | `docs/tasks/00-baseline/TASK.md` |
| 1 | Profile with zh-tw only | done 2026-11-11 (PR #4 still draft and unmerged) | PR #4; CI run 42961118515 green on ubuntu 3.10/3.12 and windows 3.12, 472 passed / 269 skipped | `docs/tasks/01-profile-zh-tw/TASK.md` |
| 2 | Vietnamese profile | done 2026-11-11 | PR #6 merged (`71dc493`); 547 passed / 269 skipped | `docs/tasks/02-profile-vi/TASK.md` |
| 3 | Detector and audits | done 2026-11-11 | PR #7 merged; CI run 43033595597 green, 634 passed / 269 skipped | `docs/tasks/03-detector-audits/TASK.md` |
| 4 | Skill file | done 2026-11-12 | PRs #9 and #11 merged; CI run 43069367924 green on ubuntu 3.10/3.12 and windows 3.12, 668 passed / 269 skipped | `docs/tasks/04-skill-file/TASK.md` |
| 5 | One full book | done 2026-11-12 | PRs #13, #14, #15 (BUG-006 fix), #16, #17 (BUG-007 fix) merged; 672 passed / 269 skipped; Kindle read-back confirmed | `docs/tasks/05-full-book/TASK.md` |

Status values: not started / in progress / blocked / done. A phase is `done` only when its detail doc's Definition of Done is fully checked, and the Evidence cell links the PR or commit.

Resume checklist for a new session:
1. Read `CLAUDE.md`, then this ledger.
2. Open only the detail doc of the phase marked in progress (or the next one).
3. For code that is being moved or ported against existing behaviour, follow the Ground-truth TDD rule in `CLAUDE.md`.
4. Skim `docs/DECISIONS.md` and `docs/BUGS.md` before touching detector or audit code.
