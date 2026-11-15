# Task: Phase 7 — Bilingual labels for in-chapter entries in `toc.ncx` (BUG-016)

Status: done 2026-11-16. PR #29, landed on main through #31; CI green.

Related: BUG-016 (`docs/BUGS.md`). Evidence: Grade run 3 on *Scarcity* (vi), rubric (e).

## Why

In the bilingual EPUB, `nav.xhtml` is bilingual but `toc.ncx` is not for 65 of its 87 entries (64 in-chapter headings plus the second Part One entry). `patch_toc_ncx` in `scripts/nav_builder.py` skips same-file descendants on purpose. The Vietnamese heading is already in the page, in the `tgt` paragraph right after the anchor, but nothing reads it back. Readers that use the NCX (older Kindle and Kobo firmware, some desktop readers) show English-only section lists.

## Scope

In: `patch_toc_ncx` and its helpers in `scripts/nav_builder.py`; one new test file; assemble call path only if the function needs the assembled HTML passed in.
Out: adding NCX entries for pages the source NCX never listed (Title Page, brand page, Part Two/Three dividers, "THE BEGINNING"); changing `nav.xhtml`; any audit or detector change (so no Advise trigger; if that changes, stop and call Advise).

## Design (draft)

Vietnamese only. zh-tw output must stay byte-identical to the oracle. The switch is one `LanguageProfile` field (working name `ncx_section_labels: bool`, zh-tw False, vi True), which fires Advise (CLAUDE.md trigger 1). Turning on another language later means setting that field to True and adding a golden case for it. `patch_toc_ncx` gets an optional `chapter_html` argument (filename to assembled HTML); with the flag off or no HTML passed, it behaves exactly as today.

For each fragment navPoint that `patch_toc_ncx` currently skips:
1. Find the element with that `id` in the assembled chapter HTML.
2. Take the first following sibling with class `tgt`.
3. If its text is non-empty and differs from the English label, write `English ｜ Target`, using the same joiner as `_nav_display_label`.
4. Otherwise leave the label as it is (no sibling, empty text, or identical text).

The function currently receives only the NCX text and entries. It needs a way to read the chapter HTML (a callback or a dict of `filename -> html`). Pick the smallest signature change; keep `profile=None` working.

## Definition of Done

- [x] Golden record first (Ground-truth TDD): run `patch_toc_ncx` from `main` at `bb0eb35` (`git show bb0eb35:scripts/nav_builder.py`) on a synthetic fixture with chapter-level and in-chapter navPoints; save its real output as `test/golden/` data. This is the "before" behaviour.
- [x] A test built from that record fails on the new path before the change, for the in-chapter entries only.
- [x] zh-tw output (flag off) is byte-identical to the golden record for every navPoint, in-chapter ones included.
- [x] After the change, with the flag on (vi): chapter-level entries are byte-identical to the golden record; in-chapter entries become `English ｜ Target` when a `tgt` sibling exists, and stay unchanged when it does not.
- [x] Edge cases covered with synthetic text (no copyrighted book text): heading with inline markup; anchor on a wrapper element; no `tgt` sibling; `tgt` identical to source; nested navPoints.
- [x] `test/test_nav_builder.py`, `test/test_nav_fixes.py`, `test/test_ncx_doctitle.py` still pass unedited.
- [x] Real check on *Scarcity*: reassemble, then count NCX navPoints without a target-language label. Result 2026-11-13: 65 before, 2 after. Left: "BENIHANA" (translation equals source) and a second whole-file "Part One" entry with no anchor to read.
- [x] `pytest -q` passes; CI green on ubuntu 3.10/3.12 and windows 3.12.
- [x] `docs/DECISIONS.md` entry for the labelling rule and the vi-only rollout. Advise call logged in `docs/eagd-log.md`. Ledger row updated with the PR link. BUG-016 marked fixed with the PR.
- [x] A fourth Grade run after the change; report the result as it is. Done as Grade runs 5 and 6 with the new rubric (`docs/grade-rubric-validation.md`); run 6 passes.

## Test Plan

- Golden derivation: `git show bb0eb35:scripts/nav_builder.py > <scratch>/nav_builder_oracle.py`, run it on the fixture, save output.
- New tests: `pytest -q test/test_ncx_section_labels.py` (expect the red run first, then green).
- Regression: `pytest -q test/test_nav_builder.py test/test_nav_fixes.py test/test_ncx_doctitle.py` (23 passed before the change).
- Full suite: `pytest -q` (728 passed / 269 skipped before this phase).
- Real book: reassemble *Scarcity* with `scripts/assemble.py` and run the NCX count from the output EPUB.

## Sub-tasks

- [x] 7.1 User approves DoD and Test Plan and answers the open questions
- [x] 7.2 Branch `fix/ncx-section-labels` from `main`
- [x] 7.3 Golden record from `bb0eb35`
- [x] 7.4 Red test, then implementation to green
- [x] 7.5 Real-book check, full suite, PR, CI
- [x] 7.6 DECISIONS, BUGS, LEDGER updated; Grade run

## Open questions (answered 2026-11-13)

1. Apply to every language? User: not sure; do Vietnamese only first, and make adding another language easy. Done as the profile flag above.
2. Add NCX entries for pages the source NCX never listed? User agreed: no, out of scope.

## Progress notes

- The oracle predates the profile, so the golden record covers zh-tw only (no profile or chapter_html argument). The fixture has no `docTitle`, because BUG-008 already changed zh-tw docTitle output.
- 738 passed / 269 skipped locally. New: `test/test_ncx_section_labels.py` (10), `test/golden/golden_ncx_sections.json`, `ncx_fixture.py`, `derive_ncx.py`.
- Not done: PR and CI, Grade run 4, sync of the installed skill copy (`~/.claude/skills/book-translator/scripts`), commit.
- 2026-11-13: Grade run 4 (old prose rubric) failed (a), (b), (c), (e) on rubric strictness; rubric rewritten as yes/no checks in `docs/grade-rubric.md` with `scripts/grade_checks.py` (`test/test_grade_checks.py`). Dry run on *Scarcity*: 11 of 12 checks YES; E5 NO (9 `(untitled)` labels, logged as BUG-017). Out of this task's scope; adopted in `CLAUDE.md` by user approval.
