# Task: Phase 13 — Short-line coverage accepts a marked translation with a new accented letter (BUG-018)

Status: done 2026-11-20 (PR #45 merged, `c585e68`). Advise ran 2026-11-20 (`docs/eagd-log.md`).

Related: BUG-018 (detector rejects short Vietnamese labels). The detector stays untouched: counting capitalised tokens flips three pinned tests (`test/test_vi_detector_phase3.py:38-44`, audit test at 158) and the same function decides which source lines are skipped; a gated detector rule only gave 305 to 271 warnings.

## Why

*The Personal MBA* gets 305 amber warnings "missing adjacent vi" for correct short translations ("Attention" to "Sự chú ý", "Goals" to "Mục tiêu"). Measured on four finished vi books, 585 short-line warnings in total.

## Scope

In: one private helper and one condition inside the short-line (`_is_newly_in_scope`) branch of `scripts/bilingual_coverage_audit.py`; new test file; DECISIONS entry; docs.
Out: `is_target_text` and every detector or threshold; 50+ character behaviour (stays a FAILURE); `_covered_by_ancestor` (still detector only, inline nodes covered through an ancestor are not affected); `translation_quality_audit.py`; any `LanguageProfile` field. No zh gate: it applies to every profile (zh gets no benefit, no harm).

## Design (Advise variant of "3b")

A source line under 50 characters that the detector path would warn about is skipped when its next sibling:
1. has `tgt` in its class list,
2. has non-empty text that differs from the source (after whitespace cleaning),
3. contains an alphabetic non-ASCII character that the source line does not contain (`{c for c in tgt if c.isalpha() and ord(c) > 127} - set(src)` is not empty).

Why condition 3 and not "any non-ASCII character": punctuation (a bullet, an em dash, curly quotes) or an accented letter copied from the source would let English near-echoes through ("—Reid" to "— Reid", "Read replicas" to "• Read replica").

Known limit, to be stated in the DECISIONS entry: a `tgt` class means assemble wrote a model or label string there, not that this line was translated. After a paragraph-count mismatch later `tgt` lines can hold another line's translation. The real guard is the rewriter's "paragraph count mismatch" warning, not this audit.

## Measured (read-only, four finished vi books)

Short-line warnings 585. Variant clears 355 (Scarcity 8 of 16, System Design Interview 42 of 255, *The Personal MBA* 299 of 305, Orwell 6 of 9). Still warn: exact echoes and ASCII-only near-echoes. Not measured: a bad translation that has a new accented letter, other languages.

## Definition of Done

- [x] Tests first, seen red (only (a) was red; the guards were green and were proven to bite by a mutation check with the naive rule): (a) vi "Attention" with `tgt tgt-vi` "Sự chú ý" gives no warning; (b) exact echo "Begin Reading" still warns; (c) "Data centers" to "Data center" still warns; (d) "Reid" to "—Reid" (punctuation only) still warns; (e) "He met Nguyễn in the market." to "He met Nguyễn at the market." still warns; (f) sibling without the `tgt` class still warns; (g) a 50+ character source with a tgt line the detector rejects is still a FAILURE; (h) zh-tw short "Reid" to "—Reid" with `tgt tgt-zh` still warns.
- [x] Existing tests are unedited and pass; `pytest -q` passes (777 passed, 269 skipped). [x] CI run 44585266720 green on main after the merge.
- [x] Real check: *The Personal MBA* 6 warnings (was 305), 0 failures; System Design Interview 213 (was 255); Scarcity 8 (16); Orwell 3 (9).
- [x] `docs/DECISIONS.md` entry (DECISION-020) (tradeoff and the known limit above).
- [x] BUG-018 updated: FIXED WITH A LIMIT in the table and the entry, with the PR link; ledger row links the PR.

## Test Plan

- `pytest -q test/test_coverage_short_lines.py` (new; b to e can be one parametrized test)
- `pytest -q test/test_bilingual_coverage_audit.py test/test_vi_detector_phase3.py` (unedited)
- `pytest -q`
- Real book: `python -m scripts.bilingual_coverage_audit --source <src.epub> --output <vi.epub> --book-dir <book_dir>` and compare warning counts with `_audit_with_warnings`.

## Progress notes

- 2026-11-20: detector options R2 and R4 measured and not adopted (log: BUG-018). Audit-side rule measured: option 3 clears 383, "3b" 360, Advise variant 355 of 585. Advise answered (opus, claude-opus-5-5).
- 2026-11-20: approved, implemented. 8 new tests; the mutation check (naive any-non-ASCII rule) turned 3 guards red. 777 passed / 269 skipped. Real books match the prediction. Open: CI and merge.
