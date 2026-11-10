# Vietnamese Target Language Port — Language Profile Plan

**Date:** 2026-11-11
**Goal:** Let the book-translator pipeline translate EPUBs into Vietnamese (`vi`) via the Claude Code subagent path, without breaking the existing Traditional Chinese (`zh-tw`) behaviour.

## Scope

**In:** Claude Code subagent path only.

**Out:**
- Local-model and cloud GPU paths (they carry Chinese-only steps such as opencc).
- Structural limits: inline markup is flattened, the translation is always a `<p>`, text outside the tag list is skipped. These are separate work in `content_blocks.py` and `bilingual_rewriter.py`. Do them only after Phase 5 works.

**Correction to earlier analysis:** the nav check is language-neutral. `_nav_display_label` only checks that the label differs from the English text. Only the label tables are Chinese.

## Design decision: language profile, not in-place replacement

- **Why not search-and-replace:** 41 of 52 test files contain Chinese text or zh names. An in-place port breaks them all and removes the safety net. A profile keeps the Chinese tests green and lets Vietnamese tests sit beside them.
- **Upstream is not a factor:** this repo forked from upstream but is independent of it now, so merge-ability is not a reason. The profile is chosen for the test safety net, and it also keeps adding more languages cheap.
- **How:** one new module holds everything language-dependent. Every other file asks the profile.

```python
# scripts/lang_profile.py
@dataclass(frozen=True)
class LanguageProfile:
    code: str                      # "vi"
    long_name: str                 # "Tiếng Việt"
    target_class: str              # "tgt-vi"
    structural_labels: dict[str, str]
    contents_labels: dict[str, str]
    prefix_labels: tuple[tuple[str, str], ...]
    prompt_rules: str
    default_custom_instructions: str
    min_length_ratio: float

    def is_target_text(self, text: str) -> bool: ...
    def is_untranslated_source(self, text: str) -> bool: ...

def get_profile(code: str) -> LanguageProfile: ...
```

## Where the code changes

| File | What depends on Chinese today | Change |
|---|---|---|
| `dispatch.py` | Traditional Chinese rule in prompt, Taiwan wording, `_target_long` table | Read rules and name from the profile |
| `glossary.py` | Prompt asks for Taiwan Chinese titles and transliterated names | Take wording from the profile |
| `bilingual_rewriter.py` | Two label dictionaries, class `tgt-zh` | Read labels and class from the profile |
| `nav_builder.py` | Prefix labels, the word for "footnote" | Read from the profile |
| `paragraph_classification.py` | `HAN_RE` decides "already translated" | Call `profile.is_target_text` |
| `bilingual_coverage_audit.py` | Sibling must contain Han characters | Call `profile.is_target_text` |
| `translation_quality_audit.py` | Han counts, Simplified Chinese check, 30% length rule | Profile ratio; skip Simplified check for `vi` |
| `state.py`, `translate_chapter_cli.py` | Default `zh-tw` | Keep default, pass the code through |
| `SKILL.md` | Triggers, defaults, author's agent-orch path | Add Vietnamese triggers and a `target_lang` step |

## Phases

### Phase 0: Baseline
- Run `pytest -q` on a clean clone.
- Pick one short public-domain EPUB as the test book.
- **Done when:** the suite is green before any change.

### Phase 1: Add the profile with Chinese only
- Move Chinese labels, rules and the Han check into a `zh-tw` profile.
- Pass `target_lang` from `state.json` into dispatch, assemble and the audits.
- **Done when:** every existing test passes with **no test edits** (proves the refactor changed no behaviour).

### Phase 2: Add the Vietnamese profile
- Write label tables, e.g. Contents → Mục lục, Copyright → Bản quyền, Acknowledgments → Lời cảm ơn.
- Write prompt rules: drop the Traditional Chinese rule; tell the model to keep personal names in original spelling (Vietnamese does not transliterate them like Chinese).
- Keep the glossary key `chapter_titles_zh` (renaming touches many files for no gain).
- **Done when:** new unit tests show Vietnamese labels in the nav and class `tgt-vi` on inserted paragraphs.

### Phase 3: Detector and audits (the hard part)
Chinese is detected by script; Vietnamese shares Latin letters with English, so another signal is needed.
- A paragraph counts as Vietnamese when it contains Vietnamese-only letters (ă, â, đ, ê, ô, ơ, ư, or a tone-marked vowel). Apply only to paragraphs ≥ 50 characters (the threshold the code already uses).
- Add an echo check: a translation equal to its source fails.
- Re-measure the length ratio. Chinese is much shorter than English; Vietnamese is about the same length, so 30% is too weak.
- **Done when:** the coverage audit fails on a chapter left untranslated on purpose, and passes on a real one.

### Phase 4: The skill file
- Add Vietnamese trigger phrases and a step that asks for the target language.
- Remove the `/Users/fredchu/bin/agent-orch` quota line, or make it optional.
- **Done when:** a fresh Claude Code session runs the skill with `vi` without manual fixes.

### Phase 5: One full book
- Run the whole pipeline on the test book.
- Open the result in a reader; check one early and one late chapter.
- **Done when:** all four audits pass and the read-back looks right.

## Risks

- **Short paragraphs:** a line like "OK." has no Vietnamese-only letters. The 50-char threshold covers this, but dialogue-heavy books will have many such lines.
- **Detector can be fooled:** an English paragraph with a French word like "café" does not match, because "é" alone is not Vietnamese-only. Test this case in Phase 3.
