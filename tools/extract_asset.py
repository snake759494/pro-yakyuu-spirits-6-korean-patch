import sys,json
from inventory import ISO,WORK
inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
with ISO.open('rb') as f:
    for name in sys.argv[1:]:
        e=next(e for e in inv['fbd'] if e['name']==name)
        f.seek(e['offset']);(WORK/'assets'/name).write_bytes(f.read(e['size']))
        print(name,e['size'])
