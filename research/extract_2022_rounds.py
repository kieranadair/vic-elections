from pathlib import Path
import pandas as pd,re,json
from lxml import html
B=Path(__file__).parent;P=B/'preferences';out=[];status=[]
def clean(s):return ' '.join(str(s).split())
def group(p):return 'Labor' if 'Australian Labor' in p else 'Coalition' if p in ['Liberal','The Nationals','National Party of Australia - Victoria','National'] else 'Other'
def num(x):
 try:return int(str(x).replace(',','').strip())
 except:return None
manifest=dict(json.loads((P/'manifest.json').read_text()))
for pf in sorted((P/'district_pages').glob('*_primary.html')):
 seat=pf.name.removesuffix('_primary.html');slug=seat.lower().replace(' ','-');url=f'https://www.vec.vic.gov.au/results/state-election-results/2022-state-election-results/results-by-district/{slug}-district-results'
 try:r=html.fromstring(pf.read_text())
 except:continue
 parties={}
 for t in r.xpath('//table'):
  for tr in t.xpath('.//tr'):
   v=[clean(c.text_content()) for c in tr.xpath('./td|./th')]
   if len(v)==4 and num(v[2]) is not None:parties[v[0].upper()]=v[1]
 records=[];source=None
 supp=list(P.glob(seat+'.xls*'))
 if supp:
  f=supp[0];df=pd.read_excel(f,header=None);hdr=next((i for i in df.index if 'Candidates Names' in str(df.iloc[i,0])),None)
  if hdr is not None:
   cols=[j for j in range(1,len(df.columns)) if pd.notna(df.iloc[hdr,j]) and clean(df.iloc[hdr,j])!='TOTAL'];names=[clean(df.iloc[hdr,j]).upper() for j in cols]
   for i in range(hdr+1,len(df)):
    label=clean(df.iloc[i,0])
    if label.startswith(('Total first','Progressive Total','FINAL TOTAL')):records.append((label,[num(df.iloc[i,j]) for j in cols]))
   source=manifest[seat]
 else:
  f=P/'district_pages'/(seat+'_distribution.html')
  try:d=html.fromstring(f.read_text())
  except:continue
  for t in d.xpath('//table'):
   h=t.xpath('./thead/tr/th');names=[clean(x.text_content()).upper() for x in h[1:-1]]
   for tr in t.xpath('./tbody/tr'):
    cells=tr.xpath('./th|./td');label=clean(cells[0].text_content()) if cells else ''
    if label.startswith(('Total first','Progressive Total','FINAL TOTAL')):records.append((label,[num(c.text_content()) for c in cells[1:-1]]))
  source=url+'/'+slug+'-results-distribution'
 missing=[n for n in names if n not in parties] if records else []
 status.append(dict(election_year=2022,electorate=seat,rounds=len(records),unmapped_candidates='; '.join(missing),source_url=source or url))
 if missing:continue
 for i,(label,vals) in enumerate(records):
  if len(vals)!=len(names):continue
  active=[(n,v) for n,v in zip(names,vals) if v is not None and v>0];total=sum(v for n,v in active)
  row=dict(election_year=2022,electorate=seat,stage=i,stage_label=label,candidates_remaining=len(active),total_votes=total,source_url=source)
  for g in ['Labor','Coalition','Other']:
   n=sum(v for name,v in active if group(parties[name])==g);row[g.lower()+'_votes']=n;row[g.lower()+'_pct']=round(100*n/total,4) if total else None
  row['remaining_candidates']='; '.join(n+' ('+parties[n]+')' for n,v in active);out.append(row)
df=pd.DataFrame(out);df.to_csv(B/'preference_rounds_2022.csv',index=False);pd.DataFrame(status).to_csv(B/'preference_coverage_2022.csv',index=False)
print('Districts',df.electorate.nunique() if len(df) else 0,'rounds',len(df));print(pd.DataFrame(status).query('rounds==0 or unmapped_candidates!=""').to_string(index=False))
