# Task Ledger

Current status: Phases 0-5 done and merged. The `vi` pipeline ran end to end on *Subtract* (EN to VI) and on a fresh-session smoke book; no phase is open.

Plan and rationale: `docs/plans/2026-11-11-vietnamese-language-profile.md`. This ledger tracks status only; a phase's DoD, test plan and notes live in its detail doc.

| # | Phase | Status | Evidence | Detail |
|---|-------|--------|----------|--------|
| 0 | Baseline | done 2026-11-11 | PR #2 (CI green: ubuntu py3.10/3.12, windows py3.12); `runs/alice/` extracts, 14 spine items | `docs/tasks/00-baseline/TASK.md` |
| 1 | Profile with zh-tw only | done 2026-11-11 | PR #4 merged 2026-11-11 (`dac59fe`); CI run 42961118515 green on ubuntu 3.10/3.12 and windows 3.12, 472 passed / 269 skipped | `docs/tasks/01-profile-zh-tw/TASK.md` |
| 2 | Vietnamese profile | done 2026-11-11 | PR #6 merged (`71dc493`); 547 passed / 269 skipped | `docs/tasks/02-profile-vi/TASK.md` |
| 3 | Detector and audits | done 2026-11-11 | PR #7 merged; CI run 43033595597 green, 634 passed / 269 skipped | `docs/tasks/03-detector-audits/TASK.md` |
| 4 | Skill file | done 2026-11-12 | PRs #9 and #11 merged; CI run 43069367924 green on ubuntu 3.10/3.12 and windows 3.12, 668 passed / 269 skipped | `docs/tasks/04-skill-file/TASK.md` |
| 5 | One full book | done 2026-11-12 | PRs #13, #14, #15 (BUG-006 fix), #16, #17 (BUG-007 fix) merged; 672 passed / 269 skipped; Kindle read-back confirmed | `docs/tasks/05-full-book/TASK.md` |
| 6 | Test for `bt_finalize.py` | done 2026-11-13 | PRs #23 and #24 merged (BUG-011 fixed in #24); CI run 43371499935 green on ubuntu 3.10/3.12 and windows 3.12; 4 tests, 728 passed / 269 skipped after #25 | `docs/tasks/06-bt-finalize-test/TASK.md` |
| 7 | Bilingual NCX section labels (BUG-016) | done 2026-11-16 (vi only) | PR #29 (landed on main through #31); CI run 43744360320 green on ubuntu 3.10/3.12 and windows 3.12; 748 passed / 269 skipped | `docs/tasks/07-ncx-section-labels/TASK.md` |
| 8 | No "(untitled)" English side in nav labels (BUG-017) | done 2026-11-16 | PR #30 (landed on main through #31); CI run 43744360320 green on ubuntu 3.10/3.12 and windows 3.12; 748 passed / 269 skipped | `docs/tasks/08-nav-placeholder-labels/TASK.md` |
| 9 | Grade N1 and JC false alarms (BUG-019, BUG-020) | done 2026-11-17 | PR #33 merged (`e7b2a39`); CI run 43896241718 green, 753 passed / 269 skipped; *The Personal MBA* 14/14 script checks YES | `docs/tasks/09-grade-n1-jc-false-alarms/TASK.md` |
| 10 | Font override for Vietnamese | done 2026-11-17 | PR #34 merged (`d45c8da`); CI run 43896142345 green on ubuntu 3.10/3.12 and windows 3.12, 757 passed / 269 skipped; real book checked by user | `docs/tasks/10-font-override/TASK.md` |
| 11 | Coverage audit failure text names the language (BUG-005) | done 2026-11-17 | PR #38 merged (`13db0a6`); 764 passed / 269 skipped on main (local); CI run 43935572921 on main | `docs/tasks/11-coverage-message-language/TASK.md` |
| 12 | Coverage audit command line picks the language (BUG-022) | done 2026-11-17 | PR #41 merged (`d490779`); CI run 43936583478 green on ubuntu 3.10/3.12 and windows 3.12, 769 passed / 269 skipped; *The Personal MBA* PASS with `--book-dir` | `docs/tasks/12-coverage-cli-book-dir/TASK.md` |
| 13 | Short-line coverage accepts a marked translation (BUG-018) | done 2026-11-20 | PR #45 merged (`c585e68`); CI run 44585266720 green; 777 passed / 269 skipped; *The Personal MBA* 305 to 6 short-line warnings | `docs/tasks/13-short-line-coverage/TASK.md` |
| 14 | Translate text inside HTML tables (BUG-012 option a) | not started | | |
| 15 | Endnote lines pass the coverage audit without hand-written exemptions (BUG-015) | not started | | |
| 16 | Check other callers of `validate_translation` for marker-less replies (BUG-011) | not started | | |
| 17 | Decide whether the blockquote feature box stays one block (BUG-014) | not started | | |

Status values: not started / in progress / blocked / done. A phase is `done` only when its detail doc's Definition of Done is fully checked, and the Evidence cell links the PR or commit.

Resume checklist for a new session:
1. Read `CLAUDE.md`, then this ledger.
2. Open only the detail doc of the phase marked in progress (or the next one).
3. For code that is being moved or ported against existing behaviour, follow the Ground-truth TDD rule in `CLAUDE.md`.
4. Skim `docs/DECISIONS.md` and `docs/BUGS.md` before touching detector or audit code.
