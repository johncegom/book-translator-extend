# CLAUDE.md

EPUB book translator (Claude Code skill). Entry point for the skill itself is `SKILL.md`; scripts are in `scripts/`, tests in `test/`.

## Commands
- Test: `pytest -q` (dev deps: `requirements-dev.txt`)

This repo was forked from `fredchu/book-translator` but is now independent. Do not plan around upstream merges, rebases or PRs.

## Where things live
- Plan (design and rationale): `docs/plans/2026-11-11-vietnamese-language-profile.md`
- Task ledger: `docs/LEDGER.md` — phase status plus links to per-phase detail. Read it first; open only the detail doc you need.
- Phase detail: `docs/tasks/<NN-slug>/TASK.md` — Definition of Done, Test Plan, Program design, sub-tasks.
- Decision log: `docs/DECISIONS.md` — deliberate tradeoffs a reasonable person might have chosen differently
- Bug log: `docs/BUGS.md` — something already wrong in the product
- Retro log: `docs/RETRO.md` — process lessons that generalize beyond one task. Skim before starting a new phase.

## Way of working (Tier 2 — Standard)
- **Task approval:** before implementing a phase, its `docs/tasks/<NN-slug>/TASK.md` must have a Definition of Done and Test Plan (with exact commands) that the user has approved. Fill the Program design section when the work touches several files or you will generate a substantial chunk of code. Tick sub-tasks as you go so an interrupted session can resume from the doc.
- **Ledger:** update `docs/LEDGER.md` when a phase starts, blocks or finishes. A phase is `done` only when its DoD is fully checked and the Evidence cell links the PR or commit.
- **Decision log:** add an entry for a real tradeoff. Skip routine or trivially reversible choices.
- **Bug log:** log a defect with symptom, root cause (or "unknown"), and reachability. Logging is not fixing: wait for an explicit decision before applying the fix. Exception: a live security hole or data-loss path gets flagged to the user immediately.
- **Retro log:** add an entry only if the lesson passes the generalization test (would it change how a different future task is approached?).
- **No silent scope expansion:** an unrelated issue found mid-task goes in the bug log or a note to the user, not into the current diff.
- **Proportionality:** overengineering is code or process that solves a problem the project doesn't have. Name the real, currently reachable reason before adding an abstraction, guard, or process step. "Just in case" is not a reason.
- **Ground-truth TDD (Tier 3), scoped to named functions only.** The oracle is the current `zh-tw` behaviour of the pre-refactor code. For each function moved into the profile (label lookup, `_target_long`, the Han check, the audit predicates and thresholds): first run the original code and record its real output as a golden case, then write the test from that record, confirm it fails or is absent on the new path, then implement to green. If a test is later found wrong, re-derive it from the original code at the pre-refactor commit; never adjust it to match what the new code outputs. Do not apply this to the Vietnamese profile: no external oracle exists there, so use ordinary test-first development with labeled sample text (Phase 3).
- **Oracle commit:** pre-refactor code is `main` at `bb0eb35`. Derive golden values with `git show bb0eb35:scripts/<file>` or a worktree, never from memory.
- **Tests:** `pytest -q`. Cloud-GPU and local-model tests are skipped by `conftest.py` (DECISION-004). CI is the reference environment (ubuntu and Windows).

## Re-calibrate this setup when
- A second contributor (human or separate AI session acting like one) joins.
- The project handles real user data, money, or credentials.
- It outlives its expected scope or stakes rise.
- The installed process visibly mismatches reality (too heavy, or its absence causes confusion). Raise it with the user instead of silently ignoring or pushing through.

## Execute / Advise / Grade / Dream (EAGD)

Rationale: `docs/execute-advise-grade-dream.md`. Each role is a separate sub-agent call (the `Agent` tool) on its bound model, not a phase inside this session.

<!-- eagd-bindings:start -->
eagd-binding: role=advise tool=Agent model=opus status=ok probed=2026-11-11 reported=claude-opus-5-5
eagd-binding: role=grade tool=Agent model=haiku status=ok probed=2026-11-11 reported=claude-haiku-5-5
eagd-binding: role=dream tool=Agent model=haiku status=ok probed=2026-11-11 reported=claude-haiku-5-5
<!-- eagd-bindings:end -->

**EAGD log:** `docs/eagd-log.md`

<!-- eagd-directive:start v=1 -->
**EAGD binding mechanics.** Managed by `bootstrap-eagd-pattern`. Do not edit
between these markers: put a local rule in a paragraph that begins
`**Local override.**` outside them, and change this span only by running the
skill's upgrade. The log is the file named on this document's `**EAGD log:**`
line.

*Precedence.* A `**Local override.**` paragraph outside this span wins over it
for the rows or roles that paragraph names. Any other text elsewhere about
binding rows, judging the `model:` reply or log statuses is superseded by this
span.

*Rows.* A binding is an `eagd-binding:` row keyed by `(role, tool)`. Find the
sub-agent tool you actually hold in your own tool list (do not guess your
vendor) and use the row for your role and that tool whose `status` is `ok` or
`flagged`. Row keys not defined here are owner extensions: pass `effort` if
your tool takes one, and ignore the rest.

