"""Read final ISO and independently check all new picture bytes and boundaries."""
import json,hashlib
from collections import defaultdict
from inventory import ISO,WORK,ROOT
from analyze import chunks
from menu_textures import paint,indices
from palette_links import resolve
from legacy_textures import labels as legacy_labels
from event_picture_labels import labels as event_labels
from mode_textures import labels as mode_labels

def reviewed_labels():
    return legacy_labels()+event_labels()+[row for row in mode_labels() if row[0]=='PNTEAMINFO.CHK' and row[1]=='TEX02']

def main():
    target=ISO.parent/'Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
    es={e['name']:e for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd']}
    grouped=defaultdict(list)
    for f,t,ls in reviewed_labels():grouped[f,t].extend(ls)
    failures=[];checked=[]
    with ISO.open('rb') as src,target.open('rb') as dst:
        for (f,t),ls in grouped.items():
            e=es[f];src.seek(e['offset']);dst.seek(e['offset'])
            original={n:b for n,o,b in chunks(src.read(e['size']))}
            built={n:b for n,o,b in chunks(dst.read(e['size']))}
            expected=paint(original[t],resolve(original,t),ls)
            if expected!=built[t]:failures.append([f,t,'picture content differs from reviewed source'])
            import numpy as np
            before=indices(original[t]);after=indices(built[t])
            allowed=np.zeros(before.shape,dtype=bool)
            for (x0,y0,x1,y1),*rest in ls:allowed[y0:y1,x0:x1]=True
            if not np.array_equal(before[~allowed],after[~allowed]):failures.append([f,t,'pixels outside reviewed rectangles changed'])
            if original[t][:160]!=built[t][:160]:failures.append([f,t,'texture header changed'])
            checked.append(dict(file=f,texture=t,rectangles=len(ls),sha256=hashlib.sha256(built[t]).hexdigest()))
    with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    report=dict(iso_sha256=digest,atlases=len(checked),rectangles=sum(x['rectangles'] for x in checked),failures=failures,checked=checked)
    (ROOT/'build/picture_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checked'},ensure_ascii=False,indent=2))
    assert not failures

if __name__=='__main__':main()
