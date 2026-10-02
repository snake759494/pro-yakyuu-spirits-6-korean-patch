"""Extract complete 180-byte player records and compare reference translations."""
from pathlib import Path
import json,unicodedata,collections
from inventory import ROOT,WORK

REF=ROOT.parent/'실황파워풀메이저리그2009/translation/names'
def norm(s):
    return unicodedata.normalize('NFKC',s).replace('・','').replace(' ','').replace('．','.')
def loadref():
    out=[]
    for src in sorted(REF.glob('p[0-9].jsonl')):
        dst=REF/('out_'+src.name)
        if not dst.exists(): continue
        ko={x['id']:x for x in map(json.loads,dst.read_text(encoding='utf-8').splitlines())}
        for x in map(json.loads,src.read_text(encoding='utf-8').splitlines()):
            if x['id'] in ko:out.append(dict(source_file=src.name,ja=x,ko=ko[x['id']]))
    return out
def main():
    b=(WORK/'assets/PLAYERDATA.CHK').read_bytes()
    ref=loadref()
    rows=[]
    for i in range(1280):
        o=32+i*180
        raw=b[o+98:o+140]
        if raw==b'\xcc'*42:continue
        fields=raw.split(b'\0')
        try: names=[s.decode('cp932') for s in fields if s]
        except UnicodeDecodeError:
            names=[s.decode('cp932',errors='backslashreplace') for s in fields if s]
        if not names:continue
        fam=names[0];giv=names[1] if len(names)>1 else ''
        matches=[r for r in ref if norm(r['ja']['fam'])==norm(fam) and norm(r['ja']['giv'])==norm(giv)]
        distinct={(r['ko']['fam'],r['ko']['giv']) for r in matches}
        row=dict(index=i,record_offset=o,name_offset=o+98,name_capacity=42,
                 latin=b[o+80:o+92].split(b'\0')[0].decode('ascii',errors='backslashreplace'),ja=names,
                 ko=None,match='unresolved')
        if len(distinct)==1:
            kf,kg=next(iter(distinct))
            row.update(ko=[kf,kg],match='exact_family_given',reference=matches)
            if len(names)>2:
                ds={r['ko']['disp'] for r in matches if norm(r['ja']['disp'])==norm(names[2])}
                if len(ds)==1:row['ko'].append(next(iter(ds)))
                else:row.update(ko=None,match='display_unresolved')
        rows.append(row)
    target=ROOT/'translation';target.mkdir(exist_ok=True)
    overrides=json.loads((target/'name_overrides.json').read_text(encoding='utf-8'))
    for row in rows:
        key='|'.join(row['ja'][:2])
        ko=overrides['by_index'].get(str(row['index'])) or overrides['by_full_name'].get(key)
        if ko:
            row.update(ko=ko,match='reviewed_identity_override')
    # Extraction must not discard subsequently audited translations.
    if (target/'players.json').exists():
        previous={p['index']:p for p in json.loads((target/'players.json').read_text(encoding='utf-8'))}
        for i,row in enumerate(rows):
            old=previous.get(row['index'])
            if old and old['ja']==row['ja'] and old.get('ko') and not row['ko']:
                rows[i]=old
    (target/'players.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (WORK/'reference_names.json').write_text(json.dumps(ref,ensure_ascii=False,indent=2),encoding='utf-8')
    print(len(rows),'players',dict(collections.Counter(x['match'] for x in rows)))
    print('WBC/late records',dict(collections.Counter(x['match'] for x in rows if x['index']>=900)))
    for x in rows:
        if x['index']>=900 and x['ko'] is None:print(x['index'],x['ja'],x['latin'])

if __name__=='__main__':main()
