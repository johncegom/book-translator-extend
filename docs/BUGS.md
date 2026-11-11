# Bug Log

Entry format: symptom, root cause (or "unknown"), reachability, options, status. Logging is not fixing — wait for an explicit decision before applying a fix.

Candidates from the Vietnamese plan, to log only if they actually occur: short-paragraph detection gaps; English text with a single accented letter (e.g. "café") misclassified as Vietnamese.

## BUG-001: EPUBs that pack several chapters into one spine file extract as a few huge items

**Symptom:** `runs/subtract/subtract.epub` (the table of contents lists about 20 sections) extracts to 5 spine items; the three body items hold 125k, 137k and 198k characters, each spanning several chapters. Alice extracts to 14 one-chapter items.
**Root cause:** `scripts/extract_epub.py` treats the OPF spine as the source of truth and creates one item per spine file; it does not split a file at chapter headings or at the NCX/nav entries. Found by reading the code and the manifest, not yet traced to a failing run.
**Reachability:** Reachable for any EPUB built with split files that group chapters (found with *Subtract*). The subagent translates one spine item per call, so an item of 100k+ characters will not fit in a call; the nav and coverage audits would also see one entry for several chapters. Not hit in Phases 0-3, which use excerpts.
**Options:** (a) split a spine file at the NCX/nav targets or at chapter headings during extraction; (b) a separate pre-step script before extraction; (c) document the limit in `SKILL.md` and require pre-split EPUBs.
**Status:** fix timing agreed 2026-11-11: decide the approach (a, b or c) at the start of Phase 4 and fix before Phase 5 starts. No fix applied yet. Phase 3 uses excerpts of *Subtract* (user, 2026-11-11); this blocks Phase 5 (full book) unless fixed or avoided.

## BUG-002: A vi book whose glossary register matches no hint phrase is audited with min_length_ratio 0.22

**Symptom:** `_min_length_ratio_from_book_dir` returns the hard-coded 0.22 when no register matches, which is effectively no truncation check for Vietnamese (measured vi/en ratios are 0.80 and up; a half-translated paragraph at 0.45 passes).
**Root cause:** `resolve_register` matches the glossary's free-text `style_anchor.register` against each hint's phrase ("storyteller cadence", "practical business memoir", "scholarly precision"), and the glossary prompt (`scripts/glossary.py:94`) lets the model "invent a new register description"; an invented phrase matches nothing. The default 0.22 was tuned for Chinese. A pinned Phase 2 test (`test_min_length_ratio_for_vi_falls_back_to_the_default`) asserts 0.22 for an unknown register, so changing it needs a decision.
**Reachability:** Reachable whenever the glossary model invents a phrase. Not yet observed in a real run (Phase 5 will show).
**Options:** (a) a top-level `default_min_length_ratio` key in `assets/register_hints.vi.json`, read by `_min_length_ratio_from_book_dir`, no new profile field, and amend the pinned test; (b) constrain the glossary prompt to the registered phrases; (c) a check after the glossary step that `resolve_register` is not None (advice from the Phase 3 Advise call).
**Status:** fix timing agreed 2026-11-11: fix in Phase 4, in code (option a: `default_min_length_ratio` key in `assets/register_hints.vi.json`, amend the pinned Phase 2 test). Not fixed yet. Source: Advise call 3.6 (claims verified in the code).

## BUG-003: The standalone `translation_quality_audit.py` CLI ignores the profile

**Symptom:** `main()` calls `_min_length_ratio_from_book_dir(args.book_dir)` and `audit_with_warnings(...)` with no profile, so running the script directly on a vi book uses zh-tw hints, the zh-tw target class and the Simplified gate.
**Root cause:** the CLI has no `--target-lang` option and does not read `state.json`. `audit_suite.py` passes the profile, so only direct invocation is affected.
**Reachability:** only by running `python scripts/translation_quality_audit.py` directly on a vi book. Not checked whether `SKILL.md` does that (Phase 4 should check).
**Options:** read `target_lang` from the book dir's `state.json` as `audit_suite` does, or add `--target-lang`.
**Status:** fix timing agreed 2026-11-11: fix in Phase 4 alongside the `SKILL.md` edit (read `target_lang` from `state.json`). Not fixed yet. `SKILL.md` runs the audits through `audit_suite` but also names `translation_quality_audit.py` directly.

## BUG-004: A dispatch `register_override` changes the prompt but not the audit's length threshold

**Symptom:** with a `register_override`, the subagent prompt uses the overridden register's rules, but `_min_length_ratio_from_book_dir` still resolves the register from the glossary's `style_anchor`.
**Root cause:** the audit only calls `resolve_register(glossary, ...)`; it has no access to the override. Found by reading the code, not observed in a run.
**Reachability:** only when an override is used and its register has a different ratio from the glossary's. With the flat vi value (0.60 for all registers) it has no effect for vi; for zh-tw the academic register is 0.30 against 0.22.
**Options:** pass the override into the audit, or leave it.
**Status:** no fix scheduled (agreed 2026-11-11). Revisit only if a real run uses `register_override`.

<!--
## BUG-001: <short symptom>

**Symptom:**
**Root cause:**
**Reachability:**
**Options:**
**Status:** pending decision
-->
