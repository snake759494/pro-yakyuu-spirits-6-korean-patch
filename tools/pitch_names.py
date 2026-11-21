"""Original (signature) pitch names stored inside PLAYERDATA.CHK player records.

Each name sits in a fixed field: b'+\\0' + b'\\x03' + <type byte> + name + zero
padding.  Only the name bytes and their existing zero padding are rewritten;
the type byte and everything after the padding stay untouched.
"""
import re
from kfont import encode

MAP={
 'フェイク':'페이크',
 '高速スライダー':'고속 슬라이더',
 'カツオカーブ':'가쓰오 커브',
 'スライダー':'슬라이더',
 'ストレート':'직구',
 'ゼロボール':'제로볼',
 'チェリーカーブ':'체리 커브',
 'ツーシームファスト':'투심 패스트',
 'イーファスピッチ':'이퓨스 피치',
}

def translations():return MAP

def spans(data):
    out=[]
    for ja,ko in MAP.items():
        for m in re.finditer(rb'\+\x00\x03.('+re.escape(ja.encode('cp932'))+rb')\x00',data,re.S):
            s=m.start(1);e=m.end(1)
            while e<len(data) and data[e]==0:e+=1
            out.append((s,e,ja,ko))
    return out

def apply(data,cm):
    out=bytearray(data);audit=[]
    for s,e,ja,ko in spans(data):
        raw=encode(ko,cm)+b'\0';assert len(raw)<=e-s,(ja,ko,hex(s),e-s)
        out[s:e]=raw.ljust(e-s,b'\0');audit.append(dict(file='PLAYERDATA.CHK',offset=s,ja=ja,ko=ko))
    return bytes(out),audit
