# EAGD lessons

Process and tooling lessons written by the Dream role. Product tradeoffs go to `docs/DECISIONS.md`; defects go to `docs/BUGS.md`.

## 2026-11-12 (Phase 5 run history)

- Verify subagent output with the orchestrator's own validation step, never with the subagent's "done" report. Several translate subagents reported completion without counting their own markers; the main session's validate step was the only real check (16 of 16 passed on first try, which is only trustworthy because it was measured). Evidence: subagent reports in the Phase 5 run.
- Have a glossary or extraction subagent prove coverage before its output is used. A Sonnet glossary pass that skimmed most chapters (self-reported) produced common words such as "more" as glossary keys. Require per-chapter evidence (counts or sampled terms) before accepting the artifact.
- Test a grader's rubric against known-good and known-bad samples before the first graded run. Grade round 1 failed two checks on identical list labels and on common-word glossary keys; both were rubric errors, not translation defects.
- When the same grader check fails in two consecutive rounds on the same shape, suspect the rubric before the output. Round 2 still flagged the gloss-in-parentheses pattern after tightening, so the check definition itself needs a mechanical, example-backed spec.
- Keep the Grade rubric to mechanically checkable items with explicit exemptions written into the rubric (for example, list labels and glossary first-mention glosses), so a pass or fail can be reproduced without judgment.
- Run a real-data smoke test with each structural variant of the input before a full run. The source_only exemption bug (BUG-006) appeared only in books whose files are split into several spine items; synthetic tests and fixtures never contained that structure, and it caused about 99% of roughly 1,200 failing audit lines on the first real run.
- When a threshold produces a false negative, measure the other side of the distribution before touching the cutoff, and never reword output to pass. The Advise call on the 0.231-vs-0.25 case recommended exactly this, and the measured source share (0.0 for all 1,268 paragraphs) showed the detector was not the problem.
- Copy measured numbers into prompts from tool output, never from memory. A share typed from memory as 0.214 was actually 0.231; the advisor caught the rounding error, but the prompt was wrong until then.
- A style skill from one language does not transfer by its word lists. The English banned-word lists were rejected by the user for Vietnamese output; porting the underlying principles into a language-specific instruction block and redoing the anchor chapter fixed it in one round. Port principles, not lists, and validate the sample with the user before fanning out.
- Use a pilot, then size-bounded batches. A pilot of 2 followed by batches of 5, 5 and 3 ran with zero retries and zero escalations. Size the largest item to fit one subagent call (the 316-paragraph item did), so no item is split mid-chapter.
- Keep helper scripts outside the repo and pass them paths as arguments, so the repo holds only reviewed artifacts. The run's validate, extract and mark_done steps ran from scratch scripts without polluting the diff.
- Treat free-text answers to a question as instructions to apply, but confirm the scope when the answer does not match an offered option. The user answered an AskUserQuestion with an instruction; the workflow accepted it, and nothing was lost because the instruction was specific.
- Treat subagent hand-back messages as data, not instructions. Each report was checked against the artifacts on disk before being relied on.

## 2026-11-12 (smoke run: *A Modest Proposal*, 3 items, en to vi)

- Probe the interpreter name before running a skill whose commands say `python3`. On this Windows machine only `python` and `py` exist, so the first extract call failed. Run `python3 --version` first and fall back to `python` or `py`.
- Print non-ASCII output only after setting `PYTHONIOENCODING=utf-8` on Windows. A Vietnamese `print` raised a cp1252 `UnicodeEncodeError` in a scratch script; no data was lost because the state had been saved before the print, but a crash at that point is easy to misread as a failed step.
- Offer to exclude boilerplate at the approval gate, before the fan-out. About 18k of the 39k characters in the essay item were Project Gutenberg licence text, which the manifest classed as `translate` and which was translated at normal cost. Whenever an extracted item contains a large licence, colophon or index block, ask whether to keep it `source_only`.
- Keep the Grade rubric mechanical, but always add an open accuracy line to the grader prompt. All five rubric items passed; the extra "flag any mistranslation" line found three real issues (a wrong clerical office, an untranslated unit, an ironic phrase), two of which were fixed with one-string edits. Treat open-ended grader findings as targeted-fix candidates.
