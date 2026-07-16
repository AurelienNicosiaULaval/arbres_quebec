#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf, csv, hashlib, io, json, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.parse import quote
from pypdf import PdfReader

OUT=Path('notes_master_math_france_wayback_alt');OUT.mkdir(parents=True,exist_ok=True)
HOST='web.archive.org'; IPS=['207.241.237.3','207.241.237.7','207.241.237.10','207.241.237.14','207.241.237.15']; UA='Mozilla/5.0 Chrome/126 Safari/537.36'
RECORDS=[
{'num':1,'title':'Cours de probabilités','path':'01 - Proba-stat/01.1 Probabilites M1/01 - Cours de probabilites - Yves Coudene (2015).pdf','queries':['perso.lpsm.paris/*coudene*probabilites.pdf','www.lpsm.paris/*coudene*probabilites.pdf','www.proba.jussieu.fr/*coudene*probabilites.pdf','www.proba.jussieu.fr/*coudene*.pdf']},
{'num':19,'title':'Modélisation et statistique bayésienne computationnelle','path':'01 - Proba-stat/01.5 Bayesien et MCMC/19 - Modelisation et statistique bayesienne computationnelle - Nicolas Bousquet (2026).pdf','queries':['perso.lpsm.paris/*bousquet*poly-complet-2026*.pdf','www.lpsm.paris/*bousquet*poly-complet-2026*.pdf','perso.lpsm.paris/*bousquet*.pdf']},
{'num':33,'title':'Contrôle optimal : théorie et applications','path':'02 - Analyse, optimisation et outils/Optimisation et controle/33 - Controle optimal theorie et applications - Emmanuel Trelat.pdf','queries':['www.ljll.fr/*trelat*livreopt2.pdf','www.ljll.math.upmc.fr/*trelat*livreopt2.pdf','www.ljll.fr/*trelat*livreopt.pdf','www.ljll.math.upmc.fr/*trelat*livreopt.pdf']},
{'num':34,'title':'Méthodes mathématiques et numériques pour les plasmas','path':'03 - EDP et calcul scientifique/34 - Methodes mathematiques et numeriques pour les plasmas - Bruno Despres (2021).pdf','queries':['www.ljll.fr/*despres*m2_plasma.pdf','www.ljll.math.upmc.fr/*despres*m2_plasma.pdf','www.ljll.fr/*m2_plasma.pdf']},
{'num':35,'title':'Équations aux dérivées partielles elliptiques','path':'03 - EDP et calcul scientifique/35 - Equations aux derivees partielles elliptiques - Herve Le Dret (2010).pdf','queries':['www.ljll.fr/*ledret*M2Elliptique*chapitre4.pdf','www.ljll.math.upmc.fr/*ledret*M2Elliptique*chapitre4.pdf','www.ljll.fr/*M2Elliptique*chapitre4.pdf']},
]

def validate(data):
 p=data.find(b'%PDF-')
 if p<0 or p>4096: raise ValueError(f'non PDF {data[:30]!r}')
 data=data[p:];n=len(PdfReader(io.BytesIO(data),strict=False).pages)
 if n<1: raise ValueError('aucune page')
 return data,n

def curl(url,timeout=120):
 errors=[]
 for round_no in range(3):
  for ip in IPS:
   with tempfile.NamedTemporaryFile(delete=False) as f: tmp=Path(f.name)
   cmd=['curl','-k','-L','--fail','--connect-timeout','10','--max-time',str(timeout),'--resolve',f'{HOST}:443:{ip}','-A',UA,'-o',str(tmp),url]
   try:
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0 and tmp.stat().st_size: return tmp.read_bytes()
    errors.append(f'{ip}:{(p.stderr or p.stdout)[-300:]}')
   finally: tmp.unlink(missing_ok=True)
  time.sleep(2+round_no*2)
 raise RuntimeError(' | '.join(errors)[-4000:])

def cdx(query):
 u=f'https://{HOST}/cdx/search/cdx?url={quote(query,safe="")}&output=json&filter=statuscode:200&fl=timestamp,original,mimetype,statuscode,digest&collapse=digest&limit=200&sort=reverse'
 raw=curl(u,90); data=json.loads(raw.decode('utf-8',errors='replace'))
 if not isinstance(data,list) or len(data)<2:return []
 hdr=data[0];return [dict(zip(hdr,r)) for r in data[1:] if len(r)==len(hdr)]

def recover(rec):
 errors=[];caps=[]
 with cf.ThreadPoolExecutor(max_workers=len(rec['queries'])) as ex:
  fs={ex.submit(cdx,q):q for q in rec['queries']}
  for f in cf.as_completed(fs):
   try:caps.extend(f.result())
   except Exception as e:errors.append(f'CDX {fs[f]}:{type(e).__name__}:{e}')
 uniq={}
 for c in caps:uniq[(c.get('timestamp'),c.get('original'))]=c
 caps=list(uniq.values());caps.sort(key=lambda c:('pdf' in (c.get('mimetype') or '').lower(),c.get('timestamp','')),reverse=True)
 for c in caps[:100]:
  try:
   snap=f'https://{HOST}/web/{c["timestamp"]}id_/{c["original"]}'
   data,n=validate(curl(snap,180));d=OUT/rec['path'];d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
   return {**rec,'status':'ok','source_url':snap,'pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'captures':len(caps),'detail':''}
  except Exception as e:errors.append(f'{c.get("timestamp")} {c.get("original")}:{type(e).__name__}:{e}')
 return {**rec,'status':'error','source_url':'','pages':0,'bytes':0,'sha256':'','captures':len(caps),'detail':' | '.join(errors)[-20000:]}

results=[]
with cf.ThreadPoolExecutor(max_workers=5) as ex:
 fs={ex.submit(recover,r):r for r in RECORDS}
 for f in cf.as_completed(fs):
  try:x=f.result()
  except BaseException:
   import traceback;r=fs[f];x={**r,'status':'error','source_url':'','pages':0,'bytes':0,'sha256':'','captures':0,'detail':'UNHANDLED '+traceback.format_exc()}
  results.append(x);print(f"[{x['num']:02d}] {x['status']} captures={x['captures']} pages={x['pages']} bytes={x['bytes']} {x['title']}",flush=True)
results.sort(key=lambda x:x['num']);fields=['num','title','path','queries','status','source_url','pages','bytes','sha256','captures','detail'];rows=[]
for x in results:
 y=dict(x);y['queries']=' | '.join(y['queries']);rows.append(y)
with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
(OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
err=[x for x in results if x['status']!='ok'];print(f'SUCCES={len(results)-len(err)} ECHECS={len(err)}');sys.exit(1 if err else 0)
