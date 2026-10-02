"""Address-scoped fictional name pool; do not turn UI 'fan' into surname 'Fang'."""
from inventory import ROOT,WORK
from kfont import encode

def translations():
    result=[]
    for line in (ROOT/'translation/overlay_generated_names.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        ref,ko=line.split('|',1);name,pos=ref.split(':')
        result.append((name,int(pos,16),ko))
    return result

def apply(data,cm):
    original=(WORK/'assets/COM_SEL.OVL').read_bytes();out=bytearray(data);audit=[]
    for name,pos,ko in translations():
        assert name=='COM_SEL.OVL'
        # This specific name pool is eight-byte aligned, including single-kanji names.
        assert pos%8==0
        end=original.index(0,pos)+1;aligned=(end+7)&~7
        capacity=aligned-pos if original[end:aligned]==b'\0'*(aligned-end) else end-pos
        raw=encode(ko,cm)+b'\0';assert len(raw)<=capacity,(hex(pos),ko)
        out[pos:pos+capacity]=raw.ljust(capacity,b'\0')
        audit.append(dict(file=name,offset=pos,ja=original[pos:end-1].decode('cp932'),ko=ko))
    assert len(out)==len(data)
    return bytes(out),audit
