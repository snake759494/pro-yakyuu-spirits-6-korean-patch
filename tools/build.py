"""Reproducible localization build; runtime verification is recorded separately."""
from pathlib import Path
import json,struct,hashlib,shutil,re,collections,sys
from inventory import ROOT,WORK,ISO,iso_entries
from kfont import encode
from compact_labels import extra_glyphs
from scoped_names import translations as scoped_translations,apply as patch_scoped_names
from fixed_font import configure,patch_font
from analyze import chunks
from menu_textures import apply as patch_menu_textures
from wbc_names import apply as patch_wbc_names
from loading_tips import apply as patch_loading_tips, translations as loading_translations
from literal_refs import starts as referenced_starts
from banners import translations as banner_translations,apply as patch_banners
from txc_extra import translations as txc_translations
from scoped_labels import translations as short_translations,apply as patch_short_labels
from embedded_labels import translations as embedded_translations,apply as patch_embedded_labels

OUT=ROOT/'build'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def copy_n(src,dst,n):
    while n:
        b=src.read(min(n,8*1024*1024))
        if not b:raise EOFError('truncated source')
        dst.write(b);n-=len(b)
def patch_strings(data,translations,cm,label):
    out=bytearray(data);changes=[];skipped=[]
    protected={p for f,p,j,k in embedded_translations() if f==label}
    refs=referenced_starts(data,label)
    lower=struct.unpack_from('<I',data,12)[0] if label.endswith('.OVL') else 0x2b0000 if label=='SLPM_551.58' else 0
    for ja,ko in translations.items():
        src=ja.encode('cp932')+b'\0';dst=encode(ko,cm)+b'\0'
        cursor=lower
        while True:
            pos=data.find(src,cursor)
            if pos<0:break
            cursor=pos+len(src)
            if pos in protected or pos+1 in protected:continue
            if pos and data[pos-1]!=0 and pos not in refs:continue
            capacity=len(src)
            # C strings in these data blocks are word-aligned; only consume
            # verified zero padding through the next word boundary.
            aligned=(pos+len(src)+3)&~3
            if data[pos+len(src):aligned]==b'\0'*(aligned-pos-len(src)):
                capacity=aligned-pos
            # GEDATA message commands reserve exactly 256 bytes for text.
            # The next command begins at/after that boundary. Audit every
            # remaining byte, never consume the following command's fields.
            if label.startswith('GEDATA') and label.endswith('::DATA0') and re.search(r'<(?:NEXTPAGE|NEXTMESS|CLOSENEXT|CLOSE|SELECT[2-6])>$',ja):
                assert len(src)<=256 and pos+256<=len(data)
                assert data[pos+len(src):pos+256]==b'\0'*(256-len(src))
                capacity=256
            if len(dst)>capacity:
                skipped.append(dict(file=label,offset=pos,ja=ja,ko=ko,reason='slot_capacity'))
                continue
            if re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',ja)!=re.findall(r'%[-+ #0-9.*]*[a-zA-Z]',ko):raise ValueError('format mismatch')
            out[pos:pos+capacity]=dst.ljust(capacity,b'\0')
            changes.append(dict(file=label,offset=pos,ja=ja,ko=ko,bytes=len(src)))
    return bytes(out),changes,skipped

def main():
    OUT.mkdir(exist_ok=True)
    inv=json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    entries=iso_entries();fbd=next(x for x in entries if x['name']=='FBD/BASEBALL.FBD')
    elfentry=next(x for x in entries if x['name']=='SLPM_551.58')
    ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    ui={}
    if (ROOT/'translation/reference_ui.json').exists():
        ui.update(json.loads((ROOT/'translation/reference_ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/dialogs.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/wbc_ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/front_ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/wbc_intros.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/extra_ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/headers.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/setup_help.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/screen_ui.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/settings_help.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/wbc_events.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/events.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/overlay_texts.json').read_text(encoding='utf-8')))
    ui.update(json.loads((ROOT/'translation/overlay_full.json').read_text(encoding='utf-8')))
    ui.update({k.replace('\r\n','\n'):v.replace('\r\n','\n') for k,v in list(ui.items())})
    originals={'SLPM_551.58':(WORK/'SLPM_551.58').read_bytes()}
    originals.update({p.name:p.read_bytes() for p in (WORK/'assets').glob('*.OVL')})
    chunk_sources={};asset_originals={}
    with ISO.open('rb') as src:
        for entry in inv['fbd']:
            if not entry['name'].endswith('.CHK'):continue
            src.seek(entry['offset']);data=src.read(entry['size'])
            is_intro=entry['name'].startswith('WBCINTRO')
            is_event=entry['name'].startswith('GEDATA')
            if not data.startswith(b'CHK ') or (b'TXCPACK ' not in data and not is_intro and not is_event):continue
            for name,off,b in chunks(data):
                if not b.startswith(b'TXCPACK ') and not (is_intro and name in ('INTR','NAME')) and not (is_event and name=='DATA0'):continue
                label=entry['name']+'::'+name
                originals[label]=b
                chunk_sources[label]=(entry['name'],off)
                asset_originals[entry['name']]=data
    source_slots={b for data in originals.values() for b in data.split(b'\0') if 2<=len(b)<=20000}
    for label,data in originals.items():
        for p in referenced_starts(data,label):
            source_slots.add(data[p:data.index(0,p)])
    usable={}
    for ja,ko in ui.items():
        try:encoded=ja.encode('cp932')
        except UnicodeEncodeError:continue
        if encoded in source_slots:usable[ja]=ko
    ui=usable
    loading = loading_translations()
    txc_ui=txc_translations()
    chars=sorted({c for s in list(ui.values())+list(txc_ui.values())+[r[2] for r in scoped_translations()]+list(banner_translations().values())+[s for p in ps if p['ko'] for s in p['ko']]+[s for row in loading for s in row] for c in s if '\uac00'<=c<='\ud7a3'})
    chars=sorted(set(chars)|extra_glyphs(ui.values())|extra_glyphs(txc_ui.values())|extra_glyphs(r[2] for r in scoped_translations()))
    chars=sorted(set(chars)|{c for f,p,j,k in short_translations() for c in k if '\uac00'<=c<='\ud7a3'})
    chars=sorted(set(chars)|{c for f,p,j,k in embedded_translations() for c in k if '\uac00'<=c<='\ud7a3'}|extra_glyphs(r[3] for r in embedded_translations()))
    elf,cm,before,after=configure((WORK/'SLPM_551.58').read_bytes(),chars)
    audit_prefix='preflight_' if '--check' in sys.argv else ''
    (OUT/(audit_prefix+'charmap.json')).write_text(json.dumps({c:b.hex() for c,b in cm.items()},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/(audit_prefix+'font_slot_audit.json')).write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
    replacement={};expanded={};changes=[];skipped=[]
    elf,delta,miss=patch_strings(elf,ui,cm,'SLPM_551.58');changes+=delta;skipped+=miss
    elf,banner_audit=patch_banners(elf,cm)
    elf,short_audit=patch_short_labels(elf,cm,'SLPM_551.58');changes+=short_audit
    elf,embedded_audit=patch_embedded_labels(elf,cm,'SLPM_551.58');changes+=embedded_audit
    (OUT/(audit_prefix+'banners.json')).write_text(json.dumps(banner_audit,ensure_ascii=False,indent=2),encoding='utf-8')
    for file in (WORK/'assets').glob('*.OVL'):
        b=file.read_bytes();patched,delta,miss=patch_strings(b,ui,cm,file.name)
        patched,short_audit=patch_short_labels(patched,cm,file.name);delta+=short_audit
        patched,embedded_audit=patch_embedded_labels(patched,cm,file.name);delta+=embedded_audit
        if delta:replacement[file.name]=patched
        changes+=delta;skipped+=miss
    for label,(name,off) in chunk_sources.items():
        translations={**ui,**txc_ui} if originals[label].startswith(b'TXCPACK ') else ui
        patched,delta,miss=patch_strings(originals[label],translations,cm,label)
        if delta:
            asset=bytearray(replacement.get(name,asset_originals[name]))
            asset[off:off+len(patched)]=patched
            replacement[name]=bytes(asset)
        changes+=delta;skipped+=miss
    pd=bytearray((WORK/'assets/PLAYERDATA.CHK').read_bytes())
    accepted=[]
    for p in ps:
        if not p['ko']:continue
        raw=b'\0'.join(encode(s,cm) for s in p['ko'])+b'\0'
        if len(raw)>p['name_capacity']:
            skipped.append(dict(file='PLAYERDATA.CHK',index=p['index'],ja=p['ja'],ko=p['ko'],reason='name_capacity'))
            continue
        off=p['name_offset'];pd[off:off+p['name_capacity']]=raw.ljust(p['name_capacity'],b'\0')
        accepted.append(p['index'])
    original_pd=(WORK/'assets/PLAYERDATA.CHK').read_bytes()
    # Names occupy only +98..139 of each 180-byte player record.
    for p in ps:
        o=p['record_offset']
        assert pd[o:o+98]==original_pd[o:o+98]
        assert pd[o+140:o+180]==original_pd[o+140:o+180]
    assert pd[231456:]==original_pd[231456:]
    replacement['PLAYERDATA.CHK']=bytes(pd)
    replacement['COM_SEL.OVL'],scoped_audit=patch_scoped_names(replacement.get('COM_SEL.OVL',originals['COM_SEL.OVL']),cm)
    changes+=scoped_audit
    replacement['COM_SEL.OVL']=patch_wbc_names(replacement.get('COM_SEL.OVL',originals['COM_SEL.OVL']),cm)
    replacement['GLOADM.CHK']=patch_loading_tips((WORK/'assets/GLOADM.CHK').read_bytes(),cm)
    patch_menu_textures(replacement)
    from mode_textures import apply as patch_mode_textures
    mode_atlases=patch_mode_textures(replacement)
    for name in ['BBFONT.CHK','MENU2D.CHK','BBFONTG.CHK','KFONT.CHK']:
        patched,count=patch_font(replacement.get(name,(WORK/'assets'/name).read_bytes()),chars,before,after)
        assert count==1
        replacement[name]=patched
    if '--check' in sys.argv:
        summary=dict(hangul_glyphs=len(chars),players_translated=len(accepted),strings_applied=len(changes),skipped=skipped,
                     replaced_files=list(replacement),strings=changes)
        (OUT/'preflight.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        if '--verify-existing' in sys.argv:
            assert not skipped
            target=ISO.parent/'Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
            assert target.stat().st_size==ISO.stat().st_size and not expanded
            checked=[]
            with ISO.open('rb') as src,target.open('rb') as dst:
                dst.seek(elfentry['offset']);assert dst.read(len(elf))==elf,'ELF source mismatch'
                for e in inv['fbd']:
                    expected=replacement.get(e['name'])
                    if expected is None:
                        src.seek(e['offset']);expected=src.read(e['size'])
                    dst.seek(e['offset'])
                    assert dst.read(e['size'])==expected,e['name']
                    checked.append(e['name'])
            verification=dict(iso_sha256=digest(target),fbd_entries=len(checked),
                              rebuilt_modified_files=len(replacement),elf_matches=True,
                              all_fbd_match_current_sources=True,failures=[])
            (OUT/'source_reproduction_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
            print(json.dumps(verification,indent=2))
        print(json.dumps({k:v for k,v in summary.items() if k not in ('strings','replaced_files')},ensure_ascii=False,indent=2))
        return
    assert not skipped, 'Translation capacity failure; run --check and resolve all skipped strings before building.'
    # Append expanded fonts inside the FBD extent. Shift subsequent ISO extents.
    boundary=fbd['offset']+fbd['size'];assert boundary%2048==0
    additions=bytearray();new_offsets={}
    for name,b in expanded.items():
        new_offsets[name]=fbd['size']+len(additions)
        additions+=b+b'\0'*((-len(b))%2048)
    shift=len(additions);target=ISO.parent/'Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
    with ISO.open('rb') as src,target.open('wb') as dst:
        copy_n(src,dst,boundary);dst.write(additions);shutil.copyfileobj(src,dst,8*1024*1024)
    with target.open('r+b') as f:
        f.seek(elfentry['offset']);f.write(elf)
        for e in inv['fbd']:
            if e['name'] in replacement:
                b=replacement[e['name']];assert len(b)==e['size']
                f.seek(e['offset']);f.write(b)
            if e['name'] in expanded:
                b=expanded[e['name']];off=new_offsets[e['name']]
                f.seek(fbd['offset']+16+268*e['index']+256)
                f.write(struct.pack('<3I',off//2048,len(b),(len(b)+2047)//2048*2048))
        for e in entries:
            pos=e['offset']+(shift if e['offset']>=boundary else 0)
            size=e['size']+(shift if e['name']==fbd['name'] else 0)
            f.seek(e['record_offset']+2);f.write(struct.pack('<I',pos//2048)+struct.pack('>I',pos//2048))
            f.seek(e['record_offset']+10);f.write(struct.pack('<I',size)+struct.pack('>I',size))
        # Update every ISO9660 volume descriptor that contains a volume-space size.
        for sector in range(16,32):
            f.seek(sector*2048);vd=f.read(2048)
            if vd[1:6]!=b'CD001':break
            if vd[0] in (1,2):
                count=struct.unpack_from('<I',vd,80)[0]+shift//2048
                f.seek(sector*2048+80);f.write(struct.pack('<I',count)+struct.pack('>I',count))
            if vd[0]==255:break
    # Byte-level verification of all ISO files, including shifted audio/video.
    validations=[]
    with ISO.open('rb') as src,target.open('rb') as dst:
        for e in entries:
            newoff=e['offset']+(shift if e['offset']>=boundary else 0)
            if e['name']==fbd['name']:continue
            src.seek(e['offset']);dst.seek(newoff)
            if e['name']==elfentry['name']:
                assert dst.read(len(elf))==elf
            else:
                remain=e['size']
                while remain:
                    n=min(remain,8*1024*1024);assert src.read(n)==dst.read(n),e['name'];remain-=n
            validations.append(e['name'])
        for e in inv['fbd']:
            src.seek(e['offset'])
            newoff=fbd['offset']+new_offsets[e['name']] if e['name'] in expanded else e['offset']
            dst.seek(newoff)
            expected=expanded.get(e['name'],replacement.get(e['name']))
            if expected is None:expected=src.read(e['size'])
            assert dst.read(len(expected))==expected,e['name']
    report=dict(status='BUILT_PENDING_RUNTIME_VERIFICATION',font='NanumSquareNeo-cBd.ttf',hangul_glyphs=len(chars),
                players_total=len(ps),players_translated=len(accepted),player_indices=accepted,wbc_display_names_translated=448,
                strings_applied=len(changes),loading_tips_translated=len(loading),additional_mode_atlases=mode_atlases,txc_additional_unique_labels=len(txc_ui),strings=changes,skipped=skipped,
                all_unassigned_glyphs_preserved=True,font_strategy='fixed_size_audited_unused_slots',font_slots_reclaimed=len(chars),
                verified_fbd_entries=len(inv['fbd']),verified_iso_files=validations,
                source_sha256=digest(ISO),output_sha256=digest(target),source_size=ISO.stat().st_size,output_size=target.stat().st_size,
                iso_growth=shift,runtime_verified=False,untranslated_players=len(ps)-len(accepted))
    (OUT/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    reproduction=dict(iso_sha256=report['output_sha256'],fbd_entries=len(inv['fbd']),
                      rebuilt_modified_files=len(replacement),elf_matches=True,
                      all_fbd_match_current_sources=True,verification_mode='build-time readback',failures=[])
    (OUT/'source_reproduction_verification.json').write_text(json.dumps(reproduction,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['strings','skipped','player_indices','verified_iso_files']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
