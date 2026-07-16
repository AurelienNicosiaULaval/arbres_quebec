#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as cf
import csv, hashlib, io, json, sys, time
from pathlib import Path
from urllib.parse import quote_plus

import requests
from pypdf import PdfReader
from warcio.archiveiterator import ArchiveIterator
import urllib3
urllib3.disable_warnings()

OUT=Path('notes_master_math_france_missing_cc')
OUT.mkdir(parents=True,exist_ok=True)
UA='Aurelien-course-library/1.0 (academic personal library recovery)'
H={'User-Agent':UA}

RECORDS=[
{'num':1,'title':'Cours de probabilités','path':'01 - Proba-stat/01.1 Probabilites M1/01 - Cours de probabilites - Yves Coudene (2015).pdf','urls':['https://perso.lpsm.paris/~coudene/probabilites.pdf','http://perso.lpsm.paris/~coudene/probabilites.pdf']},
{'num':4,'title':'Intégration, Probabilités et Processus Aléatoires','path':'01 - Proba-stat/01.1 Probabilites M1/04 - Integration, Probabilites et Processus Aleatoires - Jean-Francois Le Gall.pdf','urls':['https://www.imo.universite-paris-saclay.fr/~jean-francois.le-gall/IPPA2.pdf','http://www.math.u-psud.fr/~jflegall/IPPA2.pdf']},
{'num':5,'title':'Probabilités approfondies : martingales et chaînes de Markov','path':'01 - Proba-stat/01.2 Processus, Markov et martingales/05 - Probabilites approfondies martingales et chaines de Markov - Thomas Duquesne (2012).pdf','urls':['https://perso.lpsm.paris/~broutinn/teaching/4M011_poly_duquesne.pdf','http://perso.lpsm.paris/~broutinn/teaching/4M011_poly_duquesne.pdf']},
{'num':11,'title':'Statistique, Partie 2 : approche bayésienne','path':'01 - Proba-stat/01.5 Bayesien et MCMC/11 - Statistique, Partie 2 approche bayesienne - Anna Ben-Hamou; Arnaud Guyader.pdf','urls':['https://perso.lpsm.paris/~aguyader/files/teaching/M1/PolycopiePartie2.pdf','http://perso.lpsm.paris/~aguyader/files/teaching/M1/PolycopiePartie2.pdf']},
{'num':15,'title':'Calcul stochastique et processus de diffusion','path':'01 - Proba-stat/01.3 Calcul stochastique et diffusions/15 - Calcul stochastique et processus de diffusion - Nicolas Fournier.pdf','urls':['https://perso.lpsm.paris/~nfournier/PolyCS.pdf','http://perso.lpsm.paris/~nfournier/PolyCS.pdf']},
{'num':19,'title':'Modélisation et statistique bayésienne computationnelle','path':'01 - Proba-stat/01.5 Bayesien et MCMC/19 - Modelisation et statistique bayesienne computationnelle - Nicolas Bousquet (2026).pdf','urls':['https://perso.lpsm.paris/~bousquet/poly-complet-2026-V1.pdf','https://perso.lpsm.paris/~bousquet/poly-complet-2025.pdf','https://perso.lpsm.paris/~bousquet/cours-complet-2024.pdf','https://perso.lpsm.paris/~bousquet/cours-complet-2020.pdf']},
{'num':25,'title':'Méthodes de tenseurs pour les problèmes en grande dimension','path':'03 - EDP et calcul scientifique/25 - Methodes de tenseurs pour les problemes en grande dimension (2024).pdf','urls':['https://www.ljll.fr/MathModel/enseignement/cours/TenseursM2_2024.pdf','http://www.ljll.fr/MathModel/enseignement/cours/TenseursM2_2024.pdf']},
{'num':33,'title':'Contrôle optimal : théorie et applications','path':'02 - Analyse, optimisation et outils/Optimisation et controle/33 - Controle optimal theorie et applications - Emmanuel Trelat.pdf','urls':['https://www.ljll.fr/~trelat/fichiers/livreopt.pdf','http://www.ljll.fr/~trelat/fichiers/livreopt.pdf']},
{'num':34,'title':'Méthodes mathématiques et numériques pour les plasmas','path':'03 - EDP et calcul scientifique/34 - Methodes mathematiques et numeriques pour les plasmas - Bruno Despres (2021).pdf','urls':['https://www.ljll.fr/despres/BD_fichiers/m2_plasma.pdf','http://www.ljll.fr/despres/BD_fichiers/m2_plasma.pdf']},
{'num':35,'title':'Équations aux dérivées partielles elliptiques','path':'03 - EDP et calcul scientifique/35 - Equations aux derivees partielles elliptiques - Herve Le Dret (2010).pdf','urls':['https://www.ljll.fr/ledret/M2Elliptique/chapitre4.pdf','http://www.ljll.fr/ledret/M2Elliptique/chapitre4.pdf']},
]

