"""Check alternate CP932 spellings at string boundaries and literal references."""
import json,struct
from inventory import ROOT,WORK
from literal_refs import starts
from embedded_labels import translations

def main():
    known={(f,p) for f,p,j,k in translations()};ui={}
    for p in (ROOT/'translation').glob('*.json'):
        d=json.loads(p.read_text(encoding='utf-8'))
        if isinstance(d,dict):ui.update({j:k for j,k in d.items() if isinstance(k,str)})
    missing=[]
    for f in [WORK/'SLPM_551.58',*(WORK/'assets').glob('*.OVL')]:
        d=f.read_bytes();lo=struct.unpack_from('<I',d,12)[0] if f.suffix=='.OVL' else 0x2b0000
        positions=set(starts(d,f.name));p=lo
        for raw in d[lo:].split(b'\0'):positions.add(p);p+=len(raw)+1
        for p in positions:
            end=d.find(b'\0',p)
            if end<0:continue
            raw=d[p:end]
            try:j=raw.decode('cp932')
            except UnicodeDecodeError:continue
            if j in ui and raw!=j.encode('cp932') and (f.name,p) not in known:
                missing.append(dict(file=f.name,offset=p,ja=j,ko=ui[j]))
    (ROOT/'build/cp932_alias_audit.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Unhandled alternate CP932 encodings:',len(missing));assert not missing

if __name__=='__main__':main()
