import struct,sys
from inventory import WORK
d=(WORK/'SLPM_551.58').read_bytes()
addr=int(sys.argv[1],16)
for p in range(0x800,0x2b0000,4):
    w=struct.unpack_from('<I',d,p)[0]
    if w>>26!=15:continue
    rt=(w>>16)&31;hi=(w&65535)<<16
    for q in range(p+4,min(p+128,len(d)),4):
        v=struct.unpack_from('<I',d,q)[0]
        rs=(v>>21)&31;op=v>>26;imm=v&65535
        if rs==rt and op in (9,13,35,43):
            val=hi+(imm-(65536 if imm&32768 else 0)) if op!=13 else hi|imm
            if val==addr:print(hex(p),hex(q))
