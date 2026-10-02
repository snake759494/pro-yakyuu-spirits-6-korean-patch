"""Exact-label ligatures for fixed-size labels; no record relocation."""
import json
from pathlib import Path
LABELS = {
    '가마가야': ('가마', '가', '야'),
    '소데가우라': ('소데', '가우', '라'),
    '시즈오카어묵': ('시즈', '오', '카', '어', '묵'),
    '오코노미야키': ('오코', '노', '미', '야', '키'),
    '사와무라상': ('사와', '무라', '상'),
}
_extra=Path(__file__).resolve().parents[1]/'translation/compact_labels.json'
if _extra.exists():LABELS.update({k:tuple(v) for k,v in json.loads(_extra.read_text(encoding='utf-8')).items()})
def units(text):
    # Compact only a complete label, never syllables inside ordinary prose.
    return LABELS.get(text, tuple(text))
def extra_glyphs(texts):
    return {u for text in texts for u in units(text) if len(u)>1}
