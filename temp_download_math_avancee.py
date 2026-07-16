#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf, csv, hashlib, io, json, subprocess, tempfile
from pathlib import Path
import requests, urllib3
from pypdf import PdfReader
urllib3.disable_warnings()
OUT=Path('notes_math_avancees_france'); OUT.mkdir(parents=True,exist_ok=True)
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36','Accept':'application/pdf,application/octet-stream,*/*;q=0.8','Accept-Language':'fr-FR,fr;q=0.9,en;q=0.7'}
records=[]
for p in sorted(Path('.').glob('temp_math_catalog_*.json')): records.extend(json.loads(p.read_text(encoding='utf-8')))

def valid(data):
 p=data.find(b'%PDF-')
 if p<0 or p>4096: raise ValueError(f'absence signature PDF {data[:40]!r}')
 data=data[p:]; n=len(PdfReader(io.BytesIO(data),strict=False).pages)
 if n<1: raise ValueError('aucune page')
 return data,n

def req(url):
 r=requests.get(url,headers=H,timeout=(15,180),verify=False,allow_redirects=True);r.raise_for_status();return r.content,r.url,'requests'

def curl(url):
 with tempfile.NamedTemporaryFile(suffix='.pdf',delete=False) as f: q=Path(f.name)
 try:
  x=subprocess.run(['curl','-L','--fail','--retry','3','--retry-all-errors','--connect-timeout','15','--max-time','240','-A',H['User-Agent'],'-o',str(q),url],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  if x.returncode: raise RuntimeError((x.stderr or x.stdout)[-2000:])
  return q.read_bytes(),url,'curl'
 finally:q.unlink(missing_ok=True)

def one(r):
 e=[]
 for m in (req,curl):
  try:
   raw,u,t=m(r['url']); data,n=valid(raw); d=OUT/r['path'];d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
   return {**r,'status':'ok','final_url':u,'transport':t,'pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'detail':''}
  except Exception as z:e.append(f'{m.__name__}:{type(z).__name__}:{z}')
 return {**r,'status':'error','final_url':'','transport':'','pages':0,'bytes':0,'sha256':'','detail':' | '.join(e)[-12000:]}

res=[]
with cf.ThreadPoolExecutor(max_workers=8) as ex:
 fs={ex.submit(one,r):r for r in records}
 for f in cf.as_completed(fs):
  try:x=f.result()
  except BaseException:
   import traceback;r=fs[f];x={**r,'status':'error','final_url':'','transport':'','pages':0,'bytes':0,'sha256':'','detail':'UNHANDLED '+traceback.format_exc()}
  res.append(x);print(f"[{x['num']:02d}] {x['status']} pages={x['pages']} bytes={x['bytes']} {x['title']}",flush=True)
res.sort(key=lambda x:x['num'])
fields=['num','institution','level','domain','title','author','path','url','status','final_url','transport','pages','bytes','sha256','detail']
with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(res)
(OUT/'manifest.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
s={'total':len(res),'success':sum(x['status']=='ok' for x in res),'errors':sum(x['status']!='ok' for x in res)}
(OUT/'SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(s,ensure_ascii=False),flush=True)
