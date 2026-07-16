#!/usr/bin/env python3
from __future__ import annotations
import ast, concurrent.futures as cf, csv, hashlib, io, json, sys
from pathlib import Path
from urllib.parse import quote_plus
import requests
from pypdf import PdfReader
from warcio.archiveiterator import ArchiveIterator
import urllib3
urllib3.disable_warnings()

OUT=Path('notes_master_math_france_missing_cc_fast'); OUT.mkdir(parents=True,exist_ok=True)
HEAD={'User-Agent':'Academic-PDF-Recovery/1.0','Accept':'application/json,application/pdf,*/*'}

tree=ast.parse(Path('temp_download_missing_commoncrawl.py').read_text(encoding='utf-8'))
RECORDS=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RECORDS' for t in node.targets):
        RECORDS=ast.literal_eval(node.value); break
if RECORDS is None: raise RuntimeError('RECORDS introuvable')

cols=requests.get('https://index.commoncrawl.org/collinfo.json',headers=HEAD,timeout=30).json()
selected=cols[:28] + cols[28:70:2] + cols[70:120:4]
seen=set(); INDEXES=[]
for c in selected:
    if c['id'] not in seen:
        seen.add(c['id']); INDEXES.append((c['id'],c['cdx-api']))
print('INDEXES',len(INDEXES),flush=True)

def pages(data:bytes):
    pos=data.find(b'%PDF-')
    if pos<0 or pos>4096: raise ValueError(f'pas de signature PDF, magic={data[:20]!r}')
    data=data[pos:]
    n=len(PdfReader(io.BytesIO(data),strict=False).pages)
    if n<1: raise ValueError('aucune page')
    return data,n

def query(pair):
    idx,api,url=pair
    endpoint=f'{api}?url={quote_plus(url)}&output=json&filter=status:200&collapse=digest'
    try:
        r=requests.get(endpoint,headers=HEAD,timeout=(5,18))
        if r.status_code!=200: return []
        hits=[]
        for line in r.text.splitlines():
            try:
                h=json.loads(line)
                if h.get('filename') and h.get('offset') and h.get('length'): hits.append((idx,url,h))
            except Exception: pass
        return hits
    except Exception:
        return []

def fetch_hit(item):
    idx,orig,h=item
    start=int(h['offset']); length=int(h['length'])
    u='https://data.commoncrawl.org/'+h['filename']
    r=requests.get(u,headers={**HEAD,'Range':f'bytes={start}-{start+length-1}'},timeout=(10,90))
    if r.status_code not in (200,206): raise RuntimeError(f'WARC HTTP {r.status_code}')
    for rec in ArchiveIterator(io.BytesIO(r.content)):
        if rec.rec_type in ('response','resource'):
            data=rec.content_stream().read(); data,n=pages(data)
            return data,n,f"commoncrawl:{idx}:{h.get('timestamp','')}:{h.get('url',orig)}"
    raise ValueError('aucune réponse WARC PDF')

def direct(rec):
    for u in rec['urls']:
        try:
            r=requests.get(u,headers=HEAD,timeout=(6,25),verify=False); r.raise_for_status()
            data,n=pages(r.content); return data,n,r.url,'direct'
        except Exception: pass
    return None

def recover(rec):
    d=direct(rec)
    if d:
        data,n,src,kind=d; return {**rec,'status':'ok','data':data,'pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source_url':src,'source_kind':kind,'detail':''}
    pairs=[(idx,api,u) for u in rec['urls'] for idx,api in INDEXES]
    hits=[]
    with cf.ThreadPoolExecutor(max_workers=36) as ex:
        for batch in ex.map(query,pairs): hits.extend(batch)
    hits=sorted(hits,key=lambda z:z[2].get('timestamp',''),reverse=True)
    errors=[]
    for hit in hits[:30]:
        try:
            data,n,src=fetch_hit(hit)
            return {**rec,'status':'ok','data':data,'pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source_url':src,'source_kind':'commoncrawl','detail':f'{len(hits)} captures trouvées'}
        except Exception as e: errors.append(f'{hit[0]}:{type(e).__name__}:{e}')
    return {**rec,'status':'error','data':b'','pages':0,'bytes':0,'sha256':'','source_url':'','source_kind':'','detail':f'{len(hits)} captures. '+ ' | '.join(errors)[-10000:]}

results=[]
with cf.ThreadPoolExecutor(max_workers=5) as ex:
    fs={ex.submit(recover,r):r for r in RECORDS}
    for f in cf.as_completed(fs):
        rec=fs[f]
        try: x=f.result()
        except BaseException as e:
            import traceback
            x={**rec,'status':'error','data':b'','pages':0,'bytes':0,'sha256':'','source_url':'','source_kind':'','detail':'UNHANDLED '+traceback.format_exc()}
        if x['status']=='ok':
            dest=OUT/x['path']; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(x.pop('data'))
        else: x.pop('data',None)
        results.append(x); print(f"[{x['num']:02d}] {x['status']} pages={x['pages']} bytes={x['bytes']} {x['title']} {x['detail'][-250:]}",flush=True)
results.sort(key=lambda r:r['num'])
fields=['num','title','path','urls','status','source_url','source_kind','pages','bytes','sha256','detail']
rows=[]
for r in results:
    q=dict(r); q['urls']=' | '.join(q['urls']); rows.append(q)
with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
(OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
err=[r for r in results if r['status']!='ok']; print(f'SUCCES={len(results)-len(err)} ECHECS={len(err)}',flush=True)
sys.exit(1 if err else 0)
