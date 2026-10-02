"""Resolve PS2TEX palettes, including legacy CP4/CP8 resource names."""
import re
from functools import lru_cache

@lru_cache(None)
def external_palette(filename,palname):
    import json
    from inventory import WORK,ISO
    from analyze import chunks
    e=next(e for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd'] if e['name']==filename)
    with ISO.open('rb') as f:
        f.seek(e['offset']);d={n:b for n,_,b in chunks(f.read(e['size']))}
    return d[palname]

def resolve(d,texture):
    tex=d[texture];key=tex[36:112].split(b'\0')[0]
    pals={n:b for n,b in d.items() if b.startswith(b'PS2TEX') and b[32:36]==b'pal_'}
    matches=[b for b in pals.values() if b[36:112].split(b'\0')[0]==key]
    if matches:
        assert all(b==matches[0] for b in matches),(texture,key)
        return matches[0]
    # These chunk names explicitly pair legacy texture and palette resources.
    names=[]
    if texture.startswith('TEX'):names.append('PAL'+texture[3:])
    if texture.endswith('T'):names.append(texture[:-1]+'P')
    if texture.endswith('B'):names.extend([texture[:-1]+'C',texture[:-1]+'C0'])
    for n in names:
        if n in pals:
            b=pals[n];assert len(b)-160 in ([64,1024] if tex[116]==20 else [1024]),(texture,n)
            return b
    normalized=lambda b:re.sub(rb'_CP[48]_',b'_',b)
    matches=[b for b in pals.values() if normalized(b[36:112].split(b'\0')[0])==normalized(key)]
    if len(matches)==1:return matches[0]
    if key.startswith(b'GAME_GMsitutelop_'):
        return external_palette('GTLPTA00.CHK','PAL00')
    if key.startswith(b'PRETEM_GMplayball_kaisen_'):
        return external_palette('PREKAIPA.CHK','PAL00')
    if key.startswith(b'AURORA_') and list(pals)==['0000P']:
        return pals['0000P']
    if key.startswith(b'ENDING_sr_') and 'SR002P' in pals:
        return pals['SR002P']
    raise ValueError(('Unresolved palette',texture,key,list(pals)))
