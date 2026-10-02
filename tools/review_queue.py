"""Refresh the untranslated overlay queue from source catalogs and build inputs."""
import json,re,struct,collections,sys
from inventory import ROOT,WORK

def translations():
    names=re.findall(r"translation/([^']+\.json)",(ROOT/'tools/build.py').read_text(encoding='utf-8'))
    t={}
    for name in names:
        data=json.loads((ROOT/'translation'/name).read_text(encoding='utf-8'))
        if isinstance(data,dict):t.update(data)
    t.update({j.replace('\r\n','\n'):k.replace('\r\n','\n') for j,k in list(t.items())})
    return t

def main():
    t=translations();seen=set();out=[]
    from scoped_names import translations as scoped
    addressed={(f,p) for f,p,k in scoped()}
    files={p.name:p.read_bytes() for p in (WORK/'assets').glob('*.OVL')}
    for row in json.loads((WORK/'overlay_strings.json').read_text(encoding='utf-8')):
        d=files[row['file']];j=row['ja'];p=row['offset']
        if (row['file'],p) in addressed:continue
        if p<struct.unpack_from('<I',d,12)[0] or j in t or j in seen:continue
        if not re.search('[ぁ-んァ-ヶ一-龠]{2}',j):continue
        seen.add(j);out.append(row)
    (WORK/'overlay_remaining.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Unique remaining',len(out),dict(collections.Counter(x['file'] for x in out)))
    if len(sys.argv)>1:
        rows=[r for r in out if r['file']==sys.argv[1]]
        start=int(sys.argv[2]) if len(sys.argv)>2 else 0
        for r in rows[start:start+100]:print(f"{r['file']}:{r['offset']:x}|{r['ja']!r}")

if __name__=='__main__':main()
