from pathlib import Path
from lxml import html
import pandas as pd
import re
BASE=Path(__file__).parent
rows=[];candidates=[];issues=[]
def clean(s): return re.sub(r'\[\d+\]', '', ' '.join(s.split())).strip()
def group(p): return 'Labor' if p=='Labor' else 'Coalition' if p in ['Liberal','National','Nationals','Liberal/National'] else 'Other'
def integer(s): return int(s.replace(',',''))
for path in sorted((BASE/'sources').glob('*.html')):
 year=int(path.stem);root=html.fromstring(path.read_text())
 for t in root.xpath('//table[contains(@class,"wikitable")]'):
  caps=t.xpath('./caption');cap=clean(caps[0].text_content()) if caps else ''
  if not cap:continue
  seat=cap.split(':',1)[-1].strip() if 'state election:' in cap else 'Narracan' if 'Narracan supplementary' in cap else None
  if not seat: continue
  prim=[];pref=[];mode='primary';formal=None;winparty=None
  for tr in t.xpath('./tbody/tr|./tr'):
   v=[clean(c.text_content()) for c in tr.xpath('./td|./th')]
   if not v:continue
   if len(v)==1:
    if 'result' in v[0].lower() or 'count' in v[0].lower():mode=v[0]
    continue
   if v[0]=='Total formal votes':formal=integer(v[1]);mode='totals'
   if len(v)>=5 and v[0]=='':
    if re.search(r' (hold|gain|retain|win)\b',v[1]):
     winparty=re.split(r' (?:hold|gain|retain|win)\b',v[1])[0];continue
    try: vote=integer(v[3]);pct=float(v[4])
    except ValueError:continue
    d=dict(party=v[1],candidate=v[2],votes=vote,pct=pct)
    if mode=='primary':prim.append(d)
    elif mode!='totals':pref.append(dict(d,kind=mode))
  if not prim:issues.append((year,seat,'no candidates'));continue
  tcp=[p for p in pref if 'candidate' in p['kind'].lower()]
  pool=tcp or pref or prim
  winner=max(pool,key=lambda d:d['votes'])
  if winparty and winner['party']!=winparty:issues.append((year,seat,'winner mismatch',winparty,winner))
  sums={g:sum(p['votes'] for p in prim if group(p['party'])==g) for g in ['Labor','Coalition','Other']}
  if formal!=sum(sums.values()):issues.append((year,seat,'formal mismatch',formal,sum(sums.values())))
  source=f'https://en.wikipedia.org/wiki/Results_of_the_{year}_Victorian_state_election_(Legislative_Assembly)'
  row=dict(election_year=year,electorate=seat,winner_group=group(winner['party']),winner_party=winner['party'],winner=winner['candidate'],formal_votes=formal)
  for g,n in sums.items(): row[g.lower()+'_votes']=n;row[g.lower()+'_pct']=round(n/formal*100,4) if formal else None
  row['notes']='Supplementary election held 28 January 2023; no Labor candidate.' if year==2022 and seat=='Narracan' else 'Frankston East supplementary election held 16 October 1999.' if year==1999 and seat=='Frankston East' else ''
  row['source_url']=source;rows.append(row)
  for p in prim:candidates.append(dict(election_year=year,electorate=seat,group=group(p['party']),**p,source_url=source))

df=pd.DataFrame(rows).sort_values(['election_year','electorate'])
df=df[['election_year','electorate','winner_group','winner_party','winner','notes','source_url']]
assert not df.duplicated(['election_year','electorate']).any()
df.to_csv(BASE/'seat_results_1982_2022.csv',index=False)
matrix=df.pivot(index='electorate',columns='election_year',values='winner_group').fillna('—');matrix.to_csv(BASE/'seat_winners_matrix.csv')
summary=pd.crosstab(df.election_year,df.winner_group)[['Labor','Coalition','Other']];summary['Total']=summary.sum(axis=1)
summary.to_csv(BASE/'statewide_seat_totals.csv')
expected={1982:(49,32,0),1985:(47,41,0),1988:(46,42,0),1992:(27,61,0),1996:(29,58,1),1999:(42,43,3),2002:(62,24,2),2006:(55,32,1),2010:(43,45,0),2014:(47,38,3),2018:(55,27,6),2022:(56,28,4)}
for year,counts in expected.items():assert tuple(summary.loc[year,['Labor','Coalition','Other']])==counts
notes=[
('Scope','Victorian state Legislative Assembly general elections, 1982–2022. 12 elections; 1,049 electorate-election results. Compiled 25 November 2026.'),
('Measure','Winner of each seat at each general election, not current membership. By-elections excluded except supplementary polls completing a general election.'),
('Labor','Australian Labor Party.'),
('Coalition','Liberal and National parties combined for comparison, including years in which they campaigned separately.'),
('Other','All remaining winning parties and independents; actual party and candidate appear in Seat results.'),
('Boundaries','Electorate names reflect each election. A repeated name does not guarantee unchanged boundaries. Dash means the electorate name was not contested that year; no attempt to map abolished or renamed seats.'),
('1982','81 seats; expanded to 88 from 1985.'),
('Supplementary polls','1999 includes Frankston East (16 October 1999); 2022 includes Narracan (28 January 2023).'),
('Sources','Wikipedia electorate result tables, which cite VEC reports and historical election archives; exact URL on every detailed row. Original HTML retained in sources directory.'),
('Validation','Unique year/electorate pairs; all expected seats present; grouped seat totals checked against election summary tables. Winner taken from preference result, or primary result for a two-candidate contest.'),
('Vote counts','Omitted: some source candidate vote totals do not reconcile to published formal totals. This is a seat-winner dataset, not a verified vote-share dataset.'),
('Latest election','2022 is the latest completed general election as of compilation; 2026 election scheduled for 28 November.'),
('Official results','https://www.vec.vic.gov.au/results/state-election-results'),
('2022 parliamentary report','https://www.parliament.vic.gov.au/49950e/globalassets/sections-shared/about/publications/research-papers/the2022victorianstateelection_rp_2023_2.pdf')]
with pd.ExcelWriter(BASE/'victoria_election_results_1982_2022.xlsx',engine='openpyxl') as w:
 matrix.to_excel(w,sheet_name='Seat winners matrix');df.to_excel(w,sheet_name='Seat results',index=False);summary.to_excel(w,sheet_name='Seat totals');pd.DataFrame(notes,columns=['Topic','Explanation']).to_excel(w,sheet_name='Notes and sources',index=False)
 for sh in w.book:
  sh.freeze_panes='B2';sh.auto_filter.ref=sh.dimensions
  for col in sh.columns:
   sh.column_dimensions[col[0].column_letter].width=min(70,max(14,max(len(str(c.value or '')) for c in col[:100])+2))
print(summary.to_string());print('Saved',len(df),'results')
