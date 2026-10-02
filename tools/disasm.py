from pathlib import Path
import sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'실황파워풀메이저리그2009/tools'))
from mips import dis
from inventory import WORK
d=(WORK/'SLPM_551.58').read_bytes()
start,end=[int(s,16) for s in sys.argv[1:3]]
lines=[f'{p:08x} {dis(struct.unpack_from("<I",d,p)[0],p+0xff800)}' for p in range(start,end,4)]
(WORK/'disasm.txt').write_text('\n'.join(lines))
if len(sys.argv)>3:
    print('\n'.join(s for s in lines if any(x in s for x in sys.argv[3:])))
else:
    print('\n'.join(lines))
