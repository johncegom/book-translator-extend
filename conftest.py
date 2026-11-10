"""Skip tests for the cloud-GPU and local-model (ollama/omlx) paths.

The Vietnamese port covers only the Claude Code subagent path
(see docs/plans/2026-11-11-vietnamese-language-profile.md), so these
paths are out of scope. Skipped, not deleted: remove a name from the
list to run it again.
"""
import pytest

OUT_OF_SCOPE_TEST_FILES = {
    # cloud GPU
    "test_cloud_llm.py",
    "test_cloud_llm_colab.py",
    "test_cloud_llm_engine_selfcontained.py",
    "test_adaptive_concurrency_probe.py",
    "test_build_adaptive_probe_load.py",
    # local models
    "test_offline_default_omlx.py",
    "test_omlx_provider.py",
    "test_translate_book_ollama.py",
    "test_translate_book_ollama_multibook.py",
    "test_translate_chapter_cli_omlx.py",
}


def pytest_collection_modifyitems(config, items):
    skip = pytest.mark.skip(reason="out of scope: cloud-GPU / local-model path")
    for item in items:
        if item.path.name in OUT_OF_SCOPE_TEST_FILES:
            item.add_marker(skip)
