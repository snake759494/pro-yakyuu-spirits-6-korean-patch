"""Translate the 300 fixed cheer records, preserving their player IDs and colors."""
import json
from inventory import ROOT,WORK
from kfont import encode

START=0x2e42d0
COUNT=300
STRIDE=52

def translations():
    rows={}
    for line in (ROOT/'translation/banners.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        i,s=line.split('|',1);i=int(i)
        assert i not in rows
        rows[i]=s
    assert set(rows)==set(range(COUNT))
    return rows

def apply(data,cm):
    original=(WORK/'SLPM_551.58').read_bytes();out=bytearray(data);audit=[]
    for i,ko in translations().items():
        base=START+i*STRIDE;p=base+3;end=base+STRIDE
        nul=original.index(0,p,end)
        assert original[nul:end]==b'\0'*(end-nul)
        ja=original[p:nul].decode('cp932')
        raw=encode(ko,cm)+b'\0'
        assert len(raw)<=49,(i,ko,len(raw))
        out[p:end]=raw.ljust(49,b'\0')
        assert out[base:p]==original[base:p]
        audit.append(dict(index=i,offset=p,ja=ja,ko=ko))
    return bytes(out),audit
