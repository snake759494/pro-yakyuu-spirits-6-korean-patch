"""GEDATA's message renderer uses full-width cells (22 columns, 3 rows).

Keep ASCII command syntax intact; display text uses the original game's
full-width alphabet and spaces. ASCII word wrapping can otherwise discard
the tail before an explicit BR. Layout is checked separately from byte slots.
"""
import re

def normalize(s):
    return ''.join(t if t.startswith('<') else ''.join('\u3000' if c==' ' else chr(ord(c)+0xfee0) if '!'<=c<='~' else c for c in t) for t in re.split(r'(<[^>]+>)',s))

def line_widths(s):
    s=re.sub(r'<STR10>','가'*10,s);s=re.sub(r'<STR5>','가'*5,s)
    s=re.sub(r'<(?!BR>)[^>]+>','',s)
    return [len(line) for line in s.split('<BR>') if line]
