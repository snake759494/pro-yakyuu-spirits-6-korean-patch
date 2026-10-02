"""Extract selected atlases and make visual audit sheets from original ISO."""
import sys,json,math
from inventory import WORK,ISO
from analyze import chunks
from textures import decode
from palette_links import resolve
from PIL import Image,ImageDraw
names=sys.argv[2:];inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'));imgs=[]
with ISO.open('rb') as f:
 for n in names:
  n=n.removesuffix('.CHK')+'.CHK';e=next((e for e in inv['fbd'] if e['name']==n),None)
  if not e:continue
  f.seek(e['offset']);d=list(chunks(f.read(e['size'])));pals={v[36:112].split(b'\0')[0]:v for _,_,v in d if v.startswith(b'PS2TEX') and v[32:36]==b'pal_'}
  for t,_,v in d:
   if not(v.startswith(b'PS2TEX') and v[32:36]==b'tex_'):continue
   key=v[36:112].split(b'\0')[0]
   try:im=decode(v,resolve({a:b for a,_,b in d},t))
   except:continue
   op=WORK/'textures'/n;op.mkdir(exist_ok=True,parents=True);im.save(op/(t+'.png'));imgs.append((n,t,im))
for page in range(math.ceil(len(imgs)/24)):
 sheet=Image.new('RGB',(1200,1800),'#999999');dr=ImageDraw.Draw(sheet)
 for i,(n,t,im) in enumerate(imgs[page*24:page*24+24]):
  x=i%4*300;y=i//4*300;im.thumbnail((296,275));sheet.paste(im,(x,y+24),im);dr.text((x,y),n+' '+t,fill='black')
 sheet.save(WORK/f'{sys.argv[1]}_{page}.png')
print('textures',len(imgs),'pages',math.ceil(len(imgs)/24))
