"""Localize existing indexed menu atlases with the selected folder font."""
import struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from inventory import ROOT,WORK
from analyze import chunks
from textures import decode,swz
from palette_links import resolve

MAIN=[
 ((0,0,39,19),'대전',16,True),((44,0,144,19),'VP 상점',16,True),
 ((0,19,117,37),'페넌트 레이스',16,True),((0,37,115,56),'트레이닝',16,True),
 ((119,37,202,56),'스피리츠',16,True),((0,56,117,75),'홈런 경쟁',16,True),
 ((0,75,117,93),'유틸리티',16,True),((0,93,110,111),'스피리츠 입문',16,True),
 ((119,91,203,110),'스타덤',16,True),
 ((216,0,266,25),'대전',23,False),((267,0,438,25),'페넌트 레이스',23,False),
 ((216,25,335,49),'스피리츠',23,False),((336,25,485,49),'트레이닝',23,False),
 ((216,49,314,73),'처음부터',23,False),((315,49,410,73),'이어하기',23,False),
 ((216,73,386,98),'유틸리티',23,False),((387,73,510,98),'스타덤',23,False),
 ((216,98,360,123),'VP 상점',23,False),((361,98,510,123),'스피리츠 입문',23,False),
 ((0,110,172,133),'홈런 경쟁',22,False),
]
WBC=[((0,90,166,135),'챔피언십',24,True),((0,136,166,182),'대전',24,True),((0,182,166,228),'유틸리티',24,True),
     ((182,18,326,46),'챔피언십',22,False),((196,64,313,96),'대전',22,False),((215,108,292,137),'유틸리티',19,False)]
POSITIONS=[((26,27,52,60),'우',22,False),((52,27,78,60),'좌',22,False),((78,27,104,60),'양',22,False),
           ((156,27,182,60),'선',22,False),((182,27,208,60),'중',22,False)]
SETUP_HEAD=[((0,i*42,w,i*42+42),s,32,True) for i,(w,s) in enumerate([
    (216,'사용자 설정'),(216,'컨트롤러'),(218,'주루 조작'),(156,'수비 조작'),
    (216,'게임 난이도'),(184,'구속 단계'),(256,'완급 적응 게이지')])]
SETUP_CHOICES=[]
for i,s in enumerate(['내 설정으로','간편 새 설정','상세 설정','왼쪽 스틱','방향키','자동',
                      '직접 조작','포구 자동','쉬움','보통','어려움','느리게','빠르게','표시','숨김']):
    x={1:34,5:96,8:74,11:79}.get(i,0)
    right={1:240,5:181,8:184,11:191}.get(i,256)
    SETUP_CHOICES.append(((x,i*32,right,(i+1)*32),s,25,False))

def palette(pal):
    p=np.frombuffer(pal[160:],np.uint8).reshape(-1,4).copy()
    if len(p)==256:
        ids=np.arange(256);ids=(ids&~24)|((ids&8)<<1)|((ids&16)>>1);p=p[ids]
    p[:,3]=np.minimum(p[:,3].astype(np.uint16)*2,255)
    return p

def indices(tex):
    w,h=struct.unpack_from('<HH',tex,112);a=np.frombuffer(tex[160:],np.uint8)
    if tex[116]==19:return swz.unswizzle8(tex[160:],w,h) if tex[119] else a.reshape(h,w)
    return swz.unswizzle4(tex[160:],w,h) if tex[119] else np.stack([a&15,a>>4],1).reshape(h,w)

def encode_indices(tex,a):
    if tex[116]==19:b=swz.swizzle8(a) if tex[119] else a.tobytes()
    elif tex[119]:b=swz.swizzle4(a)
    else:
        flat=a.reshape(-1);b=(flat[::2]|(flat[1::2]<<4)).tobytes()
    assert len(b)==len(tex)-160
    assert np.array_equal(indices(tex[:160]+b),a)
    return tex[:160]+b

