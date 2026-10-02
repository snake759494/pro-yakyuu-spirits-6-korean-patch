"""Length-prefixed loading tips. Preserve record sizes and routing fields."""
import json, re, struct
from inventory import ROOT, WORK
from analyze import chunks
from kfont import encode

def records(data):
    name, offset, payload = next(x for x in chunks(data) if x[0] == 'MES')
    cursor = 0
    result = []
    while cursor < len(payload) - 4:
        size = struct.unpack_from('<I', payload, cursor)[0]
        assert size >= 13 and size % 4 == 0 and cursor + size <= len(payload)
        pos = cursor + 10
        strings = []
        for _ in range(3):
            length = payload[pos]
            raw = payload[pos+1:pos+1+length]
            assert length and len(raw) == length and raw[-1] == 0
            strings.append(raw[:-1].decode('cp932'))
            pos += 1 + length
        assert not any(payload[pos:cursor+size])
        result.append((offset+cursor, size, strings))
        cursor += size
    assert payload[cursor:] == b'\0'*4
    return result

def translations():
    return json.loads((ROOT/'translation/loading_tips.json').read_text(encoding='utf-8'))

def apply(data, cm):
    rows = records(data)
    ko = translations()
    assert len(rows) == len(ko) == 90
    out = bytearray(data)
    for index, ((offset, size, source), target) in enumerate(zip(rows, ko)):
        assert len(target) == 3
        for ja, text in zip(source, target):
            tags = lambda s: [x for x in re.findall(r'<[^>]+>', s) if x != '<BR>']
            assert tags(ja) == tags(text), (index, 'control tags')
        encoded = [encode(s, cm)+b'\0' for s in target]
        assert all(len(s) <= 255 for s in encoded), index
        block = b''.join(bytes([len(s)])+s for s in encoded)
        assert len(block) <= size-10, (index, len(block), size-10)
        out[offset+10:offset+size] = block.ljust(size-10, b'\0')
        assert out[offset:offset+10] == data[offset:offset+10]
    assert len(out) == len(data)
    # Reparse the actual output: catch bad length bytes, shifted records and
    # leftover bytes instead of merely testing the translation source.
    parsed = records(bytes(out))
    for (offset, size, source), (new_offset, new_size, decoded), target in zip(rows, parsed, ko):
        assert (offset, size) == (new_offset, new_size)
        assert [s.encode('cp932') for s in decoded] == [encode(s, cm) for s in target]
    return bytes(out)
