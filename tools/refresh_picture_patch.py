"""Refresh reviewed picture chunks in a previously verified, fixed-size build."""
import json,hashlib
import argparse
from collections import defaultdict
from inventory import ISO,ROOT,WORK
from analyze import chunks
from legacy_textures import labels as legacy_labels
from event_picture_labels import labels as event_labels
from menu_textures import paint
from palette_links import resolve
from verify_picture_patch import reviewed_labels

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--file',help='Refresh only this reviewed FBD file')
    args=parser.parse_args()
    target=ISO.parent/'Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
    path=ROOT/'build/build_report.json';report=json.loads(path.read_text(encoding='utf-8'))
    assert report['iso_growth']==0 and digest(target)==report['output_sha256']
    es={e['name']:e for e in json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))['fbd']}
    grouped=defaultdict(list)
    for f,t,ls in reviewed_labels():
        if args.file is None or f==args.file:grouped[f,t].extend(ls)
    assert grouped,'No reviewed textures matched'
    pending=[]
    with ISO.open('rb') as src,target.open('rb') as dst:
        for (f,t),ls in grouped.items():
            e=es[f];src.seek(e['offset']);dst.seek(e['offset'])
            d={n:(o,b) for n,o,b in chunks(src.read(e['size']))};current=dst.read(e['size'])
            off,old=d[t];new=paint(old,resolve({n:b for n,(o,b) in d.items()},t),ls)
            assert len(new)==len(old) and new[:160]==old[:160]
            if current[off:off+len(new)]!=new:pending.append((f,t,e['offset']+off,current[off:off+len(new)],new))
    with target.open('r+b') as dst:
        for f,t,off,old,new in pending:
            dst.seek(off);assert dst.read(len(old))==old
            dst.seek(off);dst.write(new)
    with target.open('rb') as dst:
        for f,t,off,old,new in pending:
            dst.seek(off);assert dst.read(len(new))==new
    old_hash=report['output_sha256'];report['output_sha256']=digest(target)
    report['runtime_verified']=False;report['status']='BUILT_PENDING_RUNTIME_VERIFICATION'
    report.setdefault('picture_refresh_history',[]).append(dict(previous_sha256=old_hash,chunks=[dict(file=f,texture=t) for f,t,*_ in pending]))
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(chunks_changed=len(pending),sha256=report['output_sha256']),indent=2))

if __name__=='__main__':main()
