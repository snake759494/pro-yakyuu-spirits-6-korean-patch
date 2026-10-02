from npb_names import get,player,CACHE
from inventory import ROOT
from urllib.parse import urlencode,urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json,re

ps=json.loads((ROOT/'translation/players.json').read_text(encoding='utf-8'))
todo=[p for p in ps if not p['ko'] and len(p['ja'])>=2 and all(re.search('[\u4e00-\u9fff]',s) for s in p['ja'][:2])]
def fetch(p):
    keyword=' '.join(p['ja'][:2])
    url='https://npb.jp/bis/players/search/result?'+urlencode({'search_keyword':keyword})
    soup=BeautifulSoup(get(url),'html.parser')
    links=soup.select('a.player_unit_1[href]')
    if len(links)!=1:return None
    a=links[0];row=player((a.get_text(strip=True),urljoin(url,a['href'])))
    row.update(index=p['index'],searched_name=keyword,search_url=url)
    return row
with ThreadPoolExecutor(max_workers=4) as pool:
    out=[r for r in pool.map(fetch,todo) if r]
existing=json.loads((CACHE/'readings.json').read_text(encoding='utf-8'))
known={r['index'] for r in existing}
existing.extend(r for r in out if r['index'] not in known)
(CACHE/'readings.json').write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding='utf-8')
(CACHE/'alias_readings.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Additional official search identities',len(out))
