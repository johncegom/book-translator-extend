"""DECISION-016: English-heavy technical Vietnamese is recognised as Vietnamese.

Ordinary test-first (no external oracle for Vietnamese). The positive lines are real output of the
2026-11-12 run of "System Design Interview" (short quotes of our own translation); each was rejected
by the 0.25 share rule. The three pinned negatives are accepted false negatives: the sentences are
correct Vietnamese, but too few of their words carry a Vietnamese-only letter. Pinning them makes a
later rule change show up as a deliberate diff.
"""
from __future__ import annotations

import pytest

from scripts.lang_profile import _VI_DISTINCTIVE_RE, _VI_FUNCTION_WORDS, get_profile

VI = get_profile("vi")

NEW_WORDS = ["cho", "trong", "ngay", "phía", "nào", "thành", "khi", "chúng", "nên", "vào", "thì", "mà", "sau", "nhau"]


@pytest.mark.parametrize("text", [
    "Ứng viên: Mục đích chính của crawler là gì? Dùng cho search engine indexing, data mining hay việc gì khác?",
    "Như Hình 12-7 minh họa, chat system được chia thành ba nhóm chính: stateless service, stateful (có trạng thái) service.",
    "7. Trước tiên, block server download các block từ cloud storage.",
    "Ứng viên: Web crawler thu thập bao nhiêu trang web mỗi tháng?",
    "4. News feed service lấy danh sách post ID từ news feed cache.",
    "• Datacenter ID: 5 bit, cho ta 2 ^ 5 = 32 data center.",
])
def test_english_heavy_technical_vietnamese_is_target_text(text):
    assert len(text) >= 50 or "Datacenter" in text
    assert VI.is_target_text(text) is True


@pytest.mark.parametrize("text", [
    "Để biết thêm thông tin, vui lòng liên hệ systemdesigninsider@gmail.com",
    "• Depth-first search (DFS) so với Breadth-first search (BFS)",
    "2.1 Client 1 upload nội dung file lên block server.",
])
def test_known_false_negatives_are_pinned(text):
    # Correct Vietnamese that the rule still rejects (DECISION-016). Do not tune the output to the check.
    assert VI.is_target_text(text) is False


def test_share_rule_cutoff_is_a_fifth_of_the_lowercase_tokens():
    one_in_five = "ăn " + " ".join(["infrastructure"] * 4)    # share 0.20 exactly
    one_in_six = "ăn " + " ".join(["infrastructure"] * 5)     # share 0.167
    assert len(one_in_five) >= 50 and len(one_in_six) >= 50
    assert VI.is_target_text(one_in_five) is True
    assert VI.is_target_text(one_in_six) is False


@pytest.mark.parametrize("word", NEW_WORDS)
def test_new_function_words_count_in_short_text(word):
    assert VI.is_target_text(f"ok {word}") is True


@pytest.mark.parametrize("word", ["em", "là", "anh", "ta", "hay", "do"])
def test_ambiguous_words_still_do_not_count(word):
    assert VI.is_target_text(f"ok {word}") is False


def test_function_words_have_no_distinctive_letter_unless_listed_for_a_reason():
    # The list exists for words the letter rule cannot see. A word with a distinctive letter is dead weight.
    for word in _VI_FUNCTION_WORDS:
        assert not _VI_DISTINCTIVE_RE.search(word), word


@pytest.mark.parametrize("text", [
    "We deployed the rate limiter in two data centers and then measured the latency of every single request.",
    "Nous avons déployé le service dans deux centres de données puis mesuré la latence de chaque requête.",
    "Implantamos o serviço em dois centros de dados e medimos a latência de cada requisição enviada.",
    "We ate phở, bún chả and bánh mì at the market while the team talked about the new cache design.",
])
def test_english_french_portuguese_technical_text_is_not_vietnamese(text):
    assert VI.is_target_text(text) is False


@pytest.mark.parametrize("text", [
    "Go to the data center",
    "A very long day for the team",
    "Sue and Bob",
])
def test_short_english_lines_without_vietnamese_words_stay_false(text):
    assert len(text) < 50
    assert VI.is_target_text(text) is False
