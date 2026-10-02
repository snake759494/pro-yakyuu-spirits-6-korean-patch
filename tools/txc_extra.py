"""Additional TXCPACK labels, extracted at actual NUL boundaries.

These short labels are deliberately scoped to TXCPACK data, never executable
code, player names, the phonetic dictionary or the password alphabet.
"""
import json,re,unicodedata
from inventory import ROOT

def translations():
    out={}
    for line in (ROOT/'translation/txc_extra.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        ja,ko=line.split('|',1)
        out[ja.replace('\\n','\n')]=ko.replace('\\n','\n')
    for row in json.loads((ROOT/'work/txc_remaining_full.json').read_text(encoding='utf-8')):
        ja=row['ja'];norm=unicodedata.normalize('NFKC',ja)
        for pattern,ko in [
            (r'(\d+)番手','{}순위'),(r'球種(\d+)','구종{}'),
            (r'項目(\d+)','항목{}'),(r'内容(\d+)','내용{}'),
            (r'選択肢(\d+)','선택지{}'),(r'日付(\d+)','날짜{}'),
            (r'球団名(\d+)','구단명{}'),(r'チーム(\d+)','팀{}'),
            (r'操作(\d+)','조작{}'),(r'設問(\d+)','문제{}'),
            (r'第(\d+)試合','제{}경기'),(r'対戦球団(\d+)','상대구단{}'),
        ]:
            m=re.fullmatch(pattern,norm)
            if m:out[ja]=ko.format(m[1]);break
    return out

if __name__=='__main__':
    out=translations()
    (ROOT/'translation/txc_extra.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=json.loads((ROOT/'work/txc_remaining_full.json').read_text(encoding='utf-8'))
    remaining=[r for r in rows if r['ja'] not in out]
    print(json.dumps({'translated':len(out),'unmapped':remaining},ensure_ascii=False,indent=2))
