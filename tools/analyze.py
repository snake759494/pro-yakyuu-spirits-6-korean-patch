from pathlib import Path
import json, struct, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from inventory import ROOT, WORK

def chunks(data):
    assert data[:4] == b'CHK '
    off = 16
    while off + 16 <= len(data):
        name = data[off:off+8].rstrip(b'\0').decode('ascii')
        size, used = struct.unpack_from('<2I',data,off+8)
        if name == 'CHUNKEND':
            break
        assert size >= 16 and off+size <= len(data)
        yield name, off+16, data[off+16:off+16+used-1]
        off += size

def font_preview():
    data = (WORK/'assets/BBFONT.CHK').read_bytes()
    name, off, b = next(chunks(data))
    n,w,h = struct.unpack_from('<3I',b,16)
    print('font',n,w,h,len(b),28+n*w*h//2)
    pix = np.frombuffer(b[28:28+n*w*h//2],dtype=np.uint8)
    arr = np.stack([pix&15,pix>>4],axis=1).reshape(n,h,w)*17
    sheet = Image.new('RGB',(32*38,16*45),'#222222')
    draw = ImageDraw.Draw(sheet)
    for i in range(512):
        x,y=(i%32)*38,(i//32)*45
        sheet.paste(Image.fromarray(arr[i]),(x,y))
        draw.text((x,y+24),str(i),fill='white')
    sheet.save(WORK/'font_original.png')
    samples = Image.new('RGB',(950,9*100),'#152334')
    draw = ImageDraw.Draw(samples)
    for row,p in enumerate(sorted(ROOT.glob('*.ttf'))):
        draw.text((12,row*100+4),p.name,fill='white')
        for col,size in enumerate([16,18,20,22]):
            font=ImageFont.truetype(str(p),size)
            draw.text((12+col*235,row*100+35),'대한민국 일본 선수 정보',font=font,fill='white')
            draw.text((12+col*235,row*100+65),'이치로 다르빗슈 류현진',font=font,fill='white')
    samples.save(WORK/'font_comparison.png')

def strings():
    data=(WORK/'SLPM_551.58').read_bytes()
    # NUL-terminated runs, strictly valid Shift-JIS with Japanese characters.
    pattern = re.compile(rb'(?:[\x09\x0a\x0d\x20-\x7e\xa1-\xdf]|[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){2,}\x00')
    rows=[]
    for m in pattern.finditer(data):
        raw=m.group()[:-1]
        try: s=raw.decode('cp932')
        except UnicodeDecodeError: continue
        if not re.search('[\u3040-\u30ff\u4e00-\u9fff]',s): continue
        if len(s)<2: continue
        rows.append(dict(offset=m.start(),bytes=len(raw),ja=s,ko=''))
    (WORK/'elf_strings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ELF candidate strings',len(rows),'unique',len(set(r['ja'] for r in rows)))

if __name__=='__main__':
    font_preview()
    strings()
