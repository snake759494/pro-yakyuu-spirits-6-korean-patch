"""NUL-boundary TXCPACK coverage and capacity audit, independent of regex catalogs."""
import json,re
from inventory import ROOT,WORK,ISO
from analyze import chunks
from review_queue import translations
from txc_extra import translations as extras
from compact_labels import units

def main():
    t={**translations(),**extras()};rows=[];missing=[];overflow=[]
    inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    noise={'ｸ艾D\uf8f3','艾D\uf8f3','X鎤','艾D\uf8f3\x14','艾D\uf8f3\x01','建\uf8f0\uf8f3建\uf8f0\uf8f3\x03','跏ﾒ\uf8f3\x14'}
    with ISO.open('rb') as f:
        for e in inv['fbd']:
            if not e['name'].endswith('.CHK'):continue
            f.seek(e['offset']);d=f.read(e['size'])
            if not d.startswith(b'CHK ') or b'TXCPACK ' not in d:continue
            for name,off,b in chunks(d):
                if not b.startswith(b'TXCPACK '):continue
                p=0
                for raw in b.split(b'\0'):
                    start=p;p+=len(raw)+1
                    try:j=raw.decode('cp932')
                    except UnicodeDecodeError:continue
                    if not re.search('[ぁ-んァ-ヶ一-龠]',j) or j in noise:continue
                    row=dict(file=e['name'],chunk=name,offset=start,ja=j)
                    if j not in t:missing.append(row);continue
                    cap=len(raw)+1;aligned=(start+cap+3)&~3
                    if b[start+cap:aligned]==b'\0'*(aligned-start-cap):cap=aligned-start
                    size=sum(2 if any('\uac00'<=c<='\ud7a3' for c in u) else len(u.encode('cp932')) for u in units(t[j]))+1
                    row.update(ko=t[j],capacity=cap,encoded_size=size)
                    rows.append(row)
                    if size>cap:overflow.append(row)
    report=dict(translated_occurrences=len(rows),missing=missing,overflow=overflow,binary_false_positives=sorted(noise))
    (ROOT/'build/txc_coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