def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def validate_bytes(data:bytes):
 if len(data)<1024 or not data.startswith(b'%PDF-'): raise ValueError(f'non PDF ou trop petit: {len(data)} octets, magic={data[:12]!r}')
 n=len(PdfReader(io.BytesIO(data),strict=False).pages)
 if n<1: raise ValueError('aucune page')
 return n

def direct(url):
 r=requests.get(url,headers=H,timeout=(10,45),verify=False)
 r.raise_for_status(); data=r.content
 return data,r.url,'direct'

def get_indexes():
 r=requests.get('https://index.commoncrawl.org/collinfo.json',headers=H,timeout=30)
 r.raise_for_status()
 cols=r.json()
 return [(c['id'],c['cdx-api']) for c in cols[:80]]

INDEXES=get_indexes()
print('INDEXES',len(INDEXES),INDEXES[0][0],INDEXES[-1][0],flush=True)

def query_index(api,url):
 q=f"{api}?url={quote_plus(url)}&output=json"
 r=requests.get(q,headers=H,timeout=(10,35))
 if r.status_code==404: return []
 r.raise_for_status()
 out=[]
 for line in r.text.splitlines():
  line=line.strip()
  if not line: continue
  try: out.append(json.loads(line))
  except json.JSONDecodeError: pass
 return out

def fetch_warc(rec):
 offset=int(rec['offset']); length=int(rec['length'])
 url='https://data.commoncrawl.org/'+rec['filename']
 rr=requests.get(url,headers={**H,'Range':f'bytes={offset}-{offset+length-1}'},timeout=(15,120))
 if rr.status_code not in (200,206): raise RuntimeError(f'WARC HTTP {rr.status_code}')
 raw=rr.content
 for record in ArchiveIterator(io.BytesIO(raw)):
  if record.rec_type in ('response','resource'):
   data=record.content_stream().read()
   if data.startswith(b'%PDF-'): return data
   pos=data.find(b'%PDF-')
   if 0<pos<4096: return data[pos:]
 raise ValueError(f'aucun payload PDF dans le segment WARC ({len(raw)} octets)')

def recover(rec):
 errors=[]
 for u in rec['urls']:
  try:
   data,src,kind=direct(u); pages=validate_bytes(data)
   return {**rec,'status':'ok','source_url':src,'source_kind':kind,'pages':pages,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'data':data,'detail':''}
  except Exception as e: errors.append(f'direct {u}: {type(e).__name__}: {e}')
 for u in rec['urls']:
  for idx,api in INDEXES:
   try:
    hits=query_index(api,u)
   except Exception as e:
    errors.append(f'index {idx} {u}: {type(e).__name__}: {e}')
    continue
   hits.sort(key=lambda x:(x.get('status')!='200','pdf' not in (x.get('mime') or '').lower(),-(int(x.get('timestamp','0') or 0))))
   for hit in hits[:5]:
    if hit.get('status') not in (None,'200'): continue
    try:
     data=fetch_warc(hit); pages=validate_bytes(data)
     src=f"commoncrawl:{idx}:{hit.get('timestamp','')}:{hit.get('url',u)}"
     return {**rec,'status':'ok','source_url':src,'source_kind':'commoncrawl','pages':pages,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'data':data,'detail':''}
    except Exception as e: errors.append(f'warc {idx} {u}: {type(e).__name__}: {e}')
 return {**rec,'status':'error','source_url':'','source_kind':'','pages':0,'bytes':0,'sha256':'','data':b'','detail':' | '.join(errors)[-16000:]}

results=[]
with cf.ThreadPoolExecutor(max_workers=5) as ex:
 futures={ex.submit(recover,r):r for r in RECORDS}
 for fut in cf.as_completed(futures):
  rec=futures[fut]
  try: x=fut.result()
  except BaseException as e:
   import traceback
   x={**rec,'status':'error','source_url':'','source_kind':'','pages':0,'bytes':0,'sha256':'','data':b'','detail':'UNHANDLED '+traceback.format_exc()}
  if x['status']=='ok':
   dest=OUT/x['path']; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(x.pop('data'))
  else: x.pop('data',None)
  results.append(x)
  print(f"[{x['num']:02d}] {x['status']} pages={x['pages']} bytes={x['bytes']} kind={x['source_kind']} {x['title']} detail={x['detail'][-300:]}",flush=True)
results.sort(key=lambda x:x['num'])
fields=['num','title','path','urls','status','source_url','source_kind','pages','bytes','sha256','detail']
serial=[]
for r in results:
 z=dict(r);z['urls']=' | '.join(z['urls']);serial.append(z)
with (OUT/'manifest_commoncrawl.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(serial)
(OUT/'manifest_commoncrawl.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
errs=[r for r in results if r['status']!='ok']
print(f'SUCCES={len(results)-len(errs)} ECHECS={len(errs)}',flush=True)
for r in errs: print('ECHEC',r['num'],r['title'],r['detail'],file=sys.stderr)
sys.exit(1 if errs else 0)
