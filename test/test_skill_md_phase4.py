"""Phase 4: five structural checks on SKILL.md (prose is otherwise reviewed by diff)."""
from __future__ import annotations

import re
from pathlib import Path

SKILL = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
FRONT = SKILL.split("---")[1]


def test_frontmatter_has_vietnamese_triggers_and_new_version():
    assert re.search(r"^version: 1\.4\.0$", FRONT, re.M)
    assert "dịch sách" in FRONT and "Vietnamese" in FRONT


def test_supported_languages_table_lists_zh_tw_and_vi_only():
    section = SKILL.split("## Supported languages")[1].split("\n## ")[0]
    assert "`zh-tw`" in section and "`vi`" in section
    assert "`ja`" not in section and "`ko`" not in section and "`zh-cn`" not in section


def test_quota_gate_is_conditional_and_has_no_personal_path():
    assert "/Users/fredchu" not in SKILL.split("## Translation provider")[1].split("### Cloud mode")[0]
    assert "only if an `agent-orch` command exists" in SKILL


def test_zh_tw_only_tools_are_marked():
    term = SKILL.split("### Building a small, decision-focused term list")[1][:300]
    assert "zh-tw only" in term and "skip" in term
    for heading in ("### Cloud mode", "### Offline mode"):
        assert "zh-tw only" in SKILL.split(heading)[1][:300]


def test_step1_asks_for_the_language_and_writes_it_to_state():
    step1 = SKILL.split("### Step 1: Collect parameters")[1].split("### Step 2")[0]
    assert "AskUserQuestion" in step1 and "init_state" in step1 and "`vi`" in step1
    assert "target_lang=state" in SKILL.split("### Step 6")[1].split("### Step 7")[0]
