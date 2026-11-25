from pathlib import Path
from lxml import html
import pandas as pd,json,re
from shapely.geometry import shape,mapping
B=Path(__file__).parent;S=B/'research';rows=[]
for p in sorted((S/'sources').glob('*.html')):
 year=int(p.stem)
 for t in html.fromstring(p.read_text()).xpath('//table[contains(@class,"wikitable")]'):
  cap=t.xpath('./caption');title=' '.join(cap[0].text_content().split()) if cap else ''
  seat=re.sub(r'\[\d+\]','',title.split(':',1)[-1]).strip() if 'state election:' in title else 'Narracan' if 'Narracan supplementary' in title else None
  if seat is None:continue
  sums=dict(Labor=0,Coalition=0,Other=0);formal=None
  for tr in t.xpath('./tbody/tr|./tr'):
   v=[' '.join(c.text_content().split()) for c in tr.xpath('./td|./th')]
   if v and v[0]=='Total formal votes':formal=int(v[1].replace(',',''));break
   if len(v)>=5 and v[0]=='':
    try:n=int(v[3].replace(',',''))
    except ValueError:continue
    g='Labor' if v[1]=='Labor' else 'Coalition' if v[1] in ['Liberal','National','Nationals'] else 'Other';sums[g]+=n
  total=sum(sums.values());row=dict(election_year=year,electorate=seat,source_formal=formal,candidate_sum=total,reconciles=formal==total,source_url=f'https://en.wikipedia.org/wiki/Results_of_the_{year}_Victorian_state_election_(Legislative_Assembly)')
  for g,n in sums.items():row[g.lower()+'_votes']=n;row[g.lower()+'_pct']=100*n/total
  rows.append(row)
df=pd.DataFrame(rows);rounds=pd.read_csv(B/'data/rounds_2022.csv')
for _,r in rounds[rounds.stage==0].iterrows():
 i=df.index[(df.election_year==2022)&(df.electorate==r.electorate)][0]
 for g in ['labor','coalition','other']:
  df.loc[i,g+'_votes']=r[g+'_votes'];df.loc[i,g+'_pct']=100*r[g+'_votes']/r.total_votes
 df.loc[i,'candidate_sum']=r.total_votes;df.loc[i,'source_formal']=r.total_votes;df.loc[i,'reconciles']=True;df.loc[i,'source_url']=r.source_url
assert len(df)==1049;assert not df.duplicated(['election_year','electorate']).any()
df.to_csv(B/'data/first_preferences.csv',index=False)
centres=[]
for epoch in [2014,2022]:
 f=B/'data'/f'boundaries_{epoch}.geojson';geo=json.loads(f.read_text())
 for ft in geo['features']:
  geom=shape(ft['geometry']);c=geom.centroid
  centres.append(dict(boundary_year=epoch,electorate=ft['properties']['Name'],longitude=c.x,latitude=c.y))
  ft['properties']['name']=ft['properties']['Name'];ft['geometry']=mapping(geom.simplify(.001,preserve_topology=True))
 f.write_text(json.dumps(geo,separators=(',',':')))
pd.DataFrame(centres).to_csv(B/'data/centroids.csv',index=False)
print('First preferences',len(df),'unreconciled',sum(~df.reconciles),'centroids',len(centres))
