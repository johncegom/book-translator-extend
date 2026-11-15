# Retrospective Log

Process, tooling and collaboration lessons that would change how a different future task is approached. Not for product bugs (`docs/BUGS.md`) or design tradeoffs (`docs/DECISIONS.md`), and not a per-task diary: task-specific notes go in that task's detail doc.

## RETRO-001: Check the whole test baseline before setting a "green" exit criterion

**What went well:** Running the suite first showed 22 environment failures before any code change, so Phase 1's "no test edits" rule has a measurable baseline.
**What could improve:** The plan assumed the suite was green on a clean clone. It was not on Windows, which cost a detour (skip list, CI setup). CI also did not start automatically on the first PR for reasons not found.
**Advice for next time:** Run the baseline in Phase 0 on the platform you actually use, and use CI as the second opinion. Treat a PR with "no checks reported" as a problem to investigate, not as a pass.

## RETRO-002: When a fix turns a one-to-one mapping into one-to-many, search every lookup keyed on the old key

**What went well:** The full-book run found both defects within hours, and each was fixed test-first in a small PR.
**What could improve:** BUG-001 made several spine items share one file. Two later bugs (BUG-006 in `assemble.py`, BUG-007 in `nav_builder.py`) came from code that still treated "file name" as unique. DECISION-013 even noted the risk as "known and unchecked", and it surfaced only on the real book.
**Advice for next time:** When a change breaks a uniqueness assumption, grep for every dict or lookup keyed on that attribute in the same PR, and add a test with the new shape (here: a synthetic split file) for each.

## RETRO-003: A rubric written as prose gets a different reading on every call

**What went well:** Four Grade runs on one book exposed the problem: the same output passed (a) to (d) in run 3 and failed (a), (b), (c) in run 4, and rubric items (c) and (e) pulled the nav label in opposite directions.
**What could improve:** The rubric was five prose sentences and the grader prompt was rewritten by hand each run. Open wording let the grader invent a standard ("glossary terms verbatim"), and I tuned the output toward the grader (labels, a heading) instead of questioning the rubric. Dream, which only runs after a pass, never ran.
**Advice for next time:** Write grading rubrics as yes/no questions with one pass direction, a named source of truth for each fact, and a script for every check a script can answer. Keep the rubric in a versioned file and send that file, not a fresh paraphrase. Treat a repeated failure as a possible rubric defect before changing the output.

