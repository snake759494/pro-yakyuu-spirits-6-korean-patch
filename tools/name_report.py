"""Searchable local audit of source spellings and reviewed Korean names."""
import json,collections,html
from inventory import ROOT

def main():
    ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    rows=[]
    for p in ps:
        kind='참고 프로젝트 일치' if p.get('reference') else 'NPB 공식 독음' if p.get('match')=='npb_official_kana' else '등록명·외국인 표기 검수'
        rows.append(dict(index=p['index'],ja=' / '.join(p['ja']),ko=' / '.join(p['ko'] or []),latin=p['latin'],kind=kind,
                         url=p.get('npb',{}).get('url',''),kana=p.get('npb',{}).get('kana',''),
                         reference='; '.join(r['source_file']+': '+str(r['ja'].get('src',r['ja']['id']))+' → '+r['ko']['fam']+' '+r['ko']['giv'] for r in p.get('reference',[]))))
    counts=collections.Counter(r['kind'] for r in rows)
    data=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>스피리츠6 선수 이름 대조표</title>
<style>@font-face{font-family:Neo;src:url('../NanumSquareNeo-cBd.ttf')}*{box-sizing:border-box}body{font-family:Neo,system-ui;margin:0;background:#f2f5f8;color:#1b2838}header{background:#14263d;color:white;padding:32px 5vw}h1{font-size:26px;margin:0 0 12px}p{line-height:1.7;margin:8px 0}.toolbar{position:sticky;top:0;background:#e9eef5;padding:18px 5vw;display:flex;gap:12px;align-items:center}input,select{padding:12px;border:1px solid #b7c5d5;border-radius:6px;font:inherit}input{width:40%;min-width:240px}main{padding:20px 5vw}table{width:100%;border-collapse:collapse;background:white}th,td{padding:12px;text-align:left;border-bottom:1px solid #dce3ec}th{background:#e3eaf3}td small{display:block;margin-top:5px;font:12px system-ui;color:#60728a}.ko{font-size:18px;color:#075c91}a{color:#075c91}.count{margin-left:auto}footer{padding:20px 5vw;color:#60728a}</style>
<header><h1>스피리츠6 선수 이름 대조표</h1><p>원본의 성·이름·등록명과 한글 표기를 나란히 확인할 수 있습니다. 선수 및 감독 1,276개 레코드를 포함합니다.</p><p>COUNTS</p><p>참고: 실황파워풀메이저리그2009의 번역 데이터, NPB 공식 개인 기록. 원본의 등록명과 2009년 당시 이름을 우선합니다.</p></header>
<div class="toolbar"><input id="query" placeholder="한글·일본어·영문 이름 검색" aria-label="이름 검색"><select id="kind" aria-label="검수 근거"><option>전체</option><option>참고 프로젝트 일치</option><option>NPB 공식 독음</option><option>등록명·외국인 표기 검수</option></select><span class="count" id="count"></span></div>
<main><table><thead><tr><th>번호</th><th>원문 / 영문</th><th>한글</th><th>검수 근거</th></tr></thead><tbody id="body"></tbody></table></main>
<footer>이 대조표는 번역 데이터 검수용입니다. 게임 화면별 표시 검증과 전체 한글화 완료 여부는 별도 빌드 보고서를 기준으로 합니다.</footer>
<script>const rows=DATA;const $=s=>document.querySelector(s);function cell(text,cls){const c=document.createElement('td');c.textContent=text;if(cls)c.className=cls;return c}function draw(){const q=$('#query').value.toLowerCase(),k=$('#kind').value;const found=rows.filter(r=>(k==='전체'||r.kind===k)&&[r.ja,r.ko,r.latin,r.kana,String(r.index)].join(' ').toLowerCase().includes(q));$('#body').replaceChildren();for(const r of found){const tr=document.createElement('tr');tr.append(cell(r.index));const original=cell(r.ja);const small=document.createElement('small');small.textContent=r.latin;original.append(small);tr.append(original,cell(r.ko,'ko'));const source=cell(r.kind);const detail=document.createElement('small');detail.textContent=r.reference||r.kana;source.append(detail);if(r.url){const a=document.createElement('a');a.href=r.url;a.textContent=' NPB 기록';a.target='_blank';a.rel='noopener';source.append(a)}tr.append(source);$('#body').append(tr)}$('#count').textContent=found.length+'명'}$('#query').addEventListener('input',draw);$('#kind').addEventListener('change',draw);draw()</script></html>'''
    page=page.replace('COUNTS',' · '.join(html.escape(k)+': '+str(v)+'명' for k,v in counts.items())).replace('DATA',data)
    (ROOT/'build/name_review.html').write_text(page,encoding='utf-8')
    (ROOT/'build/name_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(dict(counts))

if __name__=='__main__':main()
