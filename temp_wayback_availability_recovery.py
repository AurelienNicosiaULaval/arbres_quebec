#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf, csv, hashlib, io, json, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.parse import quote
import requests
from pypdf import PdfReader

OUT=Path('notes_master_math_france_wayback_availability');OUT.mkdir(parents=True,exist_ok=True)
IPS=['207.241.237.3','207.241.237.7','207.241.237.10','207.241.237.14','207.241.237.15']; HOST='web.archive.org'; UA='Mozilla/5.0 Chrome/126 Safari/537.36'
RECORDS=[
{'num':1,'title':'Cours de probabilités','path':'01 - Proba-stat/01.1 Probabilites M1/01 - Cours de probabilites - Yves Coudene (2015).pdf','urls':['https://perso.lpsm.paris/~coudene/probabilites.pdf','http://perso.lpsm.paris/~coudene/probabilites.pdf','https://www.lpsm.paris/pageperso/coudene/probabilites.pdf','http://www.proba.jussieu.fr/pageperso/coudene/probabilites.pdf']},
{'num':19,'title':'Modélisation et statistique bayésienne computationnelle','path':'01 - Proba-stat/01.5 Bayesien et MCMC/19 - Modelisation et statistique bayesienne computationnelle - Nicolas Bousquet (2026).pdf','urls':['https://perso.lpsm.paris/~bousquet/poly-complet-2026-V1.pdf','http://perso.lpsm.paris/~bousquet/poly-complet-2026-V1.pdf','https://www.lpsm.paris/pageperso/bousquet/poly-complet-2026-V1.pdf']},
{'num':33,'title':'Contrôle optimal : théorie et applications','path':'02 - Analyse, optimisation et outils/Optimisation et controle/33 - Controle optimal theorie et applications - Emmanuel Trelat.pdf','urls':['https://www.ljll.fr/trelat/enseignement/controlSU/livreopt2.pdf','https://www.ljll.math.upmc.fr/trelat/fichiers/livreopt2.pdf','http://www.ljll.math.upmc.fr/trelat/fichiers/livreopt2.pdf','https://www.ljll.fr/trelat/fichiers/livreopt.pdf','https://www.ljll.fr/~trelat/fichiers/livreopt.pdf']},
{'num':34,'title':'Méthodes mathématiques et numériques pour les plasmas','path':'03 - EDP et calcul scientifique/34 - Methodes mathematiques et numeriques pour les plasmas - Bruno Despres (2021).pdf','urls':['https://www.ljll.fr/despres/BD_fichiers/m2_plasma.pdf','http://www.ljll.fr/despres/BD_fichiers/m2_plasma.pdf','https://www.ljll.math.upmc.fr/despres/BD_fichiers/m2_plasma.pdf','http://www.ljll.math.upmc.fr/despres/BD_fichiers/m2_plasma.pdf']},
{'num':35,'title':'Équations aux dérivées partielles elliptiques','path':'03 - EDP et calcul scientifique/35 - Equations aux derivees partielles elliptiques - Herve Le Dret (2010).pdf','urls':['https://www.ljll.fr/ledret/M2Elliptique/chapitre4.pdf','http://www.ljll.fr/ledret/M2Elliptique/chapitre4.pdf','https://www.ljll.math.upmc.fr/ledret/M2Elliptique/chapitre4.pdf','http://www.ljll.math.upmc.fr/ledret/M2Elliptique/chapitre4.pdf']},
]

def validate(data):
 p=data.find(b'%PDF-')
 if p<0 or p>4096: raise ValueError(f'non PDF {data[:40]!r}')
 data=data[p:]; n=len(PdfReader(io.BytesIO(data),strict=False).pages)
 if n<1: raise ValueError('aucune page')
 return data,n

def available(url):
 endpoint='https://archive.org/wayback/available?url='+quote(url,safe='')+'&timestamp=20260716'
 for attempt in range(5):
  try:
   r=requests.get(endpoint,headers={'User-Agent':UA},timeout=(10,40));r.raise_for_status();j=r.json();c=j.get('archived_snapshots',{}).get('closest',{})
   if c.get('available') and c.get('url'):return c
  except Exception:pass
  time.sleep(2+attempt)
 return None

def fetch_snapshot(url):
 if url.startswith('http://'):url='https://'+url[7:]
 if '/web/' in url and 'id_/' not in url:
  left,right=url.split('/web/',1);ts,orig=right.split('/',1);ts=ts.replace('id_','');url=left+'/web/'+ts+'id_/'+orig
 errors=[]
 for round_no in range(4):
  for ip in IPS:
   with tempfile.NamedTemporaryFile(delete=False) as f:tmp=Path(f.name)
   cmd=['curl','-k','-L','--fail','--connect-timeout','12','--max-time','180','--resolve',f'{HOST}:443:{ip}','-A',UA,'-o',str(tmp),url]
   try:
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0 and tmp.stat().st_size:
     data,n=validate(tmp.read_bytes());return data,n,url
    errors.append(f'{ip}:{(p.stderr or p.stdout)[-400:]}')
   except Exception as e:errors.append(f'{ip}:{type(e).__name__}:{e}')
   finally:tmp.unlink(missing_ok=True)
  time.sleep(3+round_no*2)
 raise RuntimeError(' | '.join(errors)[-5000:])

def recover(rec):
 errors=[]
 with cf.ThreadPoolExecutor(max_workers=len(rec['urls'])) as ex:
  fs={ex.submit(available,u):u for u in rec['urls']}
  candidates=[]
  for f in cf.as_completed(fs):
   try:
    c=f.result()
    if c:candidates.append((fs[f],c))
   except Exception as e:errors.append(f'availability {fs[f]}:{e}')
 candidates.sort(key=lambda z:z[1].get('timestamp',''),reverse=True)
 for orig,c in candidates:
  try:
   data,n,snap=fetch_snapshot(c['url']);d=OUT/rec['path'];d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
   return {**rec,'status':'ok','source_url':snap,'original_variant':orig,'timestamp':c.get('timestamp',''),'pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'candidates':len(candidates),'detail':''}
  except Exception as e:errors.append(f'snapshot {c.get("url")}:{type(e).__name__}:{e}')
 return {**rec,'status':'error','source_url':'','original_variant':'','timestamp':'','pages':0,'bytes':0,'sha256':'','candidates':len(candidates),'detail':' | '.join(errors)[-18000:]}

results=[]
with cf.ThreadPoolExecutor(max_workers=5) as ex:
 fs={ex.submit(recover,r):r for r in RECORDS}
 for f in cf.as_completed(fs):
  try:x=f.result()
  except BaseException:
   import traceback;r=fs[f];x={**r,'status':'error','source_url':'','original_variant':'','timestamp':'','pages':0,'bytes':0,'sha256':'','candidates':0,'detail':'UNHANDLED '+traceback.format_exc()}
  results.append(x);print(f"[{x['num']:02d}] {x['status']} candidates={x['candidates']} pages={x['pages']} bytes={x['bytes']} {x['title']}",flush=True)
results.sort(key=lambda x:x['num']);fields=['num','title','path','urls','status','source_url','original_variant','timestamp','pages','bytes','sha256','candidates','detail'];rows=[]
for x in results:
 y=dict(x);y['urls']=' | '.join(y['urls']);rows.append(y)
with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
(OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
err=[x for x in results if x['status']!='ok'];print(f'SUCCES={len(results)-len(err)} ECHECS={len(err)}');sys.exit(1 if err else 0)
