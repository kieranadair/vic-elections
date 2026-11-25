from pathlib import Path
import json
from types import ModuleType
import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts,Map

# Community Cloud can retain imported helper modules while pulling a new app.py.
# Execute the current trusted repository source in an isolated module per run,
# bypassing both sys.modules and .pyc caches without reloading shared state.
chart_path=Path(__file__).with_name('charts.py')
charts=ModuleType('_vic_elections_charts')
charts.__file__=str(chart_path)
exec(compile(chart_path.read_bytes(),str(chart_path),'exec'),charts.__dict__)
D=Path(__file__).parent/'data'
st.set_page_config(page_title='Victoria · Electoral currents',layout='wide',initial_sidebar_state='collapsed')
st.html('<style>[data-testid="stMainBlockContainer"] {max-width: 1200px; padding-left: 2rem; padding-right: 2rem;}</style>')
st.title('Victoria · Electoral currents')
st.caption('State Legislative Assembly · 1982–2022 · Labor / Coalition / Other')
@st.cache_data
def load(file_versions):
 return (pd.read_csv(D/'first_preferences.csv'),pd.read_csv(D/'final_counts.csv'),pd.read_csv(D/'centroids.csv').query('boundary_year==2022').drop(columns='boundary_year'),json.loads((D/'boundaries_2022.geojson').read_text()))
# Source-code caching does not track changes to CSV/GeoJSON file contents.
# Include file versions so a live deploy cannot reuse data from the prior build.
file_versions=tuple(
 (str(path),path.stat().st_mtime_ns,path.stat().st_size)
 for path in (D/'first_preferences.csv',D/'final_counts.csv',D/'centroids.csv',D/'boundaries_2022.geojson')
)
first,final,centres,geo=load(file_versions);years=sorted(first.election_year.unique().tolist())
with st.sidebar:
 st.header('Data quality')
 include=st.checkbox('Include unreconciled historical primary totals',True)
 st.caption('19 historical seat tables have candidate sums that differ from their formal total. Their ternary shares use the candidate sum; an asterisk on hovered seat names flags them.')
t1,t2,t3=st.tabs(['Ternary','Windsock map','Data & methods'],key='view_tab',on_change='rerun')
with t1:
 st.subheader('How first preferences changed')
 st.caption('One circle per seat · Position: first preferences · Colour: elected party after preferences. Hover a circle for its name and vote-share guides.')
 st.markdown(' &nbsp; '.join(f'<span style="color:{color}">●</span> {party}' for party,color in charts.PARTY_COLORS.items()),unsafe_allow_html=True)
 df=first if include else first[first.reconciles]
 if t1.open:
  gallery=st.grid(2,min_column_width=380,width=1080,gap=20)
  for year in years:
   with gallery.cell():
    with st.container(width=520):
     st_echarts(charts.ternary_options(df,year),height='460px',key=f'ternary-{year}')
with t2:
 with st.expander('Map year and playback',expanded=True):
  start=st.selectbox('Start year',years,index=len(years)-1)
  play=st.toggle('Play map from start year',False)
  speed=st.slider('Seconds per election',1.,5.,2.,.5)
 c1,c2,c3=st.columns(3)
 with c1:basis=st.selectbox('Final count',['Labor–Coalition 2PP','Actual final two (2CP)'])
 with c2:focus=st.selectbox('Focus group',charts.GROUPS[:2] if basis=='Labor–Coalition 2PP' else charts.GROUPS)
 with c3:margin=st.selectbox('Length measure',['Lead over opponent','Swing needed to tie'])
 c1,c2=st.columns(2)
 with c1:zoom=st.radio('Map view',['Victoria','Melbourne'],horizontal=True)
 with c2:scale=st.slider('Pixels per percentage point',.25,3.,1.,.25)
 socks=charts.windsock_rows(final,centres,focus,basis,margin=='Swing needed to tie')
 st.caption('45° up-right: focus wins · 135° up-left: opponent wins · length: absolute margin in percentage points. Zoom and pan to inspect crowded seats.')
 st.caption('Fixed 2022 boundaries and geometric centroids in every year, matched by seat name. Unmatched names drop out. Historical locations are references, not reconstructed historical boundaries.')
 if t2.open:st_echarts(charts.map_options(socks,years,start,play,int(speed*1000),focus,scale,zoom),map=Map('Victoria',geo),height='710px',key='windsock')
 if basis=='Actual final two (2CP)':st.caption('A focus group eliminated before the final two has no final margin and is omitted. Other combines the remaining non-major candidates. 2PP and 2CP can tell different stories.')
 missing=final[~final.electorate.isin(centres.electorate)].groupby('election_year').size()
 with st.expander('Map coverage by year'):
  coverage=final.groupby('election_year').size().rename('Seats contested').to_frame();coverage['Matched to 2022 map']=final[final.electorate.isin(centres.electorate)].groupby('election_year').size();coverage['Windsocks available']=socks.groupby('election_year').size();st.dataframe(coverage.fillna(0).astype(int),width="stretch")
with t3:
 st.write('The ternary uses first preferences summed into Labor, Liberal/National Coalition and Other, divided by the candidate-vote sum. Official 2022 counts supersede secondary-source primary totals. Earlier figures come from historical result tables and retain reconciliation flags.')
 st.write('2PP means Labor versus Coalition, including alternate counts in seats where those were not the final candidates. 2CP means the actual final pair. Missing counts stay missing. Narracan had no Labor candidate in its January 2023 supplementary poll and therefore has no Labor–Coalition 2PP.')
 st.write('Lead = focus percentage − opponent percentage. Swing needed to tie = half that lead. Both are calculated within the selected final count. Arrow angles use the horizontal axis as 0°, pointing upwards at 45° or 135°.')
 st.write('2022 full distributions include later indicative counts conducted for statistical purposes. Historical final counts are secondary-source published figures and have not all been independently checked against original election reports.')
 st.markdown('[VEC results](https://www.vec.vic.gov.au/results/state-election-results) · [Full distributions](https://www.vec.vic.gov.au/results/electoral-statistics/state-election-statistics/full-preference-distributions) · [Boundary files and original-source links](https://github.com/jwood74/geographic_boundaries/tree/main/au/sed/sed_vic)')
 st.caption('2021 redistribution geometry used at the 2022 election. Polygon centroids are geometric, not population centres. Seats with unchanged names may have changed boundaries. Playback links seat names across years; it does not infer successors to abolished seats.')
 table=st.selectbox('Table',['First preferences','Final counts'])
 data={'First preferences':first,'Final counts':final}[table]
 yr=st.selectbox('Table year',sorted(data.election_year.unique().tolist()),index=len(data.election_year.unique())-1)
 st.dataframe(data[data.election_year==yr],width="stretch",hide_index=True)
 st.download_button('Download all chart inputs (CSV)',(D/'chart_inputs.csv').read_bytes(),file_name='victoria_chart_inputs.csv',mime='text/csv')
 st.download_button('Download complete table (CSV)',data.to_csv(index=False),file_name=table.lower().replace(' ','_')+'.csv',mime='text/csv')
