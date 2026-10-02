"""Relocate WBC display names inside the existing COM_SEL literal storage.

The 448 rows have player ID + family/given/display/uniform/number pointers.
Uniform lettering and uniform numbers retain their original ASCII strings.
"""
import json,struct,collections
from inventory import ROOT,WORK
from kfont import encode

BASE=0x1dcc000
START=0x10f7e0
COUNT=448

def rows():
    b=(WORK/'assets/COM_SEL.OVL').read_bytes()
    pd=(WORK/'assets/PLAYERDATA.CHK').read_bytes()
    players=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    byid={struct.unpack_from('<H',pd,p['record_offset']+72)[0]:p for p in players}
    result=[]
    for i in range(COUNT):
        off=START+24*i;v=struct.unpack_from('<6I',b,off);p=byid[v[0]]
        strings=[b[x-BASE:b.index(0,x-BASE)].decode('cp932') for x in v[1:]]
        fam,giv=p['ko'][:2];display=p['ko'][2] if len(p['ko'])>2 else fam
        n=p['index']
        # Full Korean/Chinese names, including late roster replacements.
        if 925<=n<=950 or 830<=n<=853 or 1174<=n<=1200 or n in (329,1148,1149) or (strings[2] in ['T H Im','H W Jong','C Y Lim']):
            display=fam+giv
        elif strings[2]!=strings[0] and len(p['ko'])==2:
            # Preserve the source's disambiguation of players sharing a family name.
            display=giv[0]+'.'+fam if giv else fam
        result.append(dict(table_offset=off,id=v[0],index=n,pointers=list(v[1:]),original=strings,ko=[fam,giv,display]))
    return b,result

def apply(data,cm):
    original,rs=rows();out=bytearray(data)
    names={p-BASE for r in rs for p in r['pointers'][:3]}
    reserved={p-BASE for r in rs for p in r['pointers'][3:]}
    names-=reserved
    # Every pointer to the reclaimed literal must belong to the audited table.
    for off in range(0,len(original)-3,4):
        value=struct.unpack_from('<I',original,off)[0]-BASE
        if value in names:assert START<=off<START+24*COUNT,(off,value)
    regions=[]
    for off in sorted(names):
        end=original.index(0,off)+1;end=(end+7)&~7
        assert original[original.index(0,off):end]==b'\0'*(end-original.index(0,off))
        assert not any(off<=p<end for p in reserved)
        if regions and regions[-1][1]==off:regions[-1][1]=end
        else:regions.append([off,end])
    strings={encode(s,cm)+b'\0' for r in rs for s in r['ko']}
    free=[r[:] for r in regions];allocated={}
    for s in sorted(strings,key=lambda s:(-len(s),s)):
        choices=[(hi-lo,i) for i,(lo,hi) in enumerate(free) if hi-lo>=len(s)]
        assert choices,('name storage exhausted',sum(len(x) for x in strings),sum(hi-lo for lo,hi in regions))
        _,i=min(choices);lo,hi=free[i];allocated[s]=lo;free[i][0]+=len(s)
    for lo,hi in regions:out[lo:hi]=b'\0'*(hi-lo)
    for s,off in allocated.items():out[off:off+len(s)]=s
    for r in rs:
        for j,s in enumerate(r['ko']):
            raw=encode(s,cm)+b'\0';off=allocated[raw]
            struct.pack_into('<I',out,r['table_offset']+4+j*4,BASE+off)
            assert out[off:off+len(raw)]==raw
        assert out[r['table_offset']+16:r['table_offset']+24]==original[r['table_offset']+16:r['table_offset']+24]
    assert len(out)==len(original)
    audit=dict(players=len(rs),storage_available=sum(hi-lo for lo,hi in regions),storage_used=sum(map(len,strings)),rows=rs)
    (ROOT/'build/wbc_name_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    return bytes(out)
