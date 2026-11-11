"""Characterization of the zh-tw glossary/register/prompt/audit behaviour that Phase 2 refactors.

golden_zh_tw_phase2.json was produced by test/golden/derive_phase2.py run inside a
worktree of e0f41b6 (see derive_phase2.py). These tests recompute the same values
on the current code and require an exact match, group by group.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .derive_phase2 import compute

GOLDEN = json.loads((Path(__file__).parent / "golden_zh_tw_phase2.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current():
    return compute()


@pytest.mark.parametrize("group", sorted(GOLDEN))
def test_group_matches_oracle(group, current):
    assert current[group] == GOLDEN[group]


def test_golden_covers_expected_groups():
    assert set(GOLDEN) == {
        "glossary_prompt", "register_block", "resolve_register", "resolve_register_override",
        "resolve_register_rules", "subagent_prompts", "generic_rules", "min_length_ratio", "quality_audit",
    }


def test_golden_is_not_trivially_empty():
    # Guards against a golden file regenerated from a broken or stubbed run.
    assert GOLDEN["glossary_prompt"]["path_name"] == "register_hints.json"
    assert "__REGISTER_HINTS_BLOCK__" not in GOLDEN["glossary_prompt"]["text"]
    assert "SAMPLE TEXT" in GOLDEN["glossary_prompt"]["rendered"]
    assert GOLDEN["register_block"]["ids"] == ["literary_fiction", "non_fiction_narrative", "academic_technical"]
    assert GOLDEN["resolve_register"]["'literary plain prose'"] == "literary_fiction"
    assert GOLDEN["resolve_register"]["'zzz unknown register'"] is None
    assert GOLDEN["resolve_register_override"]["'nope'"] is None
    assert GOLDEN["min_length_ratio"]["academic"] == 0.3
    assert GOLDEN["min_length_ratio"]["unmatched"] == 0.22
    assert any("翻譯腔" in r for r in GOLDEN["generic_rules"])
    assert len(GOLDEN["subagent_prompts"]) == 10
    assert GOLDEN["quality_audit"]["ok"] is False
    assert any("Simplified Chinese" in f for f in GOLDEN["quality_audit"]["failures"])
