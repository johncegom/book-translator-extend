# Task: Phase 3 — Detector and audits

Test book: *Subtract* (user, 2026-11-11). Alice fixtures are kept as-is.

Status: done 2026-11-11 (PR #7, CI green; unmerged).

Depends on: Phase 2 (merged, PR #6, `71dc493`). Plan: `docs/plans/2026-11-11-vietnamese-language-profile.md`. Decisions to honour: DECISION-003 (50-char rule, echo check, ratio), DECISION-010 (letters plus function words; supersedes the letter rule in 003).

## What Phase 3 must deliver

`vi` judged sensibly by the two audits: Vietnamese siblings pass, English echoes and untranslated chapters fail, and the length-ratio check uses a threshold measured for English→Vietnamese. zh-tw behaviour stays byte-identical (golden tests from Phase 1/2 must stay green, untouched).

## Facts from the code at `71dc493`

1. `_vi_is_target_text` (`scripts/lang_profile.py:206`) is letters-only. "Xin chào" is a known false negative (Phase 2 note).
2. `translation_quality_audit._audit_findings` (lines 107-179) has **no echo check**. A sibling `tgt-vi` paragraph identical to its source passes unless the length check trips. For zh-tw an echo cannot pass (no Han), for `vi` it can.
3. The length check applies at `len(src_text) >= 50` and `min_length_ratio` defaults to 0.22 (zh-tw tuned). `register_hints.vi.json` has no `min_length_ratio`. Vietnamese is roughly as long as English, so 0.22 would let a badly truncated translation through.
4. `bilingual_coverage_audit` calls `profile.is_target_text` on the sibling (lines 64, 136, 164), so the detector change flows through there.
5. `is_untranslated_source` (named in CLAUDE.md's Advise trigger) does not exist in the code; the nearest thing is the source-only branch at `translation_quality_audit.py:138`. Treated as that branch.

## Proposed scope

A. Detector: `is_target_text` for `vi` = distinctive letter OR at least one function word from a short, unambiguous list (DECISION-010). Candidate list to be validated against labelled vi/fr/pt/en samples; words that are also common English/French/Portuguese words are excluded (e.g. "không" is safe, "me", "do", "la", "non" are not).
B. Echo check: in `translation_quality_audit`, when a profile sets `echo_check=True`, a target paragraph (>= 50 chars) whose normalised text equals its source fails. zh-tw sets it False so its output cannot change.
C. Length ratio: measure English→Vietnamese ratios on *Subtract* (Leidy Klotz, non-fiction narrative; local copy `runs/subtract/subtract.epub`, gitignored, copyrighted so never committed) and cross-check against the existing Alice fixture (fiction). *Subtract* extracts as 3 huge multi-chapter items (BUG-001), so use hand-picked excerpts (Introduction, chapters 1-2) as the Alice fixture does, not whole items; then set `min_length_ratio` in `register_hints.vi.json` per register (not a profile field; the existing mechanism already reads it).
D. Mixed text (a single "Nguyễn" in an English paragraph): the plan says the sibling must be Vietnamese, not merely contain a Vietnamese word. Proposed rule, to be confirmed in the Advise call: for paragraphs >= 50 chars, count as Vietnamese only if distinctive letters or function words make up a minimum share of the words (threshold from labelled data); below 50 chars keep the any-match rule.

## Definition of Done

- [x] Labelled sample set (>= 40 items: vi, fr, pt, en, mixed, short) committed as test data, with the source of each sample stated. Tests written first and seen red. **Done:** 43 samples, `test/data/vi_detector_samples.json`; tests written first (25 red).
- [x] `vi` `is_target_text`: true for vi samples incl. "Xin chào", false for en/fr/pt samples incl. "café", "crêpe", "façade". Mixed-text rule pinned by tests as decided in D. **Done:** rule in 3.3 Advise outcome; `test/test_vi_detector_phase3.py`, 71 tests.
- [x] Echo check: audit fails an identical-to-source `tgt-vi` paragraph (>= 50 chars) and passes a real translation; zh-tw golden failure strings unchanged. **Done:** all profiles, no field (DECISION-011); `test/test_echo_check_phase3.py`, 8 tests; zh-tw golden strings unchanged.
- [x] `min_length_ratio` for each `vi` register set from measured data, with the measurement recorded in this doc; audit fails a truncated Vietnamese paragraph and passes the fixture. **Done:** flat 0.60 (DECISION-012); `test/test_vi_length_ratio_phase3.py`; measurements in 3.2 results.
- [x] Coverage audit: fails a chapter left untranslated on purpose and passes a translated one (plan "done when"), asserted on the Vietnamese frozen fixture. **Done:** on the `vi` frozen fixture the coverage audit fails only the 10 chapters left untranslated (h-3 to h-12) and passes the title page and chapters 1-2 (snapshot `audit_output`, identical before and after Phase 3); the tiny-EPUB pair is also in `test_lang_profile_vi.py` and the new tests.
- [x] Advise called before changing `is_target_text` and before setting the ratio/echo rules (CLAUDE.md triggers); calls logged in `docs/eagd-log.md`. **Done:** three calls logged: detector (opus), echo (opus), ratio (Fable, one-time user override).
- [x] Regression: all existing tests untouched and green; zh-tw frozen snapshot identical to the `bb0eb35` baseline; `vi` fixture snapshot differs only where intended and the diff is explained here. **Done:** 626 -> 634 passed, 269 skipped; existing-test gate empty; zh-tw and vi snapshots identical to `bb0eb35` / `baseline_vi_phase2.json`, so there is no vi diff to explain.
- [x] CI green (ubuntu 3.10/3.12, windows 3.12; run 43033595597 on PR #7). Ledger updated; tradeoffs to `docs/DECISIONS.md`, defects to `docs/BUGS.md`.

## Test Plan

- Ordinary test-first (no external oracle for `vi`): `test/test_lang_profile_vi_detector.py` (samples), additions in a new file for echo/ratio audit cases, built on tiny in-memory EPUBs like `test_zh_tw_phase2_characterization.py` does.
- zh-tw guard: `pytest -q` including the Phase 1/2 golden tests, unmodified.
- Commands: `pytest -q`; `git diff --diff-filter=MDRT --name-only 71dc493 -- test/ conftest.py requirements-dev.txt requirements.txt .github/` must list nothing; frozen-fixture `build.py` + `snapshot.py` for zh-tw (identical) and `vi` (explained diff).

## Sub-tasks

- [x] 3.1 User approved this DoD and Test Plan (2026-11-11; open questions answered)
- [x] 3.2 Labelled sample set and vi length ratios (results under "3.2 results" below)
- [x] 3.3 Advise call on detector + mixed-text rule, logged (answer under "3.3 Advise outcome")
- [x] 3.4 Red tests, then implement detector (A, D); results under "3.4 results"
- [x] 3.5 Echo check (B), for every profile with no profile field (Advise + user, DECISION-011); results under "3.5 results"
- [x] 3.6 Ratio per register (C), after an Advise call; results under "3.6 results"
- [x] 3.7 Coverage-audit pair on the fixture; DoD verified except CI (needs a PR); ledger updated

## Open questions for you

1. ~~Echo check field or always on?~~ First answered: a profile field. Superseded 2026-11-11 after the 3.5 Advise call: runs for every profile, no field (DECISION-011).
2. ~~Second real source?~~ Answered: *Subtract* is the test book from here on (Phase 3 ratio measurement and the Phase 5 full run). The Alice frozen fixtures, `runs/alice/` and all their tests/baselines stay unchanged as the committed regression samples.
3. ~~Mixed-text rule?~~ Answered (user, 2026-11-11): the share rule (option B). For paragraphs >= 50 chars, a minimum share of words must carry a distinctive letter or be a listed function word; cutoff set from labelled data and *Subtract*, not guessed. Shorter paragraphs keep the any-match rule.

## 3.2 results (2026-11-11)

**Samples:** `test/data/vi_detector_samples.json`, 43 items (vi long/short/no-distinctive-letter, en long/short/with French accents, fr, pt, mixed English+Vietnamese name, mixed Vietnamese+English term, empty/ASCII, NFD input). Written by the project, not native-reviewed; provenance is in the file. `expected` is the intended result under DECISION-010 plus the share rule.

**Findings that shape 3.3/3.4**
1. Word share (words containing a distinctive letter / all words), paragraphs >= 50 chars: real Vietnamese 0.45-0.79 (11 paragraphs, incl. 5 Alice); English, French, Portuguese 0.00; English with a Vietnamese name 0.06-0.17. A cutoff near 0.25 separates them with wide margin on this small set. Final value to be fixed in the Advise call (3.3).
2. The function-word list matters only for short text. Common function words in the DECISION-010 example (của, những, được) already contain distinctive letters; only words such as và, không, tôi, xin, chào, em need the list. Real 50+ char Vietnamese always has tone-stacked letters.
3. *Subtract* comes from `pdftohtml`: paragraphs are split at page breaks mid-sentence and carry double spaces (e.g. spine item 2, elements 40-42). Whole-book pairing by paragraph would be noisy; not a Phase 3 problem, relevant to Phase 5 together with BUG-001.

**Length ratios (vi chars / en chars, paragraphs >= 50 chars, hand-written translations):**

| Source | n | min | mean | max |
|---|---|---|---|---|
| Alice (fixture, fiction) | 8 | 0.80 | 0.87 | 0.94 |
| *Subtract* (excerpt, non-fiction; Introduction paragraphs 35, 38, 39, 43, 45, 46, 57, 58) | 8 | 0.91 | 1.01 | 1.16 |

The Subtract text and translations stay in `runs/subtract/` (gitignored, copyrighted); only these numbers are committed (`runs/subtract/measure_ratio.py` reproduces them locally). zh-tw's 0.22 default is far below both: a Vietnamese paragraph at 0.3 would pass today. Threshold choice is for 3.6. Caveat: n=16, one translator.

## 3.3 Advise outcome (2026-11-11, opus, logged in `docs/eagd-log.md`)

Rule for `vi` `is_target_text` (replaces my 0.25-of-all-words leaning; changed: yes):
1. NFC-normalise, tokenise with `\w+`; skip all-digit tokens.
2. Count only tokens with `tok[0].islower()` (proper nouns are what fooled both directions). If the text has no lowercase-initial token (Title Case headings), count every token.
3. A token matches when it has a distinctive letter or is in the function-word list: và, không, tôi, xin, chào, các, này. Not `em` (Portuguese "em", English "'em"), not `là` (French), not `anh`.
4. Text >= 50 chars: true when matches / counted tokens >= 0.25. Text < 50 chars: true when at least one token matches. The 50 matches `LEGACY_ENGLISH_MIN_LENGTH` and the audit's own length cutoff.

Why it matters beyond mixed text: `bilingual_coverage_audit._source_nodes_requiring_coverage` and `translation_quality_audit` (inline-bilingual exemption) call `is_target_text` on the English source node. With any-match, a source paragraph that merely contains a Vietnamese name is skipped from coverage. Needs tests: short English sources with Vietnamese names and no `tgt` sibling must be flagged.

Still to do from the advice: the 0.25 cutoff is checked against 11 real paragraphs by one translator; confirm on *Subtract* excerpts (3.4). `min_length_ratio` stays a separate Advise call in 3.6 (data floor 0.80, suggested 0.5-0.6). An exact-equality echo check (B) must be an actual audit check, not left to Grade.

## 3.4 results (2026-11-11)

- `test/test_vi_detector_phase3.py` written first: 25 of 71 tests red on the Phase 2 detector. `_vi_is_target_text` in `scripts/lang_profile.py` rewritten per the 3.3 rule. Suite: 618 passed, 269 skipped (547 + 71 new). No existing test file changed (`git diff --diff-filter=MDRT --name-only 71dc493 -- test/ ...` is empty); the Phase 2 detector tests pass untouched.
- Cutoff check on *Subtract*: the 8 hand-translated excerpt paragraphs score 0.59-0.68 (lowercase-token share), above the 0.45 floor seen before and far from 0.25. The cutoff stands.
- Frozen-fixture snapshots: zh-tw identical to the `bb0eb35` baseline; `vi` identical to `baseline_vi_phase2.json` (the Alice excerpt has no short English source with a Vietnamese name, so nothing moves).
- Behaviour change worth knowing: `bilingual_coverage_audit.audit()` returns only `(ok, failures)`; short untranslated English (< 50 chars) still goes amber (warning) by design. The change is that a source containing a Vietnamese name is no longer silently exempt. Tests use `_audit_with_warnings` for that.
- Known remaining weak spots (not fixed): n=11+8 real Vietnamese paragraphs, one translator; a short English sentence whose lowercase words include a function word from the list is a false positive (e.g. "xin" as a typo); lowercase-initial Vietnamese names written without capitals are counted normally.

## 3.5 results (2026-11-11)

- Advise (opus, logged): add the check, no field, every profile; exact equality, hard failure; skip headings, sources < 50 chars and `source_only` exceptions. The user chose this over the earlier field decision (DECISION-011).
- `test/test_echo_check_phase3.py` (8 tests, 5 red first), then the check in `translation_quality_audit._audit_findings`. Correction to the advice: `_clean` collapses whitespace but does not NFC-normalise, so the comparison normalises explicitly (a decomposed-Unicode echo test failed before that). Suite 626 passed, 269 skipped; existing tests untouched (gate empty); zh-tw and vi frozen snapshots still identical to their baselines.
- Not checked: `<pre>`/code nodes tagged `src` in a real book (the advice raised it); the exception match is exact on the cleaned text, like the existing source-only branch.

## 3.6 results (2026-11-11)

- Advise (Fable, one-time user override, logged): flat 0.60 for all three vi registers, provisional (DECISION-012); fallback left and logged as BUG-002; standalone CLI and `register_override` gaps logged as BUG-003 and BUG-004; amber margins unchanged. Deviation from my leaning (0.55/0.55/0.60): accepted.
- `test/test_vi_length_ratio_phase3.py` (8 tests, 6 red first), then `min_length_ratio: 0.6` added to the three registers in `assets/register_hints.vi.json`; no code change. Suite 634 passed, 269 skipped; existing tests untouched (gate empty); zh-tw and vi frozen snapshots identical to their baselines (the fixture glossary has no register, so it does not exercise the ratio).
- Advice claims verified in the code before acting: invented registers are allowed (`glossary.py:94`), the CLI passes no profile, the audit ignores `register_override`.
