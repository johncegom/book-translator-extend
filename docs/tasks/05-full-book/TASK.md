# Task: Phase 5 — One full book (*Subtract* by Leidy Klotz, English to Vietnamese)

Status: in progress. DoD and Test Plan approved by the user 2026-11-12 (with the answers at the end; the quota check is the `quota-guard` mod, built in 5.2).

Depends on: Phase 4 (merged; PRs #9 and #11). Plan: `docs/plans/2026-11-11-vietnamese-language-profile.md` ("Phase 5: run the whole pipeline on the test book, open the result in a reader, check one early and one late chapter; done when all four audits pass and the read-back looks right"). The book is copyrighted and local only (`runs/subtract/`, gitignored). The Alice fixtures stay as the committed regression samples.

## What Phase 5 must show

That the `vi` pipeline works on a real, full-length book, end to end, through the skill: extract, glossary, style sample, parallel translation, assemble, four audits, human read-back. Also the first real data to check the thresholds that Phases 3 and 4 set from about 19 hand-written paragraphs (0.25 detector share, 0.60 length ratio, 50-character rules).

## Facts at the start of Phase 5 (from the Phase 3 and 4 extractions of `runs/subtract/subtract.epub`)

1. After the BUG-001 split the book has **23 spine items**; 20 are `translate`, about **460,000 source characters** in total (roughly 115k input tokens; the Vietnamese output is larger in tokens than the English). Largest: chapter 4 at 84,236 characters, `Notes` at 77,616, chapter 7 at 73,696.
2. `Notes` (item 19, 77,616 characters) is classed as `body` / `translate`. Endnotes are citations, so translating them costs about a sixth of the whole run for little reader value. `Image Credits`, the "Thank you for buying this" page, `Document Outline` and `Title Page`/`Copyright Notice`/`Dedication` (items 2 to 4, tiny) are also `translate`; the two `PART I/II` dividers are `source_only`.
3. The text came from `pdftohtml`: paragraphs are cut in the middle of a sentence at page breaks (Phase 3 finding). A translator that sees each fragment alone may translate a half sentence; the paragraph pairing stays one to one, so the audits will not notice.
4. Known and unverified from Phase 4: `patch_toc_ncx` matches entries to NCX points by file name, so the NCX labels of the several entries of one split file may be wrong (check in the output); BUG-004 (`register_override` does not reach the audit threshold) and BUG-005 (coverage failure wording says "zh") are open and cosmetic or inapplicable here.
5. `SKILL.md` 1.4.0 expects to be installed at `~/.claude/skills/book-translator/` (its commands use that path). Nothing in this repo installs it.
6. EAGD (CLAUDE.md): Grade runs once per finished chapter batch (haiku, rubric a to e), Dream after a Grade pass writes `docs/eagd-lessons.md` (haiku). Advise is required before any change to a detector rule or threshold.

## Proposed scope and order

A0. **Quota guard (built before the pre-flight).** `tools/quota-guard/` mod plus install scripts and tests; the user installs it in the session that runs the translation.

A. **Pre-flight (no translation cost).** Extract (already done, redo from the committed code); review the 23 items and fix the classification by editing `manifest.json` (not code): `Notes` to `source_only` if the user agrees (open question 2); confirm `PART` pages and front matter. Write `state.json` with `target_lang: vi` through `state.init_state`. Fresh `glossary.json` for the `vi` profile (register chosen from the three vi registers; check that `resolve_register` matches, BUG-002 is fixed so a miss now gets 0.60 anyway).

B. **Style sample and tone gate (SKILL.md Steps 4 and 5).** Translate the first real chapter (the Introduction, 29,722 characters) with Opus as the anchor; the user reads it and confirms the tone before the fan-out. This is the human gate the skill already has; it costs one chapter if rejected.

C. **Pilot, then fan-out (Steps 6).** Pilot two small items first (`Takeaways`, 3,266, and chapter 6, 10,095) to see marker alignment, retries and the real length ratios. Then the rest in batches of 5 with Sonnet, the largest chapters (4, 7, 8) last. Retry once, escalate to Opus once, then `failed` (existing discipline). **Stop rule:** if more than 3 items need escalation in the first 10, stop and report before spending more.

D. **Grade and Dream.** After each finished batch, one Grade call (haiku, rubric a to e from CLAUDE.md) on the finished output only. Full rerun on failure unless Grade names one bounded paragraph. After the last Grade pass, one Dream call; lessons go to `docs/eagd-lessons.md`.

E. **Assemble and audit (Steps 7 and 8).** `assemble.py`, then `audit_suite`: structural, bilingual_coverage, translation_quality, href_resolve, all with the `vi` profile read from `state.json`.

F. **Recalibration from real data.** Compute, over every translated paragraph: the vi/en length ratio distribution (min, 1st and 5th percentile, median), the share of paragraphs where `is_target_text` is false, and the number of audit warnings (amber). If the data says 0.60 or 0.25 is wrong, change it only after an Advise call (CLAUDE.md trigger 2) and a DECISIONS entry; otherwise record "confirmed on n paragraphs". Separately, report the mid-sentence-fragment problem with a count of translated paragraphs that end without terminal punctuation.

G. **Human read-back.** The user opens the output EPUB in a reader and checks one early and one late chapter (plus the table of contents and one place where a chapter was split). I will list what to look at; I cannot judge Vietnamese prose quality as the final authority.

H. **Fresh-session check (moved here from Phase 4).** The user runs the skill once in a fresh Claude Code session with `vi` and reports whether anything needed a manual fix. See open question 1 for how this combines with the run itself.

## Definition of Done (draft)

- [x] `quota-guard` mod committed with tests (`claude plugin test tools/quota-guard`, 6 pass), validated, install and uninstall smoke-tested in an isolated config dir; installed by the user in the translation session.
- [x] Pre-flight recorded: item list with the final classification of every item; `state.json` has `target_lang: vi`; glossary resolves to a vi register.
- [x] Style sample approved by the user (tone gate).
- [x] Every `translate` item is `done` in `state.json`, or listed here with a reason (`failed`, `aup_refused`) and the user's decision on each. No item `pending` or `in_progress`.
- [x] Grade run for every batch; its findings are explained in Results (rubric and detector artefacts, no translation defect); Dream run (`docs/eagd-lessons.md`). NOTE: no batch was rerun, the rubric was tightened instead (or a failed batch was rerun and passed); Dream run once and `docs/eagd-lessons.md` written.
- [x] (user accepted, DECISION-015) `assemble.py` succeeds; `audit_suite` shows structural and href PASS, and one line each in bilingual_coverage and translation_quality (the two false positives listed in Results). `assemble.py` needed the BUG-006 fix (PR #15) first. 4 of 4 PASS (amber WARN is allowed only if each warning is listed here and judged harmless).
- [x] Recalibration table filled in from the real data (ratio distribution, detector false-negative count, warnings). Any threshold change has an Advise log row and a DECISIONS entry; "no change" is stated with n.
- [ ] User read-back done on one early and one late chapter, the table of contents and a split chapter boundary; findings recorded (what was wrong, what was fine).
- [ ] Fresh-session check done by the user, or explicitly waived by them in writing in this doc.
- [x] Copyright guard (`git ls-files runs` is 0; no epub of the book; no excerpts in the docs): `git ls-files` lists nothing under `runs/`, no `.epub` of the book, and no committed excerpt longer than a sentence from the book or its translation.
- [ ] Bugs found are in `docs/BUGS.md`; tradeoffs in `docs/DECISIONS.md`; a lesson that passes the generalisation test in `docs/RETRO.md`; Alice and zh-tw tests unchanged (`pytest -q` green, existing-test gate command empty); CI green; ledger updated with PR links.

## Test Plan

Phase 5 is a run, so the checks are commands on the output, plus the existing suite:

0. `claude plugin validate tools/quota-guard` and `claude plugin test tools/quota-guard` pass (these TypeScript tests are not in CI; CI runs pytest only).
1. `pytest -q` stays green before and after (no code change is planned; any fix found gets its own test-first change and PR).
2. Pre-flight: `python scripts/extract_epub.py runs/subtract/subtract.epub --out runs/subtract/out` then a script prints id, role, strategy, characters for all items (saved in the results section, numbers only).
3. After translation: `python scripts/audit_suite.py --source runs/subtract/subtract.epub --output <out.epub> --book-dir runs/subtract/out/subtract`, expecting `4 PASS`.
4. Measurement script `docs/tasks/05-full-book/measure.py` (committed; reads the gitignored run and prints only aggregate numbers, never text): ratio percentiles, `is_target_text` false count, paragraphs with no terminal punctuation, items per status.
5. Copyright guard: `git ls-files runs | wc -l` is 0 and `git ls-files | grep -i -E "subtract|klotz"` shows only docs and the measurement script.
6. Frozen snapshots and the existing-test gate from Phase 3 and 4 still hold.

## Sub-tasks

- [x] 5.1 User approved this DoD and Test Plan and answered the open questions (2026-11-12)
- [x] 5.1b `quota-guard` mod built, tested, install scripts smoke-tested in an isolated config dir (not yet installed in the user's Claude; the user runs the script)
- [x] 5.2 Pre-flight (A): extract, classification, state, skill install done 2026-11-12 (glossary is left to the fresh session, SKILL.md Step 3, because it is an LLM call over the whole book); recorded in Results
- [x] 5.3 Style sample and tone gate (B): approved 2026-11-12 on round 2 (round 1 re-translated with anti-AI-tone instructions)
- [x] 5.4 Pilot, then fan-out with Grade per batch (C, D): 16 of 16 done, 0 retries, 0 escalations; Grade run on the pilot and on batches 1 to 3 (findings below)
- [x] 5.4b BUG-006 found by the first audit, fixed in PR #15 (user chose the code fix)
- [~] 5.5 Assemble and four audits (E): assembled; 2 of 4 PASS, see Results (not yet 4 of 4)
- [~] 5.6 Recalibration with `measure.py` (F): numbers recorded, Advise done, no threshold change; waiting for the user's call on 4 of 4
- [ ] 5.7 User read-back and fresh-session check (G, H)
- [ ] 5.8 Retro, ledger, PR merges, verify DoD (Dream done; bugs and decisions logged)

## Risks

- **Cost and quota.** About 460k source characters through Sonnet (about 380k if `Notes` is skipped) plus an Opus anchor chapter and possible Opus escalations, plus Haiku Grade calls. This is the user's subscription quota; the stop rule above limits a bad start.
- **One call per item.** The largest item (84k characters) may not fit one call's output, or may misalign markers. First response: the existing retry and escalation. If it still fails, the fix is chunking inside an item, which is new code (own bug, own PR) and not part of this plan.
- **Copyrighted text.** Source and translation stay under gitignored `runs/`. Nothing quoted in commits, PRs or docs beyond numbers.
- **Evaluating Vietnamese.** The audits are structural; they cannot say the prose is good. The read-back is by the user, and the Grade rubric checks structure, not fluency.
- **Thresholds from tiny data.** If the real distribution disagrees, changes need an Advise call and a decision entry; do not tune to make a failing audit pass.

## Open questions for you

1. **Who drives the run.** (a) Pre-flight here; you start a fresh Claude Code session with the skill installed and it runs steps 3 to 8, which doubles as the fresh-session check, and I come back for the audits, measurement and write-up. (b) I drive the whole run from this session with subagents, and you do a short fresh-session check on a small item afterwards. I lean (a): it is the real user path and the check is not wasted, but it needs your session time. (b) is faster to my side and a shorter fresh-session test.
2. **Skill install.** The skill needs to sit at `~/.claude/skills/book-translator/`. Do you want a symlink or copy from this repo made (a change in your home directory, which I will not do without your say-so), or do you already have a copy from upstream there? If it is upstream's 1.3.0 it would run the old zh-tw-only instructions.
3. **`Notes` (77,616 characters) and the small tail pages.** Skip translating them (`source_only`)? I lean yes for `Notes`, and for `Image Credits`, "Thank you for buying this" and `Document Outline`; translate the rest.
4. **Budget and stop rule.** Is the "stop if more than 3 of the first 10 items need escalation" rule right, and is there a quota ceiling at which you want me to pause and ask?
5. **Reader for the read-back.** Which reader will you open the EPUB in (Calibre, Apple Books, an e-ink device)? Some readers ignore the bilingual styling; I would rather know before I tell you what to look for.

## Answers so far (user, 2026-11-12)

1. **Who drives the run:** (a). Pre-flight here; the user runs the skill in a fresh Claude Code session (this is also the fresh-session check); I do the audits, measurement and write-up afterwards.
2. **Skill install:** copy this repo's skill into `~/.claude/skills/book-translator/` (checked: no copy exists there today, so nothing is overwritten). Done in 5.2, after approval; `runs/` and `.git` are not copied.
3. **Tail pages:** `Notes`, `Image Credits`, "Thank you for buying this" and `Document Outline` become `source_only` in the pre-flight; the rest translate.
4. **Stop rule accepted** (stop and report if more than 3 of the first 10 items need Opus escalation). **Quota ceiling: 85% of the 5-hour window, enforced automatically** by a small Claude mod, `tools/quota-guard/` (the user's `usage-band` mod only displays the figure, so a new mod reads `$.session.usage()` itself): it refuses new `Agent` calls while the 5-hour window is at or above the threshold (default 85) with the percent and reset time in the message, toasts once when crossed, releases by itself after the reset, and fails open if no figure exists. `install.ps1` / `install.sh` install it into the user's Claude (user scope). The assistant still reports after every batch of 5. The old `agent-orch` gate stays unused.
5. **Reader:** Kindle (probably Send to Kindle, which converts the EPUB). Check in the read-back that the source and Vietnamese paragraphs both show in order, that Vietnamese diacritics render, and that the table of contents entries for the split chapters work. If Kindle's conversion drops the styling, that is a reader limit to record, not a pipeline failure.

## Results

### 5.2 Pre-flight (2026-11-12, numbers only)

- Re-extracted from committed code: 23 spine items. Final classification: 16 `translate` (381,561 source characters), 7 `source_only` (`Title Page` file item_001, both `PART` dividers item_006 and item_011, `Image Credits` item_018, `Notes` item_019, "Thank you for buying this" item_021, `Document Outline` item_023). Edited in `manifest.json` (spine and the compat `chapters[]` list, now 16 entries), no code change.
- Earlier "20 translate" in Facts counted the four items now set to `source_only`; the real work is 16 items.
- `state.json` written via `state.init_state(..., 'vi')`: `target_lang: vi`, all items `pending`, `glossary_built: false`, `style_confirmed: false`.
- Skill copied to `~/.claude/skills/book-translator/` (SKILL.md, scripts/, assets/, LICENSE, requirements.txt; no `runs/`, `.git`, tests). It matches the repo at `0eef0dc`.
- `pytest -q`: 668 passed, 269 skipped (unchanged).
- Glossary: not built here. The fresh session builds it (Step 3) with the `vi` profile.

### 5.3 to 5.6 Run (2026-11-12, numbers only)

- **Run shape:** glossary 49 characters / 29 places / 44 terms / 16 chapter titles, built by a Sonnet subagent that read two items in full and skimmed the rest (a weaker glossary than the skill intends; "more" and similar common words became keys). Introduction by Opus, the other 15 items by Sonnet in a pilot of 2 and three batches of 5, 5 and 3. Every item passed `validate_translation` on the first try: 0 retries, 0 Opus escalations (stop rule never near). Anti-AI-tone instructions (from the `sound-human` skill, adapted to Vietnamese translation) live in `custom_instructions.txt` of the run folder.
- **Audits, after the BUG-006 fix:** structural PASS, href_resolve PASS, bilingual_coverage FAIL (1 line), translation_quality FAIL (1 line); 24 output lines incl. stderr warnings. Before the fix: about 1,200 lines (99% from `source_only` items inside split files).
  - The coverage line is the detector false negative below. The quality line is the 0.57 length ratio below.
- **`measure.py` over 1,461 translated paragraphs (1,268 of 50+ source characters):** length ratio min 0.571, p1 0.691, p5 0.801, median 0.984, 1 below 0.60. Detector share on the translations: min 0.231, p1 0.395, p5 0.492, median 0.627; `is_target_text` false for 1 paragraph of 50+ (share 0.231) and 64 of the shorter ones. Detector share over the English source: max 0.000, 0 of 1,268 at or above 0.17. Paragraphs of 50+ without terminal punctuation: 202 in the translation, 198 in the source (the page-break fragments of fact 3; the translator kept them as fragments).
- **Recalibration verdict:** 0.60 length ratio and 0.25 detector share confirmed on n = 1,268, no change. Advise (opus, logged) said keep 0.25: the one false negative is a correct 53-character sentence of short Latin-1-accent syllables (3 of 13 counted tokens match); lowering the cutoff later is possible because the English side is empty above 0, but it needs its own change with an Advise call and a DECISIONS entry, not tuning to this paragraph. The 0.57 paragraph is a correct, concise translation; neither paragraph was reworded to pass.
- **Grade (haiku) findings, all judged not translation defects:** (b) failed only on list labels like "1." (rubric tightened to 50+ characters after the pilot); (c) glossary misses: the Potbelly Hill misses are the Vietnamese name used without the first-mention gloss in parentheses, and the Anthropocene misses are the same shape. The glossary value carries a gloss meant for the first mention; the check wants it every time. (a) one item hit the detector false negative; (d) one item hit the 0.57 paragraph.
