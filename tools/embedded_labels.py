"""Addressed strings inside reviewed packed records, never binary-wide search."""
import json,re
from inventory import ROOT,WORK
from kfont import encode

def translations():
    src=json.loads((WORK/'embedded_strings_remaining.json').read_text(encoding='utf-8'))
    rows={}
    for line in (ROOT/'translation/embedded_labels.txt').read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        i,k=line.split('|',1);r=src[int(i)]
        rows[r['file'],r['offset']]=(r['ja'],k)
    ui={}
    for f in ['ui','dialogs','extra_ui','screen_ui','overlay_texts','overlay_full']:
        ui.update(json.loads((ROOT/f'translation/{f}.json').read_text(encoding='utf-8')))
    # CP932 has duplicate byte encodings for these extension characters.
    # Match the decoded original at the reviewed address, not re-encoded bytes.
    aliases=json.loads((WORK/'executable_actionable.json').read_text(encoding='utf-8'))
    for i in [7,501,504,515,584,617,1333]:
        r=aliases[i];rows[r['file'],r['offset']]=(r['ja'],ui[r['ja']])
    ui.update({'カーブ！':'커브!','サード！':'3루수!','レフト！':'좌익수!','ライト！':'우익수!','スタート！':'출발!','実戦的な守備':'실전 수비','実戦的な走塁':'실전 주루'})
    a='<RGB 0x7c5400>';b='<RGB 0x7f7f7f>'
    ui.update({a+'５球当てればクリア'+b+'だよ。':a+'5번 맞히면 성공'+b+'이야.',a+'ヒットを４本'+b+'打てばクリアだ。':a+'안타 4개'+b+'면 성공이야.',a+'第２球種'+b+'は<R1>ボタンだよ！':a+'제2구종'+b+'은 <R1> 버튼이야!', '一塁へ送球！':'1루에 송구!','ホームインだ！':'홈인이다!', 'これは'+a+'二塁'+b+'まで行けるよ！':'이건 '+a+'2루'+b+'까지 갈 수 있어!',a+'三塁打'+b+'を狙おう！':a+'3루타'+b+'를 노리자!','二塁ランナーを'+a+'ホーム'+b+'に帰そう！':'2루 주자를 '+a+'홈'+b+'으로 보내자!','タッチアップで'+a+'ホーム'+b+'に帰そう！':'태그업으로 '+a+'홈'+b+'에 가자!'})
    for j,k in [('一塁','1루'),('二塁','2루'),('三塁','3루'),('本塁','홈'),('中継','중계')]:
        for v,w in [('送球','송구'),('牽制','견제')]:ui[a+j+b+'へ'+v+'！']=a+k+b+'에 '+w+'!'
        for v,w in [('ススメ','진루'),('モドレ','귀루')]:
            ui[j+'へ、'+a+v+'！'+b]=k+'로, '+a+w+'!'+b
            ui[j+'走者、'+a+v+'！'+b]=k+' 주자, '+a+w+'!'+b
    for j,k in [('ススメ','진루'),('モドレ','귀루'),('トマレ','정지')]:
        ui[a+j+'！'+b]=a+k+'!'+b
        ui['全員、'+a+j+'！'+b]='모두, '+a+k+'!'+b
    ui.update({'最後は実戦形式だよ。':'마지막은 실전이야.', '打球を使った守備練習だよ。':'타구로 수비 연습이야.', '打球の影と、黄色い落下点をよくみて':'공 그림자와 노란 낙하점을 보고', '<△>ボタンで次の塁へ進む進塁。':'<△> 버튼으로 다음 루에 진루.', '<○>ボタンで前の塁へ戻る帰塁。':'<○> 버튼으로 이전 루에 귀루.', '<L-STICK>左スティックで戻り先の塁を指定して':'<L-STICK> 왼쪽 스틱으로 돌아갈 루를 정해'})
    d=(WORK/'assets/TUTORIAL.OVL').read_bytes()
    # 26 menu records of 116 bytes; 298 dialogue records of 301 bytes.
    positions=list(range(152689,242087,301))+[145298+i*116+j for i in range(26) for j in (0,50)]
    for p in positions:
        key=('TUTORIAL.OVL',p)
        if key in rows:continue
        j=d[p:d.index(0,p)].decode('cp932')
        if not j:continue
        assert j in ui,('untranslated packed field',hex(p),j)
        rows[key]=(j,ui[j])
    return [(f,p,j,k) for (f,p),(j,k) in sorted(rows.items())]

def apply(data,cm,label):
    original=(WORK/label if label=='SLPM_551.58' else WORK/'assets'/label).read_bytes();out=bytearray(data);audit=[]
    for f,p,j,k in translations():
        if f!=label:continue
        raw=original[p:original.index(0,p)+1];assert raw[:-1].decode('cp932')==j
        # Only use the original text bytes; preserve packed metadata and padding.
        dst=encode(k,cm)+b'\0';assert len(dst)<=len(raw),(f,hex(p),j,k,len(dst),len(raw))
        tags=lambda s:re.findall(r'<[^>]+>|%[-+ #0-9.*]*[a-zA-Z]',s)
        assert tags(j)==tags(k),(j,k)
        out[p:p+len(raw)]=dst.ljust(len(raw),b'\0')
        audit.append(dict(file=f,offset=p,ja=j,ko=k))
    return bytes(out),audit

if __name__=='__main__':
    rows=translations()
    (ROOT/'build/embedded_labels.json').write_text(json.dumps([dict(file=f,offset=p,ja=j,ko=k) for f,p,j,k in rows],ensure_ascii=False,indent=2),encoding='utf-8')
    print('Packed text fields:',len(rows))
