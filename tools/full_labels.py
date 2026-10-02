"""Compile reviewed kanji-only labels omitted by the initial kana-filter catalog."""
import json,re,unicodedata,collections
from inventory import ROOT,WORK
from txc_extra import translations as txc
from review_queue import translations as existing
from compact_labels import units

def length(s):
    return 1+sum(2 if any('\uac00'<=c<='\ud7a3' for c in u) else len(u.encode('cp932')) for u in units(s))

def main():
    rows=json.loads((WORK/'executable_actionable.json').read_text(encoding='utf-8'))
    out={};decisions=[]
    for line in (ROOT/'translation/full_labels.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        i,k=line.split('|',1);r=rows[int(i)]
        out[r['ja']]=k.replace('\\n','\n')
    extras=txc()
    for r in rows:
        j=r['ja'];n=unicodedata.normalize('NFKC',j)
        if j in extras:out.setdefault(j,extras[j])
        m=re.fullmatch(r'通算([0-9]+)(登板|勝|奪三振|投球回|試合|本安打|打点|盗塁)',n)
        if m:out[j]='통산'+m[1]+{'登板':'등판','勝':'승','奪三振':'탈삼진','投球回':'투구이닝','試合':'경기','本安打':'안타','打点':'타점','盗塁':'도루'}[m[2]]
        m=re.fullmatch(r'([0-9]+)試合連続(安打|出塁|本塁打|先発勝利)',n)
        if m:out[j]=m[1]+'경기연속'+{'安打':'안타','出塁':'출루','本塁打':'홈런','先発勝利':'선발승'}[m[2]]
    # Real names are selected by their complete identity, not surname guesses.
    players=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    norm=lambda s:re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
    names=collections.defaultdict(list)
    for p in players:
        if p['ko']:names[norm(''.join(p['ja'][:2]))].append(p)
    for r in rows:
        if r['file']!='COM_SEL.OVL' or not 0x124ed0<=r['offset']<0x126e00:continue
        ps=names.get(norm(r['ja']),[])
        if not ps:continue
        p=ps[0];ko=' '.join(p['ko'][:2]);raw=(WORK/'assets'/r['file']).read_bytes();end=raw.index(0,r['offset'])+1;aligned=(end+3)&~3
        cap=aligned-r['offset'] if raw[end:aligned]==b'\0'*(aligned-end) else end-r['offset']
        if length(ko)>cap:ko=''.join(p['ko'][:2])
        if length(ko)>cap:ko=p['ko'][2] if len(p['ko'])>2 else p['ko'][0]
        out[r['ja']]=ko
        decisions.append(dict(file=r['file'],offset=r['offset'],ja=r['ja'],ko=ko,player_index=p['index'],capacity=cap))
    (ROOT/'translation/overlay_full.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'build/extra_real_name_audit.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
    over=[]
    files={}
    for r in rows:
        if r['ja'] not in out:continue
        f=r['file'];d=files.setdefault(f,(WORK/f if f=='SLPM_551.58' else WORK/'assets'/f).read_bytes());p=r['offset'];end=d.index(0,p)+1;aligned=(end+3)&~3
        cap=aligned-p if d[end:aligned]==b'\0'*(aligned-end) else end-p
        k=out[r['ja']]
        if length(k)>cap:over.append(dict(**r,ko=k,capacity=cap,needed=length(k)))
    print('Labels',len(out),'real names',len(decisions))
    (ROOT/'work/full_labels_overflow.json').write_text(json.dumps(over,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Overflows',len(over));print(json.dumps(over,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