def paint(tex,pal,labels):
    a=indices(tex).copy();p=palette(pal)
    if tex[116]==20:p=p[:16]
    pv=p.astype(np.float32);pv[:,:3]*=pv[:,3:4]/255
    original=decode(tex,pal)
    for item in labels:
        rect,text,size,white=item[:4]
        x0,y0,x1,y1=rect;w=x1-x0;h=y1-y0
        assert 0<=x0<x1<=original.width and 0<=y0<y1<=original.height,(text,rect,original.size)
        if len(item)>4 and item[4]=='country_map':
            # Remove only the neutral Japanese lettering. Keep the colored map
            # beneath/around it; reconstruct hidden pixels from nearby rows.
            source=np.asarray(original).copy();rgb=source[:,:,:3].astype(int)
            map_pixels=(rgb[:,:,2]-rgb[:,:,0]>45)&(rgb[:,:,1]-rgb[:,:,0]>10)&(source[:,:,3]<190)&(source[:,:,3]>0)
            safe=(source[:,:,3]==0)|map_pixels
            textmask=~safe
            crop=source[y0:y1,x0:x1].copy()
            background_mask=np.asarray(Image.fromarray((map_pixels*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.MinFilter(25)))>0
            colors,counts=np.unique(source[map_pixels],axis=0,return_counts=True)
            map_color=colors[counts.argmax()]
            for yy,xx in zip(*np.where(textmask[y0:y1,x0:x1])):
                crop[yy,xx]=map_color if background_mask[y0+yy,x0+xx] else (0,0,0,0)
            canvas=Image.fromarray(crop,'RGBA')
        elif len(item)>4 and item[4]=='inpaint':
            import cv2
            source=np.asarray(original).copy()
            mask=np.zeros(source.shape[:2],np.uint8);mask[y0:y1,x0:x1]=255
            filled=cv2.inpaint(source[:,:,:3],mask,3,cv2.INPAINT_TELEA)
            source[y0:y1,x0:x1,:3]=filled[y0:y1,x0:x1]
            canvas=Image.fromarray(source[y0:y1,x0:x1],'RGBA')
        elif len(item)>4 and isinstance(item[4],tuple) and item[4][0]=='rowfill':
            canvas=Image.new('RGBA',(w,h))
            for yy in range(h):
                color=original.getpixel((item[4][1],y0+yy))
                ImageDraw.Draw(canvas).line((0,yy,w,yy),fill=color)
        else:
            background=original.getpixel(item[4]) if len(item)>4 else (0,0,0,0)
            canvas=Image.new('RGBA',(w,h),background)
        draw=ImageDraw.Draw(canvas)
        stroke=1 if white else 0
        while True:
            font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),size)
            bb=draw.textbbox((0,0),text,font=font,stroke_width=stroke)
            if bb[2]-bb[0]<=w-2 and bb[3]-bb[1]<=h-1:break
            size-=1;assert size>=8,(text,rect)
        x=(w-(bb[2]-bb[0]))//2-bb[0];y=(h-(bb[3]-bb[1]))//2-bb[1]
        draw.text((x,y),text,font=font,fill='white' if white else 'black',stroke_width=stroke,stroke_fill=(0,0,0,210))
        rgba=np.asarray(canvas).reshape(-1,4).astype(np.float32)
        rgba[:,:3]*=rgba[:,3:4]/255
        dist=((rgba[:,None,:]-pv[None,:,:])**2).sum(axis=2)
        a[y0:y1,x0:x1]=dist.argmin(axis=1).reshape(h,w).astype(np.uint8)
    return encode_indices(tex,a)

def patch(data,labels,preview=None,texture='TEX01',palname='PAL01'):
    d={n:(o,b) for n,o,b in chunks(data)}
    off,tex=d[texture]
    pal=resolve({n:b for n,(o,b) in d.items()},texture)
    new=paint(tex,pal,labels)
    out=bytearray(data);out[off:off+len(tex)]=new
    if preview:
        im=decode(new,pal);bg=Image.new('RGBA',im.size,'#a0a0a0');bg.alpha_composite(im);bg.save(preview)
    return bytes(out)

