"""Synthetic NCX fixture for the Phase 7 golden case (BUG-016). No book text."""
from __future__ import annotations

NCX = """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="n1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="xhtml/ch1.xhtml"/>
      <navPoint id="n2" playOrder="2">
        <navLabel><text>SLACK</text></navLabel>
        <content src="xhtml/ch1.xhtml#h_slack"/>
      </navPoint>
      <navPoint id="n3" playOrder="3">
        <navLabel><text>Tunneling &amp; Focus</text></navLabel>
        <content src="xhtml/ch1.xhtml#h_tunnel"/>
      </navPoint>
      <navPoint id="n4" playOrder="4">
        <navLabel><text>NO SIBLING</text></navLabel>
        <content src="xhtml/ch1.xhtml#h_nosib"/>
      </navPoint>
      <navPoint id="n5" playOrder="5">
        <navLabel><text>Same Text</text></navLabel>
        <content src="xhtml/ch1.xhtml#h_same"/>
      </navPoint>
    </navPoint>
    <navPoint id="n6" playOrder="6">
      <navLabel><text>Chapter 2</text></navLabel>
      <content src="xhtml/ch2.xhtml"/>
    </navPoint>
  </navMap>
</ncx>
"""

ENTRIES = [
    {"id": "item_001", "original_path": "OPS/xhtml/ch1.xhtml", "first_heading": "Chapter 1",
     "output_strategy": "translate", "original_idref": "ch1",
     "_translations_extra": {"nav_overrides": {"ch1": "Chương 1"}}},
    {"id": "item_002", "original_path": "OPS/xhtml/ch2.xhtml", "first_heading": "Chapter 2",
     "output_strategy": "translate", "original_idref": "ch2",
     "_translations_extra": {"nav_overrides": {"ch2": "Chương 2"}}},
]

# Assembled chapter HTML, keyed by file basename. Mirrors bilingual_rewriter output:
# a source heading with the anchor id, then a `tgt` paragraph.
CHAPTER_HTML = {
    "ch1.xhtml": (
        '<html><body>'
        '<h1>Chapter 1</h1><p class="tgt tgt-vi">Chương 1</p>'
        '<h5 id="h_slack">SLACK</h5><p class="tgt tgt-vi">KHOẢNG ĐỆM</p>'
        '<h5 id="h_tunnel"><em>Tunneling</em> &amp; Focus</h5><p class="tgt tgt-vi">Hiệu ứng <b>đường hầm</b> &amp; tập trung</p>'
        '<h5 id="h_nosib">NO SIBLING</h5><p>plain body</p>'
        '<h5 id="h_same">Same Text</h5><p class="tgt tgt-vi">Same Text</p>'
        '</body></html>'
    ),
    "ch2.xhtml": '<html><body><h1>Chapter 2</h1><p class="tgt tgt-vi">Chương 2</p></body></html>',
}
