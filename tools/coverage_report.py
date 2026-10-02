"""Account for reviewed extraction candidates against the final build audit."""
import json
from inventory import ROOT,WORK

def main():
    report=json.loads((ROOT/'build/build_report.json').read_text(encoding='utf-8'))
    changes=report['strings'];ranges={}
    for r in changes:ranges.setdefault(r['file'],[]).append((r['offset'],r['offset']+len(r['ja'].encode('cp932'))))
    result={'iso_sha256':report['output_sha256'],'candidate_sets':{}}
    for name in ['executable_actionable','embedded_strings_remaining']:
        rows=json.loads((WORK/(name+'.json')).read_text(encoding='utf-8'));audit=[]
        for i,r in enumerate(rows):
            p=r['offset'];f=r['file'];reason=None
            if any(a<=p<b for a,b in ranges.get(f,[])):reason='translated field or interior fragment'
            elif name=='executable_actionable':
                if i in [6,*range(710,727)]:reason='preserved input/conversion character table'
                elif i in [1,2,8,9,10,11,12,13,14,1319,1437,1438]:reason='binary bytes falsely decoded as CP932'
            else:
                if i in [*range(1,70),74,75,76,77]:reason='preserved input/conversion/password table'
                elif i==0:reason='binary bytes falsely decoded as CP932'
                elif i in [70,78,337] and any(a==p+1 for a,b in ranges.get(f,[])):reason='binary prefix followed by translated field'
            audit.append(dict(index=i,**r,resolution=reason or 'UNRESOLVED'))
        result['candidate_sets'][name]={'count':len(rows),'unresolved':[r for r in audit if r['resolution']=='UNRESOLVED'],'rows':audit}
    (ROOT/'build/text_coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:{'count':v['count'],'unresolved':v['unresolved']} for k,v in result['candidate_sets'].items()},ensure_ascii=False,indent=2))
    assert all(not v['unresolved'] for v in result['candidate_sets'].values())

if __name__=='__main__':main()
