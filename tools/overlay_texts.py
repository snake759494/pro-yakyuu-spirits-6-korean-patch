"""Compile source-addressed overlay translations; check every formatting command."""
import json,re
from inventory import ROOT,WORK
from compact_labels import units

def main():
    out={};oversize=[]
    for path in sorted((ROOT/'translation').glob('overlay_*.txt')):
        if path.name=='overlay_generated_names.txt':continue
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line or line.startswith('#'):continue
            ref,ko=line.split('|',1);file,pos=ref.split(':');pos=int(pos,16)
            d=(WORK/file if file=='SLPM_551.58' else WORK/'assets'/file).read_bytes();ja=d[pos:d.index(0,pos)].decode('cp932')
            ko=ko.replace('\\n','\n').replace('\\r','\r').replace('\\t','\t')
            # The pennant ticker consumes two-byte glyphs. Keep printf commands
            # in ASCII, but use the full-width alphabet for displayed text.
            if file=='PENNANT.OVL' and 0x550e0<=pos<=0x55ad0:
                ko=''.join(part if part.startswith('%') else ''.join(
                    '\u3000' if c==' ' else chr(ord(c)+0xfee0) if '!'<=c<='~' else c
                    for c in part) for part in re.split(r'(%[-+ #0-9.*]*[a-zA-Z])',ko))
            tags=lambda s:re.findall(r'\\C[0-9A-Fa-f]{6}|\\c\d|<(?!BR>)[^>]+>|%[-+ #0-9.*]*[a-zA-Z]|\$\([^)]*\)|\$[a-zA-Z]',s)
            assert tags(ja)==tags(ko),(ref,ja,ko)
            raw=ja.encode('cp932')+b'\0';end=pos+len(raw);aligned=(end+3)&~3
            capacity=aligned-pos if d[end:aligned]==b'\0'*(aligned-end) else len(raw)
            needed=1+sum(2 if all('\uac00'<=ch<='\ud7a3' for ch in c) else len(c.encode('cp932')) for c in units(ko))
            if needed>capacity:oversize.append(dict(ref=ref,ko=ko,needed=needed,capacity=capacity))
            out[ja]=ko
    # Exact, anchored record-goal templates; numeric thresholds remain intact.
    stats={'安打':'안타','二塁打':'2루타','三塁打':'3루타','本塁打':'홈런','打点':'타점','盗塁':'도루','犠打':'희생번트','勝':'승','セーブ':'세이브','ホールド':'홀드','奪三振':'탈삼진','完投':'완투'}
    for row in json.loads((WORK/'overlay_strings.json').read_text(encoding='utf-8')):
        j=row['ja'];m=re.fullmatch(r'シーズン([０-９]+)('+ '|'.join(stats)+r')到達',j)
        if m:out[j]='시즌 '+m[1]+stats[m[2]]+' 달성'
        m=re.fullmatch(r'シーズン([０-９]+)守備機会（([遊二三外])）到達',j)
        if m:out[j]='시즌 '+m[1]+'수비 기회('+{'遊':'유','二':'2','三':'3','外':'외'}[m[2]]+') 달성'
        m=re.fullmatch(r'([０-９]+)試合連続(ホールド|セーブ)',j)
        if m:out[j]=m[1]+'경기연속 '+stats[m[2]]
        m=re.fullmatch(r'([０-９]+)イニング連続無失点',j)
        if m:out[j]=m[1]+'이닝 연속 무실점'
    (ROOT/'translation/overlay_texts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Reviewed overlay strings',len(out))
    print('Oversize:',json.dumps(oversize,ensure_ascii=False))

if __name__=='__main__':main()
