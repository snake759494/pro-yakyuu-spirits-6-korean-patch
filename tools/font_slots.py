"""Audit unreferenced first-level Kanji slots for fixed-size font localization."""
import json,re
from inventory import ROOT,WORK,ISO
from analyze import chunks
from kfont import linear,inverse

def main():
    rows=json.loads((WORK/'elf_strings.json').read_text(encoding='utf-8'))+json.loads((WORK/'overlay_strings.json').read_text(encoding='utf-8'))
    used=set(''.join(r['ja'] for r in rows))
    for p in json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8')):
        used.update(''.join(p['ja']))
    pattern=re.compile(rb'(?:[\x09\x0a\x0d\x20-\x7e]|[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){4,}\x00')
    inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    extra=[]
    with ISO.open('rb') as f:
        for e in inv['fbd']:
            if not e['name'].endswith('.CHK') or e['name']=='PLAYERDATA.CHK':continue
            f.seek(e['offset']);d=f.read(e['size'])
            if not d.startswith(b'CHK '):continue
            for name,off,b in chunks(d):
                if b.startswith((b'PS2',b'MOT',b'LITTJIF')):continue
                for m in pattern.finditer(b):
                    if m.start() and b[m.start()-1]!=0:continue
                    try:s=m.group()[:-1].decode('cp932')
                    except UnicodeDecodeError:continue
                    if not re.search('[ぁ-ヿ]',s):continue
                    if sum('ぁ'<=c<='ヿ' or '一'<=c<='鿿' for c in s)<len(s)*.35:continue
                    used.update(s);extra.append(dict(file=e['name'],chunk=name,ja=s))
    slots=[]
    for i in range(2965):
        code=inverse(linear(b'\x88\x9f')+i);ch=code.decode('cp932')
        if ch not in used:slots.append(dict(original=ch,code=code.hex(),index=611+i,split_index=376+i))
    (WORK/'font_slots.json').write_text(json.dumps(slots,ensure_ascii=False,indent=2),encoding='utf-8')
    (WORK/'asset_strings.json').write_text(json.dumps(extra,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Unused audited slots',len(slots),'additional strings',len(extra))

if __name__=='__main__':main()
