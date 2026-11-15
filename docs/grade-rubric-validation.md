# Grade rubric: validation record (2026-11-14)

How `docs/grade-rubric.md` and `scripts/grade_checks.py` were checked. Test data: the real *Scarcity* output plus copies with one planted fault each. Expected answers were written before each run. The book text used for judge samples is not stored in the repo.

## CODE checks (14 checks x 15 samples = 210 cells)

| Round | Mismatches | What they were |
|---|---|---|
| 1 | 5 | 3 wrong expectations of mine (the quality audit also fails a block with no tgt; a "copy" planted with different spacing; a mutation that hit the landmarks list); 1 real checker gap: E2 only compared `contents_labels`, so "Introduction" and "Notes" were never checked. Fixed in the script. |
| 2 | 1 | B1 misses an echo whose text differs from the source only by spacing around inline tags. |
| 3 | 14 | A whitespace-insensitive B1 flagged the audit's own exempt endnote lines (source_only keys keep the audit's spacing). Reverted to the round-2 version. |
| 4 (user-approved, past the 3-round limit) | 0 | B1 and A2 now compare with all whitespace removed on both the pair and the `source_only` keys. |

Final state: round-4 checker, 210 of 210 cells match.

Also found on the first real run: N1 first flagged "3 a.m." (spelled out as "ba giờ sáng"), so it now checks numbers of 3+ digits only. That narrows the check for a real reason (spelled-out numbers), and the limit is stated in the rubric.

## JUDGE checks (each sample judged once per question wording, Haiku)

| Item | Round 1 | Later | Result |
|---|---|---|---|
| J1 | 5/5 | | kept |
| J2 | 3/5 | | moved to HUMAN |
| J3 | 2/5 | | moved to HUMAN |
| J4 | 4/5 ("rupee" flagged) | 5/5 after exempting currency and unit names | kept |
| JC | 4/5 | round 2: 0/5 (double negative, answers inverted); round 3: 5/5 | kept, with the no-double-negative rule |

Notes: one agent judged the five samples of an item in one call (samples listed separately, shuffled, expected answers withheld), not one call per sample. In JC round 2 I changed the borderline expectation to match the reworded rule before running it; the other expectations did not change. A pass on 5 samples is weak evidence; the thresholds (at most 1 `no` in 20) are untested on a real sample of 20.

## First real Grade run with the new rubric (Scarcity, 2026-11-14, Haiku)

| Part | Result |
|---|---|
| Script checks | 12 of 14 YES. G1 NO (glossary values with a bracket: "tâm trí" in 8 blocks, "tập trung hẹp" in 4). E5 NO (9 labels with "(untitled)", BUG-017). |
| J1, 20 pairs | 1 no (P0440, an added bracket gloss) -> PASS (limit 1) |
| JC, 20 pairs (9 had glossary terms) | 1 no (P0517, "xoay xở" for a longer glossary target) -> PASS |
| J4, 20 pairs | 5 no -> FAIL. Three are citation lines in the endnotes (P0802, P0869, P0951: "retrieved from", names, "as quoted in"); two are loanwords ("e-mail", "carbon dioxide"). |

Overall: FAIL. The J4 failures are mostly the sample, not the translation: citation lines are not running text, but the sampler does not exclude them. Open: exclude reference and citation lines from `--sample` (the audit already classifies them), and decide whether common loanwords count. Dream stays un-run (no pass).

### J4 rerun after the sampler fix (same day)

`--sample` now skips endnote and reference pages and the J4 exemption lists common loanwords. J4 on the new 20 pairs (10 files, none starting with a note number): 20 yes, 0 no -> PASS. J1 and JC were not rerun; their passes come from the earlier sample, which included some endnote lines. A clean full run on the new sample is still to do. The earlier J4 FAIL was a sample and wording problem, as expected.

### E1 widened for BUG-017 (2026-11-14)

E1 now also accepts a nav label equal to a `nav_overrides` value. `test/test_nav_placeholder_labels.py` checks that a bare "Dedication" and `Chapter ｜ ` (empty target) are still NO. Script run on the real output after the change: 14 of 14 YES.

### Grade run 6 on *Scarcity* (2026-11-14, after BUG-017 and the G1 cleanup)

- Script checks: 14 of 14 YES (G1 and E5 are now YES).
- Judged, fixed-seed sample of 20 on the final EPUB, one haiku judge per check, each run once:
  - J1: 20 yes, 0 no -> PASS.
  - J4: 19 yes, 1 no -> PASS. The no (P0440) is real: "carbon dioxide" and "carbon monoxide" stayed in English.
  - JC: 18 yes, 2 no -> **FAIL** (limit 1). Both no answers (P0388, P0517) are the same case: glossary "juggling -> xoay xở nhiều việc cùng lúc", translation says "xoay xở". The long glossary value is shortened in running text.
- Overall: FAIL because of JC. Dream not run. Not rerun and nothing edited to change the result. Open question: is the glossary value too long (profile/glossary issue, fix there), or should the translation use the full phrase.

### Grade run 6, JC rerun after the glossary change (2026-11-14)

User chose to shorten the glossary value "juggling" from "xoay xở nhiều việc cùng lúc" to "xoay xở" (the text already used the short form). Only the JC prompt changed (the glossary lines); same 20 pairs, one haiku judge, run once. JC: 20 yes, 0 no -> PASS. Overall Grade run 6: PASS (14 of 14 script checks, J1 20/20, J4 19/20, JC 20/20).

Caveat: this pass comes from changing the glossary to match the output, which is the Goodhart pattern the rubric warns about. It was a decision about which wording is right (user, after reading the trade-off), not a tuning to the score, but the judge's quotes for P0388 and P0517 no longer show the term, so the rerun is weak evidence for those two pairs. Nine places in the text still use the longer phrase "xoay xở nhiều việc cùng lúc"; they contain the shortened value.
