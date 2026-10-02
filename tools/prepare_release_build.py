"""Extract private build inputs from the user's checksum-matched original ISO."""
import json,shutil
from inventory import ROOT,WORK,ISO,main as inventory
from apply_release import verify

def main():
    manifest=json.loads((ROOT/'release_manifest.json').read_text(encoding='utf-8'))
    verify(ISO,manifest['source'])
    if not (ROOT/'NanumSquareNeo-cBd.ttf').is_file():
        raise FileNotFoundError('Place NanumSquareNeo-cBd.ttf in the repository root; see docs/FONT_CREDITS.md')
    inventory()
    entries=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    names=json.loads((ROOT/'metadata/extraction_list.json').read_text(encoding='utf-8'))
    byname={e['name']:e for e in entries['fbd']}
    with ISO.open('rb') as src:
        elf=next(e for e in entries['iso'] if e['name']=='SLPM_551.58')
        src.seek(elf['offset']);(WORK/'SLPM_551.58').write_bytes(src.read(elf['size']))
        for name in names:
            e=byname[name];src.seek(e['offset']);(WORK/'assets'/name).write_bytes(src.read(e['size']))
    for p in (ROOT/'metadata').glob('*.json'):
        if p.name!='extraction_list.json':shutil.copy2(p,WORK/p.name)
    (ROOT/'build').mkdir(exist_ok=True)
    print('Private source assets prepared:',len(names))

if __name__=='__main__':main()
