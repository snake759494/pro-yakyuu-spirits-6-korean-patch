from inventory import ROOT,WORK,ISO
from analyze import chunks
import json,struct,re,collections

def main():
    inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    fonts=[]
    resources=[]
    text=[]
    pattern=re.compile(rb'(?:[\x09\x0a\x0d\x20-\x7e]|[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]){2,}\x00')
    with ISO.open('rb') as f:
        for e in inv['fbd']:
            f.seek(e['offset']);b=f.read(e['size'])
            if b'PS2 FONT' in b:
                fonts.append(dict(name=e['name'],offsets=[m.start() for m in re.finditer(b'PS2 FONT',b)]))
            if e['name'].endswith('.OVL'):
                (WORK/'assets'/e['name']).write_bytes(b)
                resources.append(e['name'])
                for m in pattern.finditer(b):
                    if m.start()>0 and b[m.start()-1]!=0:continue
                    try:s=m.group()[:-1].decode('cp932')
                    except UnicodeDecodeError:continue
                    if not re.search('[\u3040-\u30ff]',s):continue
                    if len(s)<3:continue
                    text.append(dict(file=e['name'],offset=m.start(),ja=s,ko=''))
    (WORK/'font_resources.json').write_text(json.dumps(fonts,indent=2),encoding='utf-8')
    (WORK/'overlay_strings.json').write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf-8')
    print('font resources',fonts)
    print('overlay files',len(resources),'candidate strings',len(text))

if __name__=='__main__':main()
