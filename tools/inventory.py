"""Read-only ISO/BNDR inventory and extraction of selected development assets."""
from pathlib import Path
import json, struct, hashlib

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / 'Pro Yakyuu Spirits 6 (Japan).iso'
WORK = ROOT / 'work'

def iso_entries():
    with ISO.open('rb') as f:
        def read(off, n):
            f.seek(off)
            return f.read(n)
        pvd = read(16 * 2048, 2048)
        assert pvd[1:6] == b'CD001'
        result = []
        def walk(lba, size, prefix=''):
            b = read(lba * 2048, size)
            i = 0
            while i < len(b):
                n = b[i]
                if not n:
                    i = (i // 2048 + 1) * 2048
                    continue
                assert n >= 34 and i + n <= len(b)
                name = b[i+33:i+33+b[i+32]]
                sector, length = struct.unpack_from('<I', b, i+2)[0], struct.unpack_from('<I', b, i+10)[0]
                if name not in (b'\0', b'\1'):
                    path = prefix + name.decode('ascii').split(';')[0]
                    if b[i+25] & 2:
                        walk(sector, length, path + '/')
                    else:
                        result.append(dict(name=path, offset=sector*2048, size=length,record_offset=lba*2048+i))
                i += n
        walk(struct.unpack_from('<I', pvd,158)[0],struct.unpack_from('<I',pvd,166)[0])
        return result

def main():
    WORK.mkdir(exist_ok=True)
    files = iso_entries()
    fbd = next(e for e in files if e['name']=='FBD/BASEBALL.FBD')
    assets = WORK / 'assets'
    assets.mkdir(exist_ok=True)
    with ISO.open('rb') as f:
        f.seek(fbd['offset'])
        h = f.read(16)
        assert h[:4] == b'BNDR'
        sector, start, count = struct.unpack_from('<3I',h,4)
        assert sector == 2048
        table = f.read(count*268)
        entries = []
        for i in range(count):
            name = table[i*268:i*268+256].split(b'\0')[0].decode('ascii')
            lba, size, capacity = struct.unpack_from('<3I',table,i*268+256)
            assert lba >= start and size <= capacity and lba*sector+capacity <= fbd['size']
            e = dict(index=i,name=name,offset=fbd['offset']+lba*sector,size=size,capacity=capacity)
            entries.append(e)
            if any(s in name.upper() for s in ('FONT','MAINMENU','PLAYER','TEXT','MENU2D')):
                f.seek(e['offset'])
                (assets/name).write_bytes(f.read(size))
    (WORK/'inventory.json').write_text(json.dumps(dict(iso=files,fbd=entries),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(files)} ISO files; {len(entries)} validated BNDR entries')
    print([(e['name'],e['size']) for e in entries if (assets/e['name']).exists()])

if __name__ == '__main__':
    main()
