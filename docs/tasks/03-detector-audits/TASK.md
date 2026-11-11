# Task: Phase 3 — Detector and audits

Test book: *Subtract* (user, 2026-11-11). Alice fixtures are kept as-is.

Status: approved 2026-11-11; in progress (3.2).

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

## Definition of Done (draft)

- [ ] Labelled sample set (>= 40 items: vi, fr, pt, en, mixed, short) committed as test data, with the source of each sample stated. Tests written first and seen red.
- [ ] `vi` `is_target_text`: true for vi samples incl. "Xin chào", false for en/fr/pt samples incl. "café", "crêpe", "façade". Mixed-text rule pinned by tests as decided in D.
- [ ] Echo check: audit fails an identical-to-source `tgt-vi` paragraph (>= 50 chars) and passes a real translation; zh-tw golden failure strings unchanged.
- [ ] `min_length_ratio` for each `vi` register set from measured data, with the measurement recorded in this doc; audit fails a truncated Vietnamese paragraph and passes the fixture.
- [ ] Coverage audit: fails a chapter left untranslated on purpose and passes a translated one (plan "done when"), asserted on the Vietnamese frozen fixture.
- [ ] Advise called before changing `is_target_text` and before setting the ratio/echo rules (CLAUDE.md triggers); calls logged in `docs/eagd-log.md`.
- [ ] Regression: all existing tests untouched and green; zh-tw frozen snapshot identical to the `bb0eb35` baseline; `vi` fixture snapshot differs only where intended and the diff is explained here.
- [ ] CI green (ubuntu 3.10/3.12, windows 3.12). Ledger updated; tradeoffs to `docs/DECISIONS.md`, defects to `docs/BUGS.md`.

## Test Plan

- Ordinary test-first (no external oracle for `vi`): `test/test_lang_profile_vi_detector.py` (samples), additions in a new file for echo/ratio audit cases, built on tiny in-memory EPUBs like `test_zh_tw_phase2_characterization.py` does.
- zh-tw guard: `pytest -q` including the Phase 1/2 golden tests, unmodified.
- Commands: `pytest -q`; `git diff --diff-filter=MDRT --name-only 71dc493 -- test/ conftest.py requirements-dev.txt requirements.txt .github/` must list nothing; frozen-fixture `build.py` + `snapshot.py` for zh-tw (identical) and `vi` (explained diff).

## Sub-tasks

- [x] 3.1 User approved this DoD and Test Plan (2026-11-11; open questions answered)
- [x] 3.2 Labelled sample set and vi length ratios (results under "3.2 results" below)
- [ ] 3.3 Advise call on detector + mixed-text rule; log it
- [ ] 3.4 Red tests, then implement detector (A, D)
- [ ] 3.5 Echo check (B), with the profile switch
- [ ] 3.6 Ratio per register (C); Advise call if it changes a threshold
- [ ] 3.7 Coverage-audit pair on the fixture; verify DoD; ledger

## Open questions for you

1. ~~Echo check field or always on?~~ Answered (user, 2026-11-11): a profile field, `echo_check` (zh-tw False, vi True; 18 fields).
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
