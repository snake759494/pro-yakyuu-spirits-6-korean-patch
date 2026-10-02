"""Cache NPB public name readings for exact-name matches; four bounded workers."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import requests,json,re,time,unicodedata,collections
from bs4 import BeautifulSoup
from inventory import ROOT,WORK

CACHE=WORK/'npb';CACHE.mkdir(exist_ok=True)
BASE='https://npb.jp/bis/players/all/'
def get(url):
    name=re.sub('[^A-Za-z0-9._-]','_',url.removeprefix('https://npb.jp/'))
    dest=CACHE/name
    if dest.exists():return dest.read_text(encoding='utf-8')
    for attempt in range(3):
        try:
            r=requests.get(url,timeout=30);r.raise_for_status();r.encoding='utf-8'
            dest.write_text(r.text,encoding='utf-8');time.sleep(.15);return r.text
        except requests.RequestException:
            if attempt==2:raise
            time.sleep(1)
def norm(s):
    s=unicodedata.normalize('NFKC',s)
    return re.sub(r'[\s・.]','',s).translate(str.maketrans('髙﨑齋齊澤濱邊邉廣','高崎斎斉沢浜辺辺広'))
def index(url):
    soup=BeautifulSoup(get(url),'html.parser')
    return [(a.select_one('.name').get_text().strip(),urljoin(url,a['href'])) for a in soup.select('a[href]') if re.search(r'/?\d{8}\.html$',a['href']) and a.select_one('.name')]
def player(pair):
    name,url=pair
    soup=BeautifulSoup(get(url),'html.parser')
    n=soup.select_one('#pc_v_name');k=soup.select_one('#pc_v_kana')
    return dict(name=n.get_text().strip() if n else name,kana=k.get_text().strip() if k else None,url=url)
def main():
    soup=BeautifulSoup(get(urljoin(BASE,'index.html')),'html.parser')
    urls=sorted({urljoin(BASE,a['href']) for a in soup.select('a[href]') if re.fullmatch('index_[a-z]+.html',a['href'])})
    names=collections.defaultdict(set)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rows in pool.map(index,urls):
            for n,url in rows:names[norm(n)].add((n,url))
    ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
    matches=[];missing=[];todo=set()
    for p in ps:
        if p['ko']:continue
        ns=p['ja'];candidates=names.get(norm(''.join(ns[:2])),set())
        if not candidates and len(ns)>2:candidates=names.get(norm(ns[2]),set())
        if len(candidates)==1:
            pair=next(iter(candidates));todo.add(pair);matches.append((p['index'],pair))
        else:missing.append(dict(index=p['index'],ja=ns,candidates=list(candidates)))
    print('Exact NPB identities',len(matches),'remaining',len(missing),flush=True)
    readings={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,row in enumerate(pool.map(player,sorted(todo))):
            readings[row['url']]=row
            if i%50==0:print('Readings',i,'/',len(todo),flush=True)
    result=[dict(index=i,**readings[pair[1]]) for i,pair in matches]
    (CACHE/'readings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (CACHE/'unresolved.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved',len(result),'official readings',flush=True)

if __name__=='__main__':main()
