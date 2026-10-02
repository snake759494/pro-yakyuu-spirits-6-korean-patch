"""Find explicitly referenced executable string starts, including after floats.

OVLs use the file-relative base in header word 2. The ELF load segment starts
at file 0x800 / virtual 0x100000. Only references into the data area qualify.
"""
import struct

def starts(data,label):
    if label.endswith('.OVL'):
        base=struct.unpack_from('<I',data,8)[0]
        lower=struct.unpack_from('<I',data,12)[0];code=0x40
    elif label=='SLPM_551.58':base=0xff800;lower=0x2b0000;code=0x800
    else:return set()
    result=set()
    def accept(value):
        p=value-base
        if lower<=p<len(data) and data.find(b'\0',p,min(len(data),p+20001))>=0:result.add(p)
    for p in range(lower+(4-lower%4)%4,len(data)-3,4):
        accept(struct.unpack_from('<I',data,p)[0])
    for p in range(code,lower-3,4):
        word=struct.unpack_from('<I',data,p)[0]
        if word>>26!=15:continue # LUI
        register=(word>>16)&31;hi=(word&65535)<<16
        if not register:continue
        for q in range(p+4,min(p+36,lower-3),4):
            w=struct.unpack_from('<I',data,q)[0];op=w>>26
            rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;imm=w&65535
            if rs==register and op in (9,13):
                accept(hi+(imm-(65536 if imm&32768 else 0)) if op==9 else hi|imm)
            # Stop once the original high-half register is overwritten.
            if (op==0 and rd==register) or (op in (8,9,10,11,12,13,14,15,32,33,35,36,37) and rt==register):break
            if op in (2,3):break
    return result
