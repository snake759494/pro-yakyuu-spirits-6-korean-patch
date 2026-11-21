"""In-game score bug team letters (TEAM_<code>_<kit>.CHK :: UP04T, 32x32).

The originals are one katakana/kanji per team (ソ, 横, 楽 ...). Flags and
three-letter country codes are left untouched.
"""
import json
from inventory import ISO,WORK
from analyze import chunks
from menu_textures import paint

MARKS={'BS':'오','C':'히','CL':'센','D':'주','E':'라','EL':'이','F':'닛','G':'거',
       'H':'소','L':'세','M':'롯','PL':'퍼','T':'한','WL':'웨','YB':'요','YS':'야'}

def targets():
    out=[]
    for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd']:
        n=e['name']
        if not (n.startswith('TEAM_') and n.endswith('.CHK')):continue
        code=n[5:-4].rsplit('_',1)[0]
        if code in MARKS:out.append((n,MARKS[code]))
    return out

def apply(replacement):
    entries={e['name']:e for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd']}
    done=0
    with ISO.open('rb') as src:
        for name,mark in targets():
            data=replacement.get(name)
            if data is None:
                e=entries[name];src.seek(e['offset']);data=src.read(e['size'])
            d={n:(o,b) for n,o,b in chunks(data)}
            off,tex=d['UP04T'];pal=d['UP04P'][1]
            new=paint(tex,pal,[((0,0,32,32),mark,26,True)])
            out=bytearray(data);out[off:off+len(tex)]=new
            replacement[name]=bytes(out);done+=1
    return done
