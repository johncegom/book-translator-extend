"""Language profiles: everything that depends on the target language.

Phase 1 registers only ``zh-tw``. The zh-tw data below was moved verbatim from
``bilingual_rewriter``, ``nav_builder``, ``dispatch`` and friends; the golden
tests in ``test/golden`` pin it against the pre-refactor code (bb0eb35).

``get_profile`` is strict. ``resolve_profile`` is the lenient lookup the
existing entry points use: it casefolds and falls back to zh-tw for any
unregistered code (DECISION-006). Compare profiles by ``.code``, never by
identity or ``==`` (the package can be imported under two module names).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

_ZH_TW_STRUCTURAL_LABELS = {
    'Contents': '目錄',
    'Introduction': '導論',
    'PART I': '第一部',
    'PART II': '第二部',
    'Acknowledgments': '致謝',
    'Notes': '註釋',
    'About the Author': '關於作者',
    'What’s next on your reading list?': '你的下一本書想讀什麼？',
    "What's next on your reading list?": '你的下一本書想讀什麼？',
    'Discover your next great read!': '發現下一本精彩好書！',
    'Get personalized book picks and up-to-date news about this author.': '取得為你量身推薦的書單，以及這位作者的最新消息。',
    'Sign up now.': '立即註冊。',
    'GO TO NOTE REFERENCE IN TEXT': '返回正文註記位置',
}

_ZH_TW_CONTENTS_LABELS = {
    'Contents': '目錄',
    'Cover': '封面',
    'Title Page': '書名頁',
    'Copyright': '版權頁',
    'Dedication': '獻辭',
    'PART I': '第一部',
    'PART II': '第二部',
    'Acknowledgments': '致謝',
    'Notes': '註釋',
    'About the Author': '關於作者',
}

_ZH_TW_PREFIX_LABELS = (
    ('praise for ', '各界讚譽'),
    ('advance praise for ', '各界讚譽'),
    ('also by ', '作者其他著作'),
)

_ZH_TW_PROMPT_RULES = 'Traditional Chinese rule: If the target is 台灣繁體中文, output must use\n繁體中文 (Traditional Chinese / Taiwan locale). 禁止使用任何簡體字。\n常見錯誤對照：『学』→『學』、『为』→『為』、『这』→『這』、\n『们』→『們』、『实』→『實』、『时』→『時』、『国』→『國』。'

_ZH_TW_DEFAULT_CUSTOM_INSTRUCTIONS = 'If the target is 台灣繁體中文, use 台灣用語 (e.g. 「軟體」not「软件」, 「網路」not「网络」). Avoid 翻譯腔. Prefer short sentences over four-character literary clichés.'

_HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def _zh_tw_is_target_text(text: str) -> bool:
    """True when text contains any CJK Han character (U+4E00-U+9FFF)."""
    return bool(_HAN_RE.search(text))


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    long_name: str
    html_lang: str
    target_class: str
    structural_labels: dict[str, str]
    contents_labels: dict[str, str]
    prefix_labels: tuple[tuple[str, str], ...]
    footnote_label: str  # contains "{n}"
    bilingual_edition_label: str
    aup_refused_notice: str
    prompt_rules: str
    default_custom_instructions: str
    is_target_text: Callable[[str], bool]


ZH_TW = LanguageProfile(
    code="zh-tw",
    long_name='台灣繁體中文',
    html_lang="zh-Hant",
    target_class="tgt-zh",
    structural_labels=_ZH_TW_STRUCTURAL_LABELS,
    contents_labels=_ZH_TW_CONTENTS_LABELS,
    prefix_labels=_ZH_TW_PREFIX_LABELS,
    footnote_label="註腳 {n}",
    bilingual_edition_label="中英對照",
    aup_refused_notice='本章因 LLM 政策拒答，保留原文未譯',
    prompt_rules=_ZH_TW_PROMPT_RULES,
    default_custom_instructions=_ZH_TW_DEFAULT_CUSTOM_INSTRUCTIONS,
    is_target_text=_zh_tw_is_target_text,
)

_REGISTRY: dict[str, LanguageProfile] = {ZH_TW.code: ZH_TW}


def get_profile(code: str) -> LanguageProfile:
    """Strict lookup (casefolded). Raises ValueError for an unregistered code."""
    try:
        return _REGISTRY[str(code).strip().casefold()]
    except KeyError:
        raise ValueError(f"no language profile registered for {code!r}") from None


def resolve_profile(code: str | None) -> LanguageProfile:
    """Lenient lookup: casefold, and fall back to zh-tw for any unregistered code."""
    return _REGISTRY.get(str(code or "").strip().casefold(), ZH_TW)
