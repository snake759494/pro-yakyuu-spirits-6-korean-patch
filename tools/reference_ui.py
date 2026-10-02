from inventory import ROOT,WORK
import json,collections,re

ref=ROOT.parent/'실황파워풀메이저리그2009/translation'
matches=collections.defaultdict(set)
for file in (ref/'jobs').glob('*.jsonl'):
    output=ref/'out'/file.name
    if not output.exists():continue
    src=[json.loads(s) for s in file.read_text(encoding='utf-8').splitlines() if s]
    dst={r['id']:r['ko'] for r in [json.loads(s) for s in output.read_text(encoding='utf-8').splitlines() if s]}
    for r in src:
        ja=r['jp'];ko=dst.get(r['id'])
        if not ko or ko==ja or '{' in ja or '{' in ko:continue
        if re.search('[\u3040-\u30ff\u4e00-\u9fff]',ko):continue
        if len(ja)<2:continue
        matches[ja].add(ko)
result={ja:next(iter(ks)) for ja,ks in matches.items() if len(ks)==1}
(ROOT/'translation/reference_ui.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Unambiguous reference translations',len(result))