*No usable row* (none for your tool, a status other than `ok` or `flagged`, the
row's model is your own, or the spawn errors). Advise and Dream skip: never run
them on your own model or an unknown one, because a same-model "consultation"
looks like a second opinion and is not. Proceed on your recorded leaning, log
the Advise call `SKIPPED reason=<code>` (for example
`no-verified-model-binding`), and say in the PR body or final report that the
role did not run. Grade may fall back to a fresh, context-free call on your own
model, since fresh eyes is its main value; add a Grade-fallbacks row only when
it does.

*Calling a role.* Call that tool with the row's `model`. Advise gets the
question, your leaning with the case for and against, and the artifacts the
decision turns on, verbatim (not your summary, not the transcript), and is
asked to name any context it lacked. Grade gets only the rubric and the
finished output, withholding the reasoning behind it. Dream gets the full run
history. Ask Advise and Dream to begin their reply with `model: <its own id>`.
A call on a `flagged` row is unverified: pass the explicit id and still ask for
that line.

*Judging the `model:` reply.* Take the id after `model:` on the reply's first
line. Normalize it and every id you compare it with, including the row's
`model=`: lowercase, trim surrounding whitespace, remove every quote and
backtick character, then drop one trailing period, then a trailing `-latest`.
Take the first case that fits:
1. It is your own id → set `status=stale`, add a Binding-changes row, and skip
   Advise until it is fixed.
2. It equals `reported=` → proceed.
3. It is uninformative (empty or missing, equal to `model=`, a bare family (an
   id with no digit in it), or a display name, meaning spaces inside the
   normalized id) → as in 1 on an `ok` row; no change on a `flagged` row.
4. Neither it nor `model=` contains the other → as in 1.
5. Otherwise the alias moved. Do not edit the row yourself. On a `flagged` row,
   proceed. On an `ok` row, if you hold an ask-the-user tool
   (`AskUserQuestion` on Claude Code) and are not a sub-agent, ask once per id
   per conversation, showing both ids:
   - "Use `<new>`": set `reported=<new>` (normalized) on every `ok` row with
     this tool and `model=`, add a Binding-changes row, and log the call as
     plain `answered`.
   - "Keep the binding and use the answer": log `answered flag=drift-assumed`
     and name the id in the final report.
   - Any other reply: set `status=stale` and log `SKIPPED reason=drift-declined`.

   If you cannot ask (a sub-agent, or no ask tool), act as "Keep the binding"
   but log `answered flag=drift-unconfirmed`.

*Flagged rows.* Log a call on a `flagged` row as `answered flag=unverified` and
say in the PR body or final report "Advise ran unverified on `<tool>`: the
model override could not be confirmed". Grade on a flagged row runs and adds a
Grade-fallbacks row with `reason=unverified-binding`. Dream marks its entry
`(model unverified)`. If a flagged call returns an informative `model:` reply
that fits `model=`, do not rewrite `reported=`; suggest re-running the skill to
verify.

*Logging.* Add one row per event at the end of its table in the log: Advise
calls (date, branch, question, prior leaning, answer, which was taken, tool,
requested model, reported model, status, changed yes/no), Binding changes
(date, role, tool, old, new, reason; also whenever a row's model, status or
reported id changes), Grade fallbacks (date, branch, tool, reason). An Advise
status is `answered`, `answered flag=unverified`, `answered flag=drift-assumed`,
`answered flag=drift-unconfirmed`, or `SKIPPED reason=<code>` (including
`drift-declined`). A row's `status` is `ok`, `flagged`, `unverified` or `stale`.
<!-- eagd-directive:end -->

**Advise.** Fires on observable conditions, never on felt doubt: (1) before adding or changing a field on `LanguageProfile` in `scripts/lang_profile.py`; (2) before changing a detector rule or audit threshold (`is_target_text`, `is_untranslated_source`, `min_length_ratio`). One call each time. Only judgment calls go here: anything answerable by reading the repo, read; a preference only the user can settle goes to `AskUserQuestion`. Write your leaning and why in one or two lines, then call Advise as described under EAGD binding mechanics, and log the call.

**Grade.** Runs once per finished translated chapter batch, or per phase "done when" check in the Vietnamese plan. Give it only the rubric and the finished output. Rubric (pass/fail each): (a) every body paragraph of 50+ chars has a target-language sibling; (b) no translation equals its source; (c) glossary terms and chapter numbers are consistent; (d) length ratio within the profile's `min_length_ratio`; (e) the bilingual/nav labels use the profile's labels. Default fail mode is full rerun; a targeted fix is allowed only when Grade can point to one bounded paragraph and nothing suggests the flaw recurs.

**Dream.** Runs after a Grade pass, with the full run history. It writes durable lessons to `docs/eagd-lessons.md` (create on first run). Process or tooling lessons only; product tradeoffs go to `docs/DECISIONS.md`, defects to `docs/BUGS.md`.

**Re-calibrate EAGD when:** a role fires on nearly every task (narrow the trigger or cheapen the model); a role never fires after a long period (remove it); Advise's decision-change rate (`Changed=yes` over answered rows, per Tool) sits near zero (the calls are ceremony). Before narrowing any trigger, count `SKIPPED` rows per Tool in `docs/eagd-log.md`: a low firing rate may be a missing-binding problem instead.
