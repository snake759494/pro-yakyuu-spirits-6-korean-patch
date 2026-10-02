"""Extend full Japanese fonts with Korean, preserving original reachable glyphs.

Two duplicate symbols in the game's range table are unreachable (the preceding
range already matches them). Reuse this two-slot range for the final Japanese
range, then use the final range for appended Korean glyphs. The glyph count
stays below 6000 so the engine retains its 114-range lookup path.
"""
import struct,json
import numpy as np
from PIL import Image,ImageFont,ImageDraw
from inventory import ROOT,WORK
from analyze import chunks
from compact_labels import units

TABLE=0x2b4980
def linear(code):
    a=int.from_bytes(code,'little')
    if a&0x8000:a=(a-256)&65535
    if a&255>=224:a=(a-64)&65535
    a=(a-16513)&65535
    return (a>>8)+(a&255)*188
def inverse(n):
    a=((n%188)<<8)|(n//188)
    a=(a+16513)&65535
    if a&255>=160:a=(a+64)&65535
    if a>=32512:a=(a+256)&65535
    return a.to_bytes(2,'little')
def ranges(elf):
    return [(elf[TABLE+i*12+4:TABLE+i*12+6],struct.unpack_from('<I',elf,TABLE+i*12+8)[0]) for i in range(114)]
def mapping(rs):
    out={};idx=0
    for code,count in rs:
        for j in range(count):out.setdefault(inverse(linear(code)+j),idx+j)
        idx+=count
    return out
def configure(elf,chars):
    old=ranges(elf)
    assert old[6]==(b'\x81\x7b',2) and old[-1]==(b'\x98\xf0',1)
    assert sum(n for _,n in old)==3669
    out=bytearray(elf)
    out[TABLE+6*12+4:TABLE+6*12+6]=old[-1][0]
    out[TABLE+113*12+4:TABLE+113*12+6]=b'\xf0\x40'
    struct.pack_into('<I',out,TABLE+113*12+8,len(chars))
    new=ranges(out)
    before,after=mapping(old),mapping(new)
    assert set(before)<=set(after)
    for code,idx in before.items():
        assert after[code]==(146 if code==b'\x98\xf0' else idx)
    charmap={ch:inverse(linear(b'\xf0\x40')+i) for i,ch in enumerate(chars)}
    assert all(after[code]==3668+i for i,code in enumerate(charmap.values()))
    assert 3668+len(chars)<6000
    return bytes(out),charmap,before,after
def glyph(ch,w,h):
    render_w=w*len(ch)
    im=Image.new('L',(render_w,h),0)
    font=ImageFont.truetype(str(ROOT/'NanumSquareNeo-cBd.ttf'),h-2)
    draw=ImageDraw.Draw(im)
    box=draw.textbbox((0,0),ch,font=font)
    x=(render_w-(box[2]-box[0]))//2-box[0]
    y=(h-(box[3]-box[1]))//2-box[1]
    draw.text((x,y),ch,font=font,fill=255)
    if len(ch)>1:im=im.resize((w,h),Image.Resampling.LANCZOS)
    a=(np.asarray(im).astype(np.uint16)+8)//17
    assert a.max()>0
    return (a[:,::2]|(a[:,1::2]<<4)).astype(np.uint8).tobytes()
def patch_font(data,chars,before,after):
    out=bytearray(data[:16]);found=0
    for name,off,b in chunks(data):
        if b.startswith(b'PS2 FONT') and struct.unpack_from('<I',b,16)[0]==3669:
            n,w,h=struct.unpack_from('<3I',b,16);stride=((w+1)//2)*h
            assert len(b)==28+n*stride and w%2==0
            raw=bytearray(b[28:]);last=raw[3668*stride:3669*stride]
            raw[146*stride:147*stride]=last
            raw[3668*stride:]=b''.join(glyph(ch,w,h) for ch in chars)
            head=bytearray(b[:28]);struct.pack_into('<I',head,16,3668+len(chars))
            replacement=bytes(head)+bytes(raw)
            for code,oldidx in before.items():
                ni=after[code]
                assert b[28+oldidx*stride:28+(oldidx+1)*stride]==raw[ni*stride:(ni+1)*stride]
            b=replacement;found+=1
        # CHK payloads have a mandatory FF terminator included in `used`.
        # Even word-aligned PS2TEX payloads reserve a full extra 16-byte block.
        capacity=(17+len(b)+15)//16*16
        out+=name.encode('ascii').ljust(8,b'\0')+struct.pack('<2I',capacity,len(b)+1)+b
        out+=b'\xff'+b'\xcc'*(capacity-17-len(b))
    out+=b'CHUNKEND'+b'\0'*8
    struct.pack_into('<I',out,12,len(out))
    return bytes(out),found
def encode(s,cm):
    return b''.join(cm[ch] if ch in cm else ch.encode('cp932') for ch in units(s))
