# Task: Phase 2 — Vietnamese profile (`vi`)

Status: DRAFT 2026-11-11. All five open questions decided. DoD awaiting the user's final approval. Nothing is implemented. Call Advise (once, for the new field set) before changing `LanguageProfile`.

Depends on: Phase 1 (merged, PR #4). Plan: `docs/plans/2026-11-11-vietnamese-language-profile.md`. Decisions to honour: DECISION-002 (keep the `chapter_titles_zh` key), DECISION-006 (tighten `resolve_profile`), DECISION-007 (profile shape).

## What Phase 2 must deliver

A registered `vi` profile so that, with `target_lang: "vi"` in `state.json`, the subagent path builds a Vietnamese prompt, assembles a nav and OPF labelled in Vietnamese, inserts paragraphs with class `tgt-vi`, and the two audits judge Vietnamese siblings sensibly. Phase 3 hardens the detector and the audits (echo check, length ratio, short paragraphs); Phase 4 does `SKILL.md`; Phase 5 runs a whole book.

## Findings that shape the scope (from reading the code at `dac59fe`)

1. **`assets/register_hints.json` is Chinese-only.** All three registers carry Chinese `prefer`/`avoid` lists and `subagent_rules` such as "Plain everyday Chinese (跑/看/說 not 奔馳…)", "NO 中英並列", "「中文（English）」". `resolve_register_rules` injects these into the subagent prompt, and the glossary prompt shows the same block to the glossary-building model. A `vi` run on a literary book (Alice) would receive Chinese style rules. This is the largest item in the phase and was not in the original plan.
2. **`glossary.py` `GLOSSARY_PROMPT` is zh-specific** (lines 62–83: "台灣繁體中文 if target is zh-tw", transliteration advice for names, the `第一章` / `第一部` title examples, `翻譯腔`). It was allow-listed in Phase 1.
3. **`dispatch.GENERIC_SUBAGENT_RULES`** (fallback rules when no register matches) includes "Avoid 翻譯腔." and was allow-listed in Phase 1.
4. **`resolve_profile` falls back silently to zh-tw** for any unregistered code (DECISION-006). Once `vi` exists, a typo such as `vn` would silently produce Chinese output.
5. **The detector for `vi` cannot reuse a script test.** The plan's rule: a paragraph counts as Vietnamese when it contains Vietnamese-only letters (ă â đ ê ô ơ ư or tone-marked vowels). Phase 2 needs a working `is_target_text` to construct the profile and to keep assemble from misclassifying English; Phase 3 pins the thresholds, the echo check and the audit behaviour.
6. **Out of scope and unchanged:** the ollama/omlx/cloud paths, `translate_chapter_cli.py`, `offline_postprocess.py` (opencc), `build_terms.py` (decide below), the Simplified-Chinese gate (a no-op for `vi` by construction, see DoD).

## Decisions on the open questions (user, 2026-11-11)

1. **Register hints: decided, option (a).** A second file `assets/register_hints.vi.json` plus a profile field naming it. The zh-tw file stays untouched.
2. **Vietnamese wording: decided 2026-11-11.** Title Page = `Trang tiêu đề` (user, also used on the FTU WPS page); Introduction = `Lời nói đầu` (user's choice); the other terms are accepted as a working set, "temporary use", and may be revised later. Roman (`Phần I`) and Arabic (`Phần 1`) numbering are both acceptable; the tables keep Roman to match the English source keys. Sources are in the provenance table below.
3. **Names: decided.** Keep the original spelling of personal and place names; no Vietnamese forms (no Luân Đôn / Pa-ri) unless the glossary supplies one.
4. **`build_terms.py`: out of scope for Phase 2 (accepted).** It is an optional term-review step whose OpenCC/Simplified check is mandatory and zh-only. Phase 4 must make `SKILL.md` say the step is not available for `vi` and must not let a Vietnamese run hit the OpenCC `RuntimeError`.
5. **Unknown codes: decided.** `assemble` and `audit_suite` (and the `state.json` reader) raise a clear error for a `target_lang` with no profile (e.g. `vn`). `build_subagent_prompt` keeps the pinned fallback for `zh-cn`, `en`, `ja`, `ko`.

## Draft Vietnamese data (for your review)

| Field | Draft value |
|---|---|
| `code` | `vi` |
| `long_name` | `Tiếng Việt` |
| `html_lang` | `vi` |
| `target_class` | `tgt-vi` |
| `footnote_label` | `Chú thích {n}` |
| `bilingual_edition_label` | `Song ngữ Anh–Việt` |
| `aup_refused_notice` | `Chương này bị từ chối dịch do chính sách của LLM; giữ nguyên bản gốc, chưa dịch` |
| `prefix_labels` | `praise for ` → `Lời khen ngợi`; `advance praise for ` → `Lời khen ngợi`; `also by ` → `Cùng tác giả` |
| `contents_labels` | Contents → Mục lục; Cover → Bìa; Title Page → Trang tiêu đề; Copyright → Bản quyền; Dedication → Lời đề tặng; PART I → Phần I; PART II → Phần II; Acknowledgments → Lời cảm ơn; Notes → Chú thích; About the Author → Về tác giả |
| `structural_labels` | Contents → Mục lục; Introduction → Lời nói đầu; PART I → Phần I; PART II → Phần II; Acknowledgments → Lời cảm ơn; Notes → Chú thích; About the Author → Về tác giả; "What’s next on your reading list?" / "What's next on your reading list?" → "Bạn sẽ đọc gì tiếp theo?"; "Discover your next great read!" → "Khám phá cuốn sách hay tiếp theo của bạn!"; "Get personalized book picks and up-to-date news about this author." → "Nhận gợi ý sách dành riêng cho bạn và tin tức mới nhất về tác giả này."; "Sign up now." → "Đăng ký ngay."; "GO TO NOTE REFERENCE IN TEXT" → "QUAY LẠI VỊ TRÍ GHI CHÚ TRONG VĂN BẢN" |
| `prompt_rules` (no braces) | "Vietnamese rule: If the target is Tiếng Việt, write standard Vietnamese with full diacritics in Unicode NFC. Keep the original spelling of personal names and place names unless the glossary gives a Vietnamese form. Prefer natural, idiomatic Vietnamese over word-for-word rendering. Use Vietnamese punctuation and quotation marks consistently." |
| `default_custom_instructions` | "Translate for a Vietnamese general reader. Keep sentences natural; avoid translationese (câu dịch word-for-word)." |
| `is_target_text` | `True` when the text contains a Vietnamese-only letter (ă â đ ê ô ơ ư, upper or lower case, or any tone-marked vowel) |

### Provenance of the label wording

| English | Vietnamese | Basis |
|---|---|---|
| Title Page | Trang tiêu đề | user instruction; also on fwps.ftu.edu.vn/quy-dinh (the national book standard TCVN 8694:2011 says "trang tên sách"; the user's choice wins) |
| Acknowledgments | Lời cảm ơn | fwps.ftu.edu.vn/quy-dinh |
| Notes | Chú thích | fwps.ftu.edu.vn/quy-dinh ("chú thích cuối trang") |
| Contents | Mục lục | TCVN 8694:2011 and general usage |
| Introduction | Lời nói đầu | user's choice (the sampled Alpha Books EPUB uses "Mở đầu"; not adopted) |
| Cover, Copyright, Dedication, About the Author, Part | Bìa, Bản quyền, Lời đề tặng, Về tác giả, Phần | author's knowledge, accepted as temporary; unsourced |

Not adopted: `Kết luận` and `Nhà Xuất bản` (no matching English keys in the current tables).

## Definition of Done (draft)

Profile and data
- [ ] `vi` is registered; `get_profile("vi")` returns it, `get_profile("VI")` too. Profiles are compared by `.code`.
- [ ] The Vietnamese label tables, prefix labels, footnote label, edition label and AUP notice are as approved in the table above (user-reviewed wording).
- [ ] `is_target_text` for `vi`: true for a string with a Vietnamese-only letter or tone-marked vowel; false for plain English, for "café"/"naïve"/"façade" (a French accent alone is not Vietnamese), for empty and for ASCII-only text. Unit-tested with at least 20 labelled samples (test-first, ordinary TDD per CLAUDE.md; no oracle exists). Thresholds, the 50-character rule and the echo check stay in Phase 3.
- [ ] The Simplified-Chinese gate is skipped for `vi`: `_offending_simplified_chinese_chars` is only evaluated when the active profile declares it (a new field or an explicit `if profile.code.startswith("zh")` guard; choose in the Advise call). `BANNED_PATTERNS` are zh-only and not applied to `vi`.

Register hints, glossary and prompts
- [ ] Per Open Question 1: a Vietnamese register file exists (≥ the two registers literary fiction and non-fiction narrative, Vietnamese `prefer`/`avoid`/`subagent_rules`, `min_length_ratio` set from a measurement, not copied from zh), and `resolve_register`, `resolve_register_override` and `resolve_register_rules` take the profile. For zh-tw the loaded data and the rendered prompt are unchanged (golden `prompt` group still passes).
- [ ] `GLOSSARY_PROMPT` is rendered from the profile (target language name, name-handling advice, chapter-title examples such as `Chương 1: …`); the zh-tw rendering is byte-identical to today (pin the current text in a new golden group derived from `dac59fe` first, then refactor).
- [ ] `GENERIC_SUBAGENT_RULES` becomes profile-driven; zh-tw output unchanged; `vi` gets Vietnamese-appropriate fallback rules (no `翻譯腔`).
- [ ] The glossary key stays `chapter_titles_zh` (DECISION-002); the glossary prompt text says so in a comment so a reader is not misled.

Behaviour end to end (`vi`)
- [ ] `build_subagent_prompt(..., target_lang="vi")` contains the Vietnamese rules and no Han characters and no `Traditional Chinese rule`.
- [ ] With a frozen Vietnamese fixture (see Test Plan), `assemble` yields a nav with `lang="vi"`, the Vietnamese edition label and contents label, OPF `<dc:language>vi</dc:language>`, and paragraphs with classes `tgt tgt-vi`; the output contains no Han and no `tgt-zh`.
- [ ] `bilingual_coverage_audit` passes on the Vietnamese fixture and fails on the same fixture with one paragraph left in English (both asserted).
- [ ] An unregistered `target_lang` (e.g. `vn`) raises a clear error in `assemble` and `audit_suite` (Open Question 5); `build_subagent_prompt` keeps the pinned fallback for `zh-cn`/`en`/`ja`/`ko`. A DECISION entry records the final rule and supersedes the "tighten in Phase 2" note in DECISION-006.

Regression and process
- [ ] All Phase 1 checks still hold: golden and frozen-zh-tw snapshot identical to `bb0eb35`; no existing test file modified (`git diff --diff-filter=MDRT --name-only dac59fe -- test/ conftest.py requirements-dev.txt requirements.txt .github/` prints nothing); scope guard for the ollama/omlx files empty; the Phase 1 grep gate still clean on the zh-tw side.
- [ ] CI green (ubuntu 3.10/3.12, windows 3.12).
- [ ] Ledger updated; any new bug found goes to `docs/BUGS.md`, any tradeoff to `docs/DECISIONS.md`.

## Test Plan

- Test-first (ordinary TDD; there is no external oracle for Vietnamese): `test/test_lang_profile_vi.py` written red before the profile data. Groups: registry, label tables, `is_target_text` samples, prompt content, nav/OPF/rewriter output with `vi`, both audits (pass and fail pairs), unknown-code errors.
- Golden for the refactors that touch zh-tw (register hints, glossary prompt, generic rules): derive from a `dac59fe` worktree first, then change code, exactly as in Phase 1.
- Frozen Vietnamese fixture: `docs/tasks/02-profile-vi/frozen-fixture/` mirroring the zh-tw one (Alice excerpt: title page, chapter I and II first paragraphs) with hand-written Vietnamese translations and `target_lang: "vi"`. Native review of those translations is not required for the test, but they must contain Vietnamese diacritics so `is_target_text` is exercised.
- Commands: `pytest -q`; the Phase 1 gate commands (`git diff --diff-filter=MDRT …`, scope guard, grep gate); `python docs/tasks/02-profile-vi/frozen-fixture/build.py … && snapshot.py …` for `vi`.

## Program design (sketch; confirm in the Advise call)

- New or changed `LanguageProfile` fields (each needs a reason; none added "just in case"): `register_hints_path` (Open Question 1a), `glossary_prompt_notes` (name-handling advice and chapter-title examples), `generic_rules` (replaces `GENERIC_SUBAGENT_RULES`), and a way to express "apply the Simplified gate" (boolean `simplified_gate`). Four additions to the 13 fields; the Advise call should challenge each.
- Call sites: `glossary.py` (`GLOSSARY_PROMPT`, `_load_register_hints`, `resolve_register*`), `dispatch.py` (`GENERIC_SUBAGENT_RULES`, `build_subagent_prompt`), `translation_quality_audit.py` (Simplified gate and `BANNED_PATTERNS` guarded by the profile), `assemble.py` / `audit_suite.py` / `lang_profile.py` (strict lookup), `assets/` (new `register_hints.vi.json`).
- Layout: single package (`scripts/`) plus one asset file.

## Sub-tasks

- [ ] 2.1 User answers the open questions and reviews the Vietnamese wording; DoD approved
- [ ] 2.2 Advise call for the field changes (log in `docs/eagd-log.md`)
- [ ] 2.3 Golden group for the zh-tw glossary prompt, generic rules and register-hint rendering, derived from a `dac59fe` worktree
- [ ] 2.4 Red tests: `test_lang_profile_vi.py`, then the Vietnamese frozen fixture and its snapshot
- [ ] 2.5 Add fields and the `vi` profile; refactor the glossary and dispatch pieces; register hints for `vi`
- [ ] 2.6 Guard the Simplified gate and strict unknown-code handling; DECISION entry
- [ ] 2.7 Verify the DoD; update the ledger

## Notes / deviations
