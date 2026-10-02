"""Japanese personal-name reading transliteration (official kana input only).

Existing manually reviewed and reference-project spellings take precedence.
Foreign players are excluded from this Japanese reading converter.
"""
import json,re
from inventory import ROOT,WORK

BASE=dict(zip('あいうえおかきくけこがぎぐげごさしすせそざじずぜぞたちつてとだぢづでどなにぬねのはひふへほばびぶべぼぱぴぷぺぽまみむめもやゆよらりるれろわゐゑをん',
 '아 이 우 에 오 카 키 쿠 케 코 가 기 구 게 고 사 시 스 세 소 자 지 즈 제 조 타 치 쓰 테 토 다 지 즈 데 도 나 니 누 네 노 하 히 후 헤 호 바 비 부 베 보 파 피 푸 페 포 마 미 무 메 모 야 유 요 라 리 루 레 로 와 이 에 오 ん'.split()))
DIG={}
for root,values in {'き':'캬 큐 쿄','ぎ':'갸 규 교','し':'샤 슈 쇼','じ':'자 주 조','ち':'차 추 초','ぢ':'자 주 조','に':'냐 뉴 뇨','ひ':'햐 휴 효','び':'뱌 뷰 뵤','ぴ':'퍄 퓨 표','み':'먀 뮤 묘','り':'랴 류 료'}.items():
    for small,ko in zip('ゃゅょ',values.split()):DIG[root+small]=ko
INITIAL={'카':'가','키':'기','쿠':'구','케':'게','코':'고','타':'다','테':'데','토':'도','치':'지','차':'자','추':'주','초':'조','캬':'갸','큐':'규','쿄':'교'}
def transliterate(kana):
    s=''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in kana)
    out=[];i=0;previous=''
    while i<len(s):
        c=s[i]
        if c=='ー':i+=1;continue
        if c=='っ':
            if not out:raise ValueError('leading sokuon')
            out[-1]=chr(ord(out[-1])+19);i+=1;previous='';continue
        if c=='ん':
            if not out or (ord(out[-1])-0xac00)%28:raise ValueError('invalid nasal context')
            out[-1]=chr(ord(out[-1])+4);i+=1;previous='';continue
        # Written ou/oo/uu are long vowels, omitted in Korean transcription.
        if c=='う' and previous and previous in 'うくぐすずつづぬふぶぷむゆるおこごそぞとどのほぼぽもよろょゅ':
            i+=1;previous='';continue
        if c=='お' and previous and previous in 'おこごそぞとどのほぼぽもよろょ':
            i+=1;previous='';continue
        pair=s[i:i+2]
        if pair in DIG:ko=DIG[pair];i+=2;previous=pair[-1]
        elif c in BASE:ko=BASE[c];i+=1;previous=c
        else:raise ValueError(f'unsupported kana: {kana}')
        if not out:ko=INITIAL.get(ko,ko)
        out.append(ko)
    return ''.join(out)

def main():
    assert transliterate('あきやま')=='아키야마'
    assert transliterate('こうじ')=='고지'
    assert transliterate('かわさき')=='가와사키'
    assert transliterate('てつや')=='데쓰야'
    assert transliterate('おおた')=='오타'
    assert transliterate('せっつ')=='셋쓰'
    assert transliterate('ちば')=='지바'
    ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    byid={p['index']:p for p in ps}
    readings=json.loads((WORK/'npb/readings.json').read_text(encoding='utf-8'))
    applied=[];pending=[]
    for r in readings:
        p=byid[r['index']]
        if p['ko'] and p.get('match')!='npb_official_kana':continue
        # Japanese kanji names only; never use Japanese rules for foreign names.
        if not all(re.search('[\u4e00-\u9fff]',s) for s in p['ja'][:2]):
            pending.append(r);continue
        k=r['kana'] or '';parts=k.split('・')
        if len(parts)!=2 or not all(re.fullmatch('[ぁ-ゖー]+',s) for s in parts):
            pending.append(r);continue
        try:ko=[transliterate(s) for s in parts]
        except ValueError:pending.append(r);continue
        if len(p['ja'])>2:
            # A registered abbreviation must be reconciled separately.
            pending.append(r);continue
        p.update(ko=ko,match='npb_official_kana',npb=r)
        applied.append(dict(index=p['index'],ja=p['ja'],ko=ko,**{k:v for k,v in r.items() if k!='index'}))
    (ROOT/'translation/players.json').write_text(json.dumps(ps,ensure_ascii=False,indent=2),encoding='utf-8')
    audit=[dict(index=p['index'],ja=p['ja'],ko=p['ko'],**{k:v for k,v in p['npb'].items() if k!='index'}) for p in ps if p.get('match')=='npb_official_kana']
    (ROOT/'translation/npb_name_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    (WORK/'npb/pending.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Official kana transliterations',len(applied),'pending',len(pending),'translated total',sum(bool(p['ko']) for p in ps))

if __name__=='__main__':main()
