from pathlib import Path
from lxml import html
import re,pandas as pd
B=Path(__file__).parent
out=[]
def clean(x):return re.sub(r'\[\d+\]','',' '.join(x.split()))
def group(p):return 'Labor' if p=='Labor' else 'Coalition' if p in ['Liberal','National','Nationals','Liberal/National'] else 'Other'
for f in sorted((B/'sources').glob('*.html')):
 y=int(f.stem);r=html.fromstring(f.read_text())
 for t in r.xpath('//table[contains(@class,"wikitable")]'):
  cap=t.xpath('./caption');s=clean(cap[0].text_content()) if cap else ''
  seat=s.split(':',1)[-1].strip() if 'state election:' in s else 'Narracan' if 'Narracan supplementary' in s else None
  if seat is None:continue
  primary=[];blocks=[];mode='primary';block=[]
  for tr in t.xpath('./tbody/tr|./tr'):
   v=[clean(c.text_content()) for c in tr.xpath('./th|./td')]
   if len(v)==1 and ('result' in v[0].lower() or 'count' in v[0].lower()):
    if block:blocks.append((mode,block));block=[]
    mode=v[0]
   if len(v)>=5 and v[0]=='':
    try:n=int(v[3].replace(',',''))
    except ValueError:continue
    d={'party':v[1],'candidate':v[2],'votes':n}
    if mode=='primary':primary.append(d)
    else:block.append(d)
  if block:blocks.append((mode,block))
  tpp=[(k,v) for k,v in blocks if len(v)==2 and {group(d['party']) for d in v}=={'Labor','Coalition'}]
  tcp=[(k,v) for k,v in blocks if 'candidate' in k.lower() and len(v)==2]
  final=tcp[-1] if tcp else blocks[-1] if blocks else ('Two-candidate primary contest',primary) if len(primary)==2 else None
  if not tpp and len(primary)==2 and {group(d['party']) for d in primary}=={'Labor','Coalition'}:tpp=[('Two-candidate primary contest',primary)]
  row={'election_year':y,'electorate':seat,'source_url':f'https://en.wikipedia.org/wiki/Results_of_the_{y}_Victorian_state_election_(Legislative_Assembly)'}
  for tag,selected in [('tpp',tpp[-1] if tpp else None),('tcp',final)]:
   row[tag+'_status']='Published' if selected else 'Not found in source'
   if selected:
    kind,vals=selected;total=sum(d['votes'] for d in vals);row[tag+'_total']=total;row[tag+'_source_count_type']=kind
    for g in ['Labor','Coalition','Other']:
     n=sum(d['votes'] for d in vals if group(d['party'])==g);row[tag+'_'+g.lower()+'_votes']=n;row[tag+'_'+g.lower()+'_pct']=round(n/total*100,4)
    row[tag+'_candidates']='; '.join(d['candidate']+' ('+d['party']+')' for d in vals)
  out.append(row)
df=pd.DataFrame(out).sort_values(['election_year','electorate']);df.to_csv(B/'final_preference_counts_1982_2022.csv',index=False)
print(df.groupby(['election_year','tpp_status']).size().to_string())
