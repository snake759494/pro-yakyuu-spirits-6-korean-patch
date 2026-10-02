"""Compile reviewed event translations and verify embedded commands."""
import json,re
from inventory import ROOT,WORK
from event_layout import normalize

def main():
    out={}
    for path in sorted((ROOT/'translation').glob('events_*.txt')):
        for row in path.read_text(encoding='utf-8').splitlines():
            if not row or row.startswith('#'):continue
            ref,body=row.split('|',1);file,address=ref.split(':');p=int(address,16)
            data=(WORK/'assets'/('GEDATA'+file+'.CHK')).read_bytes()
            assert data[p-1]==0,(ref,'string boundary')
            ja=data[p:data.index(0,p)].decode('cp932')
            first=re.match(r'^(?:<BR>)*(<RGB [^>]+>)',ja)
            last=re.search(r'<(?:NEXTPAGE|NEXTMESS|CLOSENEXT|CLOSE|SELECT[2-6])>$',ja)
            assert last,ref
            ko=(first[1] if first and not body.startswith(first[1]) else '')+body+last[0]
            ko=normalize(ko)
            tags=lambda s:re.findall(r'<(?!BR>)[^>]+>',s)
            assert tags(ja)==tags(ko),(ref,ja,ko)
            out[ja]=ko
    (ROOT/'translation/events.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Reviewed events',len(out))

if __name__=='__main__':main()
