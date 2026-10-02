"""Read raw PS2TEX indexed texture chunks for localization inspection."""
import struct,sys
import numpy as np
from PIL import Image
from analyze import chunks
from inventory import WORK,ROOT
# swz/gsmem are preserved from the user's reference project.
import swz

def decode(tex,pal):
    w,h=struct.unpack_from('<HH',tex,112);psm=tex[116]
    a=np.frombuffer(tex[160:],dtype=np.uint8)
    if psm==20:
        a=swz.unswizzle4(tex[160:],w,h).reshape(-1) if tex[119] else np.stack([a&15,a>>4],axis=1).reshape(-1)
    elif psm==19 and tex[119]:a=swz.unswizzle8(tex[160:],w,h).reshape(-1)
    assert len(a)==w*h,(w,h,psm,len(a))
    p=np.frombuffer(pal[160:],dtype=np.uint8).reshape(-1,4).copy()
    if len(p)==256:
        ids=np.arange(256);ids=(ids&~24)|((ids&8)<<1)|((ids&16)>>1);p=p[ids]
    p[:,3]=np.minimum(p[:,3].astype(np.uint16)*2,255)
    return Image.fromarray(p[a].reshape(h,w,4),'RGBA')

def main():
    filename=sys.argv[1] if len(sys.argv)>1 else 'MENU2D.CHK'
    d={n:b for n,o,b in chunks((WORK/'assets'/filename).read_bytes())}
    out=WORK/'textures'/filename;out.mkdir(exist_ok=True,parents=True)
    pals={b[36:112].split(b'\0')[0]:b for b in d.values() if b.startswith(b'PS2TEX') and b[32:36]==b'pal_'}
    for n,b in d.items():
        if b.startswith(b'PS2TEX') and b[32:36]==b'tex_':
            key=b[36:112].split(b'\0')[0]
            if key in pals:decode(b,pals[key]).save(out/(n+'.png'))

if __name__=='__main__':main()
