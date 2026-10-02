"""Single-character UI labels, limited to reviewed string-table ranges.

Never globally replace a two-byte kanji: the same bytes can occur in numbers,
font maps, IME conversion keys, and real/fictional name data.
"""
import json,re
from inventory import ROOT,WORK
from kfont import encode

RANGES={
 'SLPM_551.58':[(0x2e7fc0,0x2e8140),(0x2f4fc0,0x2f5390),(0x2fa300,0x2fa358),(0x2fb580,0x2fb5a0),(0x2fbc70,0x2fbd98),(0x3016d0,0x3017d0)],
 'COM_MAT.OVL':[(0x11d800,0x127000)],
 'COM_SEL.OVL':[(0x10ac00,0x10c300),(0x118800,0x124a00),(0x128970,0x129e00),(0x12ad60,0x12dd00)],
 'MATCH.OVL':[(0xc9c00,0xcd400)],
 'PENNANT.OVL':[(0x53cd0,0x59400),(0x59f90,0x59f98)],
 'PNSOLO.OVL':[(0x699a0,0x73f40)],
 'PNTEAM.OVL':[(0x32900,0x368a0)],
 'PRACTICE.OVL':[(0x20e00,0x21900)],
 'SPIMATCH.OVL':[(0x19d80,0x19dd0)],
 'SPIRITS.OVL':[(0x73dd0,0x76e00)],
 'SELECT.OVL':[(0x74fd0,0x74fe8)],
 'TRIAL.OVL':[(0x20780,0x20790)],
}

MAP={
 '闘':'투','魂':'혼','こ':'을','め':'담','て':'아','入':'입','一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10',
 '投':'투','捕':'포','遊':'유','左':'좌','中':'중','右':'우','外':'외','打':'타','安':'안','本':'홈','前':'앞','越':'뒤','線':'선','権':'인','走':'주','飛':'뜬','直':'직','邪':'파','併':'병','失':'실','野':'야','送':'송','犠':'희','死':'사','敬':'고','見':'루','空':'헛','振':'삼','逃':'낫','球':'구',
 '月':'월','火':'화','水':'수','木':'목','金':'금','土':'토','日':'일','肩':'어깨','肘':'팔꿈치','腰':'허리','足':'다리',
 '歳':'세','指':'지','白':'흰','赤':'적','黒':'흑','色':'색','形':'형','目':'눈','鼻':'코','口':'입','茶':'갈','緑':'녹','紫':'자','黄':'황','紺':'남','袖':'소매','謎':'?','朝':'아침','昼':'낮','夜':'밤',
 '割':'할','分':'푼','厘':'리','点':'점','回':'회','票':'표','呉':'구레','寮':'숙소','無':'무','粋':'멋','和':'일','洋':'양','位':'위','億':'억','万':'만','風':'풍','芯':'심',
 '%d回':'%d회','%d番 %s':'%d번 %s','%d歳':'%d세','表、':'초,','裏、':'말,','た。':'다.','%d分':'%d무','、%d号 ':',%d호 ','%s%d号 ':'%s%d호 ','号 ':'호 ',
 '５～６回':'5~6회','６～７回':'6~7회','７～８回':'7~8회','８～９回':'8~9회','１～２回':'1~2회',
 '白／Ｄ':'흰/D','白／ＹＳ':'흰/YS','白／Ｂｓ':'흰/Bs','白／ＹＢ':'흰/YB','ＹＳ／赤':'YS/적','ＹＢ／白':'YB/흰',
 '１０割':'10할','　安':'　안','前２':'앞2','越２':'뒤2','線２':'선2','権２':'인2','前３':'앞3','越３':'뒤3','線３':'선3','　本':'　홈',
 '%d年':'%d년','月　':'월　','対　':'대　','- 他':'- 외','名 -':'명 -','%d%d%d票':'%d%d%d표','%d%d票':'%d%d표','%d票':'%d표',
 '打．００%d　':'타.00%d ','打．０%d　':'타.0%d ','打．%d　':'타.%d ','防０．０%d　':'방0.0%d ','防０．%d　':'방0.%d ','防%d．０%d　':'방%d.0%d ','防%d．%d　':'방%d.%d ',
 '%d日':'%d일','%d割':'%d할','%d度':'%d도','走 力':'주 력','投 手':'투 수','球 種':'구 종','終　了':'종　료',
 '投 球 練 習':'투 구 연 습','打 撃 練 習':'타 격 연 습','盗  技':'기술 습득','投 球 練 習＋':'투 구 연 습+','盗  技＋':'기술 습득+','超 神 盗 技':'초신기술습득','夢 盗 技':'꿈의기술','闘 魂 注 入':'투 혼 주 입','剛 球 伝 授':'강 속 전 수','豪 打 伝 授':'강 타 전 수',
 '左１０１ｍ、右１００ｍ':'좌101m,우100m',
}

def translations():
    rows=[]
    for f,ranges in RANGES.items():
        d=(WORK/f if f=='SLPM_551.58' else WORK/'assets'/f).read_bytes()
        for lo,hi in ranges:
            p=lo
            for raw in d[lo:hi].split(b'\0'):
                start=p;p+=len(raw)+1
                try:j=raw.decode('cp932')
                except UnicodeDecodeError:continue
                k=MAP.get(j)
                if f=='SLPM_551.58' and 0x2f4fc0<=start<0x2f5390:
                    k={'燕':'야','巨':'거','中':'주','広':'히','横':'요','神':'한','楽':'라','日':'닛','西':'세','湘':'쇼','韓':'한','台':'대'}.get(j)
                if f=='SLPM_551.58' and 0x2e7fc0<=start<0x2e8140:
                    k={'闘':'투','魂':'혼','こ':'을','め':'담','て':'아','一':'일','球':'구','入':'입'}.get(j)
                if f=='SLPM_551.58' and start==0x2fbd58:k='볼' # Four balls, not numeral four.
                if k is not None:rows.append((f,start,j,k))
    return rows

def apply(data,cm,label):
    original=(WORK/label if label=='SLPM_551.58' else WORK/'assets'/label).read_bytes();out=bytearray(data);audit=[]
    for f,p,j,k in translations():
        if f!=label:continue
        end=p+len(j.encode('cp932'))+1;aligned=(end+3)&~3
        cap=aligned-p if original[end:aligned]==b'\0'*(aligned-end) else end-p
        # The reviewed short-label arrays use eight-byte-aligned C strings.
        # Consume only their existing zero padding; never move a following label.
        aligned8=(end+7)&~7
        if p%8==0 and original[end:aligned8]==b'\0'*(aligned8-end):cap=aligned8-p
        raw=encode(k,cm)+b'\0';assert len(raw)<=cap,(f,hex(p),j,k,len(raw),cap)
        out[p:p+cap]=raw.ljust(cap,b'\0');audit.append(dict(file=f,offset=p,ja=j,ko=k))
    assert len(out)==len(data)
    return bytes(out),audit

if __name__=='__main__':
    rows=translations()
    (ROOT/'build/scoped_short_labels.json').write_text(json.dumps([dict(file=f,offset=p,ja=j,ko=k) for f,p,j,k in rows],ensure_ascii=False,indent=2),encoding='utf-8')
    print('Scoped short labels',len(rows))
