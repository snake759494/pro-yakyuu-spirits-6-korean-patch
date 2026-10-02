"""Remove instruction-byte false positives from the original font audit.

The original scan included MIPS instructions decoded as one Japanese character
plus ASCII garbage. Keep all data-area candidates, all meaningful consecutive
Japanese code-area candidates, original player names, asset strings and every
complete event message. Append new slots so earlier audited slots retain order.
"""
import json,re,struct
from inventory import ROOT,WORK
from kfont import inverse,linear

def main():
    rows=json.loads((WORK/'elf_strings.json').read_text(encoding='utf-8'))+json.loads((WORK/'overlay_strings.json').read_text(encoding='utf-8'))
    bounds={p.name:struct.unpack_from('<I',p.read_bytes(),12)[0] for p in (WORK/'assets').glob('*.OVL')}
    used=set();excluded=[]
    for row in rows:
        lower=bounds.get(row.get('file'),0x2b0000)
        if row['offset']<lower and not re.search('[ぁ-ヿ一-鿿]{2}',row['ja']):
            excluded.append(row);continue
        used.update(row['ja'])
    for file in ['asset_strings.json','event_catalog.json']:
        for row in json.loads((WORK/file).read_text(encoding='utf-8')):used.update(row['ja'])
    for row in json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8')):used.update(''.join(row['ja']))
    original=WORK/'font_slots_initial.json'
    if not original.exists():original.write_bytes((WORK/'font_slots.json').read_bytes())
    old=json.loads(original.read_text(encoding='utf-8'));previous={r['original'] for r in old};extra=[]
    for i in range(2965):
        code=inverse(linear(b'\x88\x9f')+i);ch=code.decode('cp932')
        if ch not in used and ch not in previous:
            extra.append(dict(original=ch,code=code.hex(),index=611+i,split_index=376+i))
    assert all(x['original'] not in used for x in extra)
    (WORK/'font_slots.json').write_text(json.dumps(old+extra,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(previous_slots=len(old),added_slots=len(extra),total_slots=len(old+extra),excluded_instruction_candidates=excluded,added=extra)
    (WORK/'font_expansion_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Audited slots',len(old),'->',len(old+extra))

if __name__=='__main__':main()
