# Task: Phase 6 — Automated test for `scripts/bt_finalize.py`

Status: done 2026-11-13. PR #23 (script) and PR #24 (tests and the BUG-011 catch) merged; CI run 43371499935 green on ubuntu 3.10/3.12 and windows 3.12.

Depends on: PR #23 (adds `scripts/bt_finalize.py`) being merged, so this work branches from `main` with the script present. Related: BUG-010 (`docs/BUGS.md`), `test/test_state_concurrency.py`.

## Why

PR #23 moved the run helper into `scripts/` and switched it to `state.update`. It shipped with no automated test (stated in the PR body). Two things are currently unguarded: that the script marks an item done only after validation passes, and that parallel finalizers do not lose a `state.json` update, which is the reason the script exists in this form.

## Scope

In: one new test file, `test/test_bt_finalize.py`. Plus the BUG-011 catch in `scripts/bt_finalize.py`.
Out: refactoring the script (the BUG-011 catch is the only script edit), testing `dispatch` or `translation_log` internals (they have their own tests), CI changes.

## Definition of Done

- [x] `test/test_bt_finalize.py` covers four behaviours (the fourth added 2026-11-12 on Advise, user-approved), using a synthetic two-paragraph chapter (no copyrighted book text):
  1. Valid reply: exit 0, `OK <item> 2 paras` on stdout, `chapters/<item>_translation.txt` holds the two paragraphs joined by a blank line, the item is `done` in `state.json`, a `translation_log` entry exists.
  2. Invalid reply (one marker missing): exit 1, `WARNINGS` on stdout, the item stays `pending`, no translation file is written.
  3. Reply with no markers (`validate_translation` passes, `extract_aligned_translation` raises): exit 1 with `WARNINGS` and no traceback, item stays `pending`, no translation file. Guards the order extract, write, `state.update`. Logged and fixed (script only) as BUG-011; the one-line script change is in scope by user decision 2026-11-13.
  4. Parallel: six copies of the real script run as separate processes; all six items end `done`.
- [x] The parallel test is shown to fail when the script's `state.update` call is replaced by plain `state.load` + `state.save` (red check), then the script is restored unchanged (`git diff scripts/bt_finalize.py` is empty).
- [x] `pytest -q` passes locally (723 passed, 269 skipped) with no other test edited or removed.
- [x] CI green on ubuntu 3.10/3.12 and windows 3.12 (run 43371499935).
- [x] Ledger row updated with the PR link.

## Test Plan

- New file only: `pytest -q test/test_bt_finalize.py` (expect 4 passed).
- Red check, run by hand once, three times (the race is probabilistic): swap in the unlocked load/save in `scripts/bt_finalize.py`, run `pytest -q test/test_bt_finalize.py -k parallel`, expect failure each time, restore the file.
- Full suite: `pytest -q`; expect the previous count plus 4 (720 + 4 = 724 passed, 269 skipped before any other change).
- Note the limit: the parallel test is probabilistic. On a very fast machine it could pass without the lock; it failed on all three runs in the draft. It cannot give a false failure with the lock in place.

## Sub-tasks

- [x] 6.1 User approves the DoD and Test Plan
- [x] 6.2 Wait for PR #23 to merge; branch `test/bt-finalize` from `main`
- [x] 6.3 Add the test file (a draft already exists untracked at `test/test_bt_finalize.py` on `feat/bt-finalize-script`; carry it over, do not rewrite it)
- [x] 6.4 Red check, full suite, PR, CI
- [x] 6.5 Ledger and this doc ticked

## Open questions

1. Branch order: wait for PR #23 to merge (recommended, cleaner history), or stack this on `feat/bt-finalize-script` now?
2. Is the probabilistic parallel test acceptable in CI, or do you want a deterministic variant (for example, holding the lock from the test and asserting a second `update` waits)? The deterministic one is slower to write and tests the lock rather than the script.
