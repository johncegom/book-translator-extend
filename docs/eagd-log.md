# EAGD log

Append one row per event at the end of its table. A single line per row, no line breaks inside a cell, a literal `|` written as `\|`, `—` for a field that doesn't apply.

## Advise calls

| Date | Branch | Question | Prior leaning | Answer | Taken | Tool | Requested | Reported | Status | Changed |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | feat/lang-profile-zh-tw | Phase 1 LanguageProfile field set and shape | 8 fields (code, long_name, target_class, 3 label fields, prompt_rules, is_target_text); optional profile arg defaulting to zh-tw; is_target_text replaces only paragraph_classification.HAN_RE | Ship 13 fields (add html_lang, footnote_label, bilingual_edition_label, aup_refused_notice, default_custom_instructions); route the 3 same-range Han checks through is_target_text; keep defaults plus a sentinel-profile guard test; add resolve_profile with zh-tw fallback | pending user approval of DoD changes | Agent | fable (user override, one time; binding is opus) | claude-fable-5-2 | answered flag=user-model-override | yes |

## Binding changes

| Date | Role | Tool | Old | New | Reason |
|---|---|---|---|---|---|
| 2026-11-11 | advise | Agent | — | opus (claude-opus-5-5) | initial install, probe ok |
| 2026-11-11 | grade | Agent | — | haiku (claude-haiku-5-5) | initial install, probe ok |
| 2026-11-11 | dream | Agent | — | haiku (claude-haiku-5-5) | initial install, probe ok |

## Grade fallbacks

| Date | Branch | Tool | Reason |
|---|---|---|---|
