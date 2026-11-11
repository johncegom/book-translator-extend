"""Characterization of zh-tw behaviour against the pre-refactor oracle (bb0eb35).

golden_zh_tw.json was produced by test/golden/derive.py run inside a worktree
of bb0eb35 (see derive.py for the exact command). These tests recompute the
same values on the current code and require an exact match, group by group.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .derive import compute

GOLDEN = json.loads((Path(__file__).parent / "golden_zh_tw.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current():
    return compute()


@pytest.mark.parametrize("group", sorted(GOLDEN))
def test_group_matches_oracle(group, current):
    assert current[group] == GOLDEN[group]


def test_golden_covers_expected_groups():
    assert set(GOLDEN) == {
        "tables", "target_long", "han", "paragraph", "untranslated_reason", "nav", "rewriter", "audit", "prompt",
    }


def test_golden_is_not_trivially_empty():
    # Guards against a golden file regenerated from a broken or stubbed run.
    assert GOLDEN["tables"]["structural"]["Contents"] == "目錄"
    assert GOLDEN["target_long"]["zh-tw"] == "台灣繁體中文"
    assert GOLDEN["target_long"]["fr"] == "fr"
    assert GOLDEN["audit"]["min_length_ratio"]["no_dir"] == 0.22
    assert "tgt-zh" in GOLDEN["rewriter"]["target_classes"]
    assert len(GOLDEN["audit"]["reviewable_short_target"]) == 5 * 5 * 9 * 3 * 2
