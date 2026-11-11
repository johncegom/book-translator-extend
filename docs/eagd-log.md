# EAGD log

Append one row per event at the end of its table. A single line per row, no line breaks inside a cell, a literal `|` written as `\|`, `—` for a field that doesn't apply.

## Advise calls

| Date | Branch | Question | Prior leaning | Answer | Taken | Tool | Requested | Reported | Status | Changed |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | feat/lang-profile-zh-tw | Phase 1 LanguageProfile field set and shape | 8 fields (code, long_name, target_class, 3 label fields, prompt_rules, is_target_text); optional profile arg defaulting to zh-tw; is_target_text replaces only paragraph_classification.HAN_RE | Ship 13 fields (add html_lang, footnote_label, bilingual_edition_label, aup_refused_notice, default_custom_instructions); route the 3 same-range Han checks through is_target_text; keep defaults plus a sentinel-profile guard test; add resolve_profile with zh-tw fallback | pending user approval of DoD changes | Agent | fable (user override, one time; binding is opus) | claude-fable-5-2 | answered flag=user-model-override | yes |
| 2026-11-11 | feat/lang-profile-vi | Phase 2 LanguageProfile additions and structural changes | 4 fields: register_hints_path, glossary_prompt_notes, generic_rules, simplified_gate; min_length_ratio later; vi detector letters a-circumflex/e-circumflex/o-circumflex etc. | 17 fields total; register_hints_file (bare filename); glossary_prompt_slots dict with 4 slots + build_glossary_prompt; generic_rules kept; simplified_gate bool guarding only the Simplified message; do NOT add min_length_ratio; BANNED_PATTERNS apply to vi unchanged; drop circumflex letters from the vi detector; carve 3 existing tests out of the no-edit rule; new pins in new golden files | pending user approval of DoD amendments | Agent | fable (user override, one time; binding is opus) | claude-fable-5-2 | answered flag=user-model-override | yes |
| 2026-11-11 | docs/phase3-detail | Phase 3 vi is_target_text: share cutoff, short-text rule, function-word list | share >= 0.25 of all words for paragraphs >= 50 chars; any-match below 50 with list {và, không, tôi, xin, chào, em, các, này} (no là/anh) | Keep 0.25 and the 50-char split; count only lowercase-initial tokens (skip all-digit tokens) at every length, with fallback to all tokens when none are lowercase-initial; drop em; keep the other six; pin tok[0].islower() after NFC; add source-side exemption fixtures; set min_length_ratio (about 0.5-0.6) in a separate Advise call | Adopted all; verified the audits' own 50-char cutoff matches and that the coverage audit also runs is_target_text on source nodes | Agent | opus | claude-opus-5-5 | answered | yes |
| 2026-11-11 | feat/vi-detector-audits | Phase 3 echo check: new profile field echo_check or run for every profile; comparison; failure vs warning | echo_check profile field (zh-tw False, vi True), exact equality after NFC+whitespace, source >= 50 chars, hard failure | Add the check but no field: it is a defect in any language and a Han target can never equal an English source; exact equality after _clean, case-sensitive; hard failure with hard_target_failure=True; skip headings, sources < 50 chars and source_only exceptions; add one zh-tw test where an echo fails; only add a flag if a zh-tw golden fixture contains an echo pair | Answer taken (user chose it over the earlier field decision) | Agent | opus | claude-opus-5-5 | answered | yes |

## Binding changes

| Date | Role | Tool | Old | New | Reason |
|---|---|---|---|---|---|
| 2026-11-11 | advise | Agent | — | opus (claude-opus-5-5) | initial install, probe ok |
| 2026-11-11 | grade | Agent | — | haiku (claude-haiku-5-5) | initial install, probe ok |
| 2026-11-11 | dream | Agent | — | haiku (claude-haiku-5-5) | initial install, probe ok |

## Grade fallbacks

| Date | Branch | Tool | Reason |
|---|---|---|---|
