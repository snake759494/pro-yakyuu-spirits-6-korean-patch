"""Read the actual ISO and verify encoded UI, player, WBC, and banner contents."""
import json,struct,hashlib
from inventory import ROOT,WORK,ISO,iso_entries
from analyze import chunks
from kfont import encode
from wbc_names import BASE
from build import digest

def main():
    report=json.loads((ROOT/'build/build_report.json').read_text(encoding='utf-8'))
    target=ISO.with_name('Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso')
    assert digest(target)==report['output_sha256']
    cm={c:bytes.fromhex(b) for c,b in json.loads((ROOT/'build/charmap.json').read_text(encoding='utf-8')).items()}
    entries={e['name']:e for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd']}
    entries['SLPM_551.58']=next(e for e in iso_entries() if e['name']=='SLPM_551.58')
    buffers={}
    def read(label):
        if label in buffers:return buffers[label]
        file=label.split('::')[0]
        if file not in buffers:
            e=entries[file]
            with target.open('rb') as f:f.seek(e['offset']);buffers[file]=f.read(e['size'])
        if '::' in label:buffers[label]=next(b for n,o,b in chunks(buffers[file]) if n==label.split('::')[1])
        return buffers[label]
    final={}
    for r in report['strings']:final[(r['file'],r['offset'])]=r
    failures=[]
    for (label,p),r in final.items():
        raw=encode(r['ko'],cm)+b'\0'
        if read(label)[p:p+len(raw)]!=raw:failures.append(r)
    players=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    for p in players:
        raw=b'\0'.join(encode(s,cm) for s in p['ko'])+b'\0';b=read('PLAYERDATA.CHK');off=p['name_offset']
        assert b[off:off+len(raw)]==raw,p['index']
    wbc=json.loads((ROOT/'build/wbc_name_audit.json').read_text(encoding='utf-8'))
    b=read('COM_SEL.OVL')
    for r in wbc['rows']:
        for i,k in enumerate(r['ko']):
            off=struct.unpack_from('<I',b,r['table_offset']+4+i*4)[0]-BASE;raw=encode(k,cm)+b'\0'
            assert b[off:off+len(raw)]==raw,(r['id'],k)
    banners=json.loads((ROOT/'build/banners.json').read_text(encoding='utf-8'))
    for r in banners:
        raw=encode(r['ko'],cm)+b'\0';b=read('SLPM_551.58');assert b[r['offset']:r['offset']+len(raw)]==raw
    result=dict(iso_sha256=report['output_sha256'],unique_ui_locations=len(final),ui_mismatches=failures,
                players_verified=len(players),wbc_players_verified=len(wbc['rows']),banners_verified=len(banners))
    (ROOT/'build/built_text_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));assert not failures

if __name__=='__main__':main()
