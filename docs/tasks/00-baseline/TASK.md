# Task: Phase 0 — Baseline

Status: done 2026-11-11 (PR #2).

## Definition of Done
- [x] `pytest -q` is green before any change (cloud-GPU and local-model tests skipped by `conftest.py`, DECISION-004).
- [x] CI is green on ubuntu (py 3.10, 3.12) and windows (py 3.12) (DECISION-005).
- [x] One short public-domain EPUB picked: *Alice's Adventures in Wonderland* (Gutenberg #11) at `runs/alice/alice.epub` (gitignored).
- [x] `scripts/extract_epub.py` extracts it cleanly.

## Test Plan
- Commands: `pytest -q`; `python scripts/extract_epub.py runs/alice/alice.epub --out runs/alice/out`
- Result: 438 passed, 269 skipped locally. Manifest: 14 spine items, cover is `source_only`, 12 chapters plus a title page marked `translate`.

## Notes / deviations
- The original plan said "clean clone, suite green". A raw Windows run had 22 failures in cloud-GPU tests (bash, CRLF), so those test files are skipped instead of fixed.
- Test commands for later phases: Phase 1 must keep the same 438 passed / 269 skipped, with no test edits.