def apply(replacement):
    for name,labels in [('MAINMENU.CHK',MAIN),('WBMAINSEL.CHK',WBC)]:
        data=replacement.get(name,(WORK/'assets'/name).read_bytes())
        replacement[name]=patch(data,labels,ROOT/'build'/('preview_'+name+'.png'))
    name='MENU2D.CHK';data=replacement.get(name,(WORK/'assets'/name).read_bytes())
    replacement[name]=patch(data,POSITIONS,ROOT/'build'/'preview_positions.png','TEX02','PAL02')
    name='EXSETUP.CHK';data=replacement.get(name,(WORK/'assets'/name).read_bytes())
    data=patch(data,SETUP_HEAD,ROOT/'build/preview_setup_head.png','TEX02','PAL02')
    replacement[name]=patch(data,SETUP_CHOICES,ROOT/'build/preview_setup_choices.png','TEX05','PAL05')
    extras = [
        ('NPBWBC.CHK','TEX00','PAL00',[((48,0,282,28),'플레이할 모드를 선택하세요',20,True)]),
        ('ORDERD.CHK','TEX00','PAL00',[((0,3,63,37),'후공',22,True),((64,3,126,37),'선공',22,True)]),
        ('ORDERD.CHK','TEX02','PAL02',[((257,0,314,26),'후공',20,True),((315,0,374,26),'선공',20,True),
            ((252,192,434,255),'상대 타순 설정 중\n잠시 기다려 주세요',17,False)]),
        ('GAME2D.CHK','TEX40','PAL40',[((0,0,108,36),'빠름!',29,True),((0,36,108,72),'늦음!',29,True),
            ((0,74,84,108),'조금',26,True),((0,108,108,128),'타이밍',16,True)]),
        ('GAME2D.CHK','TEX46','PAL46',[
            ((0,0,100,27),'세이프',22,True),((101,0,221,27),'아웃',22,True),
            ((0,27,100,54),'페어',22,True),((104,27,235,54),'파울',22,True),
            ((0,54,247,82),'인필드 플라이',22,True),((0,82,255,110),'인정 2루타',22,True),
            ((0,110,109,137),'타임',22,True),((110,110,248,137),'공수 교대',22,True),
            ((0,137,199,165),'경기 종료',22,True),((0,165,123,194),'무승부',22,True),
            ((125,165,254,194),'투구 연습',22,True)]),
        ('BBMENU.CHK','TEX01','PAL01',[((0,0,33,16),'좌투',14,True),((0,16,33,32),'우투',14,True)]),
    ]
    # The badge icon remains to the left of each text rectangle.
    badge=[(([52,42,60,60,52,52,45][i],8+i*39,176,35+i*39),s,21,True) for i,s in enumerate(
        ['COM 대전','필드 플레이','2인 대전 1P','2인 대전 2P','협력 1P','협력 2P','온라인 대전'])]
    extras.extend([('EXSETUP.CHK','TEX03','PAL03',badge),('OPTPLT.CHK','TEX02','PAL02',badge)])
    skills=[]
    for row,names in enumerate([
        ['번트','','','','존재','위압','평균'],
        ['주루','','','','장타','라인','아치'],
        ['도루','','','','밀기','당김','광각'],
        ['내안','만루','대타','삼진','초구','몰타','끈기'],
        ['몸박','초홈','당김','연속','추가','기회','끝내기'],
        ['기회','','','','주자'],
        ['승운','불운','슬로','강속','후반','막판','릴리스'],
        ['대좌','','','','반응','','견제'],
        ['퀵','','','','폭투','포커','회전'],
        ['볼넷','피홈','강속','','','속구','책임'],
        ['위기','','배분','단기','접전','낮공','선회'],
        ['큰판','요동','제구'],
    ]):
        for col,s in enumerate(names):
            if s:skills.append(((col*32,row*20,min(col*32+32,256),row*20+20),s,14,True))
    extras.extend([
        ('EXSETUP.CHK','IMGT06','IMGP06',[((53,124,84,140),'느림',14,True,(55,141)),((211,124,242,140),'빠름',14,True,(214,141))]),
        ('GAME2D.CHK','TEX00','PAL00',skills),
        ('GAME2D.CHK','TEX06','PAL06',[((70,0,98,16),'장타',13,True),((98,0,128,16),'대우',13,True),((70,17,98,34),'주력',13,True),((98,17,128,34),'번트',13,True),((70,35,98,52),'대좌',13,True)]),
        ('GAME2D.CHK','TEX03','PAL03',[
            ((0,i*20,36,i*20+19),s,15,False,(2,2+i*20)) for i,s in enumerate(['선발','2번','3번','4번','5번','6번','7번','8번','9번','투수','타자'])
        ]+[((40,i*20,74,i*20+19),s,15,False,(2,2)) for i,s in enumerate(['1주','2주','3주'])]
          +[((76,i*20,96,i*20+19),s,15,False,(2,2)) for i,s in enumerate(['투','포','1','2','3','유','좌','중','우','지','타'])]),
        ('GAME2D.CHK','TEX05','PAL05',[((74,17,96,34),'구',16,True)]),
        ('GAME2D.CHK','TEX11','PAL11',[((28,18,48,40),'초',18,True),((48,18,74,40),'말',18,True)]),
        ('GAME2D.CHK','TEX13','PAL13',[((50,18,76,40),'초',18,True),((76,18,106,40),'말',18,True)]),
        ('GAME2D.CHK','TEX16','PAL16',[((71,99,88,119),'월',16,True),((88,99,105,119),'일',16,True)]),
        ('GAME2D.CHK','TEX14','PAL14',[((30,0,99,20),'조작 안내',14,True)]),
        ('GAME2D.CHK','TEX34','PAL34',[((0,0,187,26),'이 타석의 작전',22,True),((112,68,220,96),'공격 작전',23,True),((112,97,220,125),'수비 작전',23,True)]),
        ('GAME2D.CHK','TEX37','PAL37',[((41,90,87,110),'전력',18,True)]),
        ('GEBACK061.CHK','TEX00','PAL00',[((305,3,496,26),'상위 2개 팀 진출',18,True,(310,5)),((18,124,208,145),'1패까지는 가능',18,True,(20,126))]),
        ('GEBACK059.CHK','TEX00','PAL00',[((35,7+i*35,289,34+i*35),'1라운드 '+s+'조',20,True,(37,9+i*35)) for i,s in enumerate('ABCD')]+[((340,27,476,47),'2라운드',18,True,(343,28)),((340,99,476,119),'2라운드',18,True,(343,100))]),
        ('GEBACK060.CHK','TEX00','PAL00',[((34,29,287,52),'2라운드 1조',20,True,(36,30)),((34,101,287,123),'2라운드 2조',20,True,(36,102)),((376,65,486,86),'결승 라운드',18,False,(378,66))]),
        ('GEBACK062.CHK','TEX00','PAL00',[((55,19+i*32,182,39+i*32),s,18,True,(58,20+i*32)) for i,s in enumerate(['2조 1위','1조 2위','1조 1위','2조 2위'])]),
        ('GEBACK063.CHK','TEX00','PAL00',[((337,108,496,129),'승부치기',22,True,(341,110)),((257,99,330,114),'일반 연장',13,False,(258,105))]),
        ('GEBACK064.CHK','TEX00','PAL00',[((25,13,169,36),'연장 13회부터',18,True,(27,15)),((258,13,455,36),'마지막 타자의 앞 타자',17,True,(260,15)),((311,65,486,88),'앞 이닝 마지막 타자',17,True,(314,67))]),
        ('GEBACK065.CHK','TEX00','PAL00',[((203,16+i*44,472,47+i*44),s,23,True,(204,17+i*44)) for i,s in enumerate(['1라운드       70구','2라운드       85구','결승 라운드 100구'])]),
        ('GEBACK066.CHK','TEX00','PAL00',[((62,48,164,66),'준결승에서',16,False,(60,47)),((46,73,177,90),'30구 이상 투구',17,True,(49,74)),((256,69,465,97),'결승 등판 불가',22,True,(259,70))]),
    ])
    for name,tex,pal,labels in extras:
        source=replacement.get(name,(WORK/'assets'/name).read_bytes())
        replacement[name]=patch(source,labels,ROOT/'build'/('preview_'+name+'_'+tex+'.png'),tex,pal)
