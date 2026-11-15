# Grade rubric (draft, not yet adopted)

Status: draft 2026-11-13, waiting for user approval. `CLAUDE.md` still holds the old five-line rubric.

## How Grade uses this file

- Grade gets this file, the finished EPUB path and the book folder. It gets nothing else.
- Every check is a yes/no question. **YES is always the passing answer.**
- Reply format, one line per check: `ID: YES` or `ID: NO`, then a count or one quoted line as evidence. No opinions, no "partly", no extra advice.
- If a check cannot be run, answer `NO - could not check` and say why.
- Overall result: PASS only if every check is YES. List the NO lines and stop.
- Each check names a command, a file or a count. Grade does not judge translation quality; it only reads facts.

## (a) Coverage

- **A1.** Does `audit_suite` report `bilingual_coverage` with 0 FAIL lines? (WARN lines are allowed.)
- **A2.** Does every top-level source block of 50+ characters (a paragraph, or a whole `<blockquote>`) have a `tgt` element directly after it, unless its text is in `translations/source_only.json`? A blockquote counts as one block (BUG-014, option a).

## (b) Untranslated text

- **B1.** Is every source/target pair with identical text either listed in `translations/source_only.json` with a non-empty reason, or shorter than 5 words?
- **B2.** Does `translation_quality` report 0 FAIL lines?

## (c) Consistency

- **C1.** If the book folder has a `spec_terms.json` (terms the user fixed), is every key's value present in the target text of every paragraph whose source contains that key? If the file does not exist, answer YES and write `no spec_terms.json`.
- **C2.** Are the numbered chapter labels in `nav.xhtml` and `toc.ncx` the same numbers in the same order, with the source number equal to the target number in each label?

Why only these: fixed terms are the only glossary entries a user has confirmed word for word, so verbatim presence is a fair test for them. Other glossary terms may take natural inflected forms and are not checked.

- **N1.** Does every number of 3 or more digits in a source block of 50+ characters also appear in its target block (separators ignored, so 2,750 equals 2.750)? One- and two-digit numbers are skipped because Vietnamese often spells them out ("3 a.m." becomes "ba giờ sáng").
- **G1.** Is every parenthetical that the translation added (not in the source) used in at most 3 blocks? (Repeated brackets usually come from a glossary value that contains a bracket.)

## (d) Length

- **D1.** Is the lowest target/source character ratio over all paired blocks of 50+ characters at or above the value returned by `_min_length_ratio_from_book_dir(book_dir, profile=<the profile for state.json target_lang>)`?

## (e) Labels

Source of truth for a label: the profile's `structural_labels` and `bilingual_edition_label`, then `nav_overrides` in the book's `translations_extra.json`.

- **E1.** Does every `nav.xhtml` entry either equal one of the profile's labels, equal a `nav_overrides` value (a page with no heading shows its target label alone, BUG-017), or contain `｜` followed by non-empty target text?
- **E2.** Is the `nav.xhtml` label for each structural page (Title Page, Contents, Dedication, Introduction, Notes, Acknowledgments) equal to the profile's label, or to `nav_overrides` for that page?
- **E3.** Does the `nav.xhtml` `<title>` and the `toc.ncx` `docTitle` end with the profile's `bilingual_edition_label`?
- **E4.** For every `toc.ncx` entry that points to a heading with a `tgt` element directly after it holding different text, does the label contain `｜`? (Entries with no such element, or identical text, are excluded; the script reports how many.)
- **E5.** Is every `nav.xhtml` and `toc.ncx` label free of an empty or `(untitled)` source side?

Known and out of scope for (e): `toc.ncx` lists only entries that the source NCX listed (BUG-016 task, open question 2). `nav.xhtml` may list more pages.

## Notes for whoever adopts this

- `scripts/grade_checks.py` runs every check here and prints one `ID: YES|NO - evidence` line each. Grade runs it and reports its output; it does not re-derive the answers.
- Nothing in this file is specific to one book. Book-specific facts (fixed terms, label overrides, source-only lines) live in the book's own files, which the checks read: `spec_terms.json`, `translations_extra.json`, `translations/source_only.json`.
- The glossary is not checked for verbatim presence. Natural inflected forms are allowed on purpose (see the analysis of run 4).


## Judged checks (J1, J4, JC)

These need reading, so Grade answers them, but only on a fixed sample and one pair at a time.

- Sample (endnote and reference pages are left out: a file where 60% or more of the 50+ character blocks start with a note number): `python -m scripts.grade_checks --source ... --output ... --book-dir ... --sample 20` prints 20 pairs (fixed seed, same pairs on every run), with each pair's glossary terms and the book's `style_anchor.avoid` list.
- Grade answers each question for each sampled pair: `P<id>: yes|no | "<one quote from the Vietnamese>"`. No scores, no explanation.
- A judged check passes if at most 1 pair in 20 is `no`. (A pass is weak evidence: 20 pairs catch gross faults, not rare ones.)

| ID | Question (yes = pass) |
|---|---|
| J1 | Does the Vietnamese make the same claims as the English: nothing added, nothing dropped, no claim reversed? |
| J4 | Is the Vietnamese free of English words left in running text? Exempt: personal and place names, titles of works, URLs, currency and unit names, loanwords in common Vietnamese use (for example "e-mail"), a term inside quotation marks, and an English term in parentheses right after its Vietnamese rendering. |
| JC | Does the Vietnamese use the listed Vietnamese words for each glossary term shown with the pair? A different or missing leading function word (for example a nominalizer or classifier) is fine; a different content word is not fine. Answer yes only if every listed term is rendered with its listed words; answer no if any term is rendered with a different content word. Answer yes if no listed term occurs. |

Wording rule learned in validation: no double negatives in a question. A "yes only if ... but no ..." form made the judge answer every sample backwards.

## Human items (not yes/no, not graded)

- Idioms rendered by meaning (was J2). In validation the judge failed 2 of 5 samples, and the "word for word" line is blurry (a literal calque can be a normal phrase). J1 already catches a wrong meaning.
- The style-avoid list (was J3). The list is free text written per book and its items are degrees ("dry academic", "too literal", "too much Sino-Vietnamese"); the judge answered "no" to every sample, including real passes.
- Natural fluency and rhythm of the Vietnamese. Two readers can disagree on what reads naturally.
- Tone and humor kept. Same reason.
- The "average score >= 8.0" cross-modal gate (SKILL.md Phase 3, deferred). It is a score, not a yes/no.
These stay with the human read-back.
