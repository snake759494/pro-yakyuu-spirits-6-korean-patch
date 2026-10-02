"""Keep font counts, CHK offsets, file sizes, and ISO sectors unchanged."""
import json,struct
from analyze import chunks
from inventory import WORK
from kfont import glyph

def configure(elf,chars):
    slots=json.loads((WORK/'font_slots.json').read_text(encoding='utf-8'))
    assert len(chars)<=len(slots),(len(chars),len(slots))
    assigned=[dict(row,hangul=ch) for row,ch in zip(slots,chars)]
    cm={r['hangul']:bytes.fromhex(r['code']) for r in assigned}
    return elf,cm,assigned,None

def patch_font(data,chars,assigned,_):
    out=bytearray(data);found=0
    for name,off,b in chunks(data):
        if not b.startswith(b'PS2 FONT'):continue
        n,w,h=struct.unpack_from('<3I',b,16)
        if n not in (3669,3401,3397):continue
        stride=((w+1)//2)*h
        assert len(b)==28+n*stride
        touched=set()
        for row in assigned:
            idx=row['index'] if n==3669 else row['split_index']
            assert idx<n
            p=off+28+idx*stride
            out[p:p+stride]=glyph(row['hangul'],w,h)
            touched.add(idx)
        for i in range(n):
            if i not in touched:
                p=off+28+i*stride
                assert data[p:p+stride]==out[p:p+stride]
        found+=1
    assert len(out)==len(data)
    return bytes(out),found
