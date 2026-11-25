"""ECharts option builders. Geometry and vote calculations are testable in Python."""
import math
from streamlit_echarts import JsCode
GROUPS=['Labor','Coalition','Other']
COLORS={'Labor':'#d34a59','Coalition':'#367ac3','Other':'#c89b35'}
def ternary_xy(labor,coalition,other):
 total=labor+coalition+other
 return ((coalition+other/2)/total,math.sqrt(3)/2*other/total)
def timeline(years,start,play=False,speed=1800):
 return dict(axisType='category',data=[str(y) for y in years],currentIndex=years.index(start) if start in years else 0,autoPlay=play,loop=False,playInterval=speed,bottom=8,left=45,right=45,label=dict(color='#aebbd0'),lineStyle=dict(color='#5a6c84'),controlStyle=dict(color='#d7e3f4',borderColor='#d7e3f4'))
def common():
 return dict(backgroundColor='#111c2c',textStyle=dict(color='#d7e3f4'),animationDurationUpdate=900,animationEasingUpdate='cubicInOut')
def ternary_options(df,years,start,play,speed):
 render=JsCode("""function(p,a){var q=a.coord([a.value(0),a.value(1)]);return {type:'circle',id:a.value(6),shape:{cx:q[0],cy:q[1],r:5},style:a.style({opacity:0.8,stroke:'#111c2c',lineWidth:1}),transition:['shape']};}""").js_code
 tip=JsCode("""function(p){var v=p.value;return v[6]+'<br>Labor '+v[2].toFixed(2)+'%<br>Coalition '+v[3].toFixed(2)+'%<br>Other '+v[4].toFixed(2)+'%<br>'+v[5];}""").js_code
 gridlines=[]
 for k in [.2,.4,.6,.8]:
  for ends in [((k,1-k,0),(k,0,1-k)),((1-k,k,0),(0,k,1-k)),((1-k,0,k),(0,1-k,k))]:
   gridlines.append(dict(type='line',coordinateSystem='cartesian2d',data=[list(ternary_xy(*v)) for v in ends],symbol='none',lineStyle=dict(color='#2d3a4d',width=1),silent=True,tooltip=dict(show=False),z=0))
 edge=dict(type='line',data=[[0,0],[1,0],[.5,math.sqrt(3)/2],[0,0]],symbol='none',lineStyle=dict(color='#8fa0b8',width=1),silent=True,tooltip=dict(show=False))
 base=common();base.update(timeline=timeline(years,start,play,speed),grid=dict(top=65,bottom=110,left='12%',right='12%',containLabel=False),xAxis=dict(type='value',min=-.12,max=1.12,show=False),yAxis=dict(type='value',min=-.1,max=1.0,show=False),legend=dict(data=GROUPS,top=8,textStyle=dict(color='#d7e3f4')),tooltip=dict(trigger='item',formatter=tip,confine=True),graphic=[dict(type='text',left='10%',bottom=85,style=dict(text='Labor 100%',fill='#d7e3f4')),dict(type='text',right='8%',bottom=85,style=dict(text='Coalition 100%',fill='#d7e3f4')),dict(type='text',left='center',top=46,style=dict(text='Other 100%',fill='#d7e3f4'))])
 opts=[]
 for year in years:
  sub=df[df.election_year==year];series=gridlines+[edge]
  for g in GROUPS:
   data=[]
   for _,r in sub.iterrows():
    vals=[float(r[x+'_pct']) for x in ['labor','coalition','other']]
    if GROUPS[max(range(3),key=lambda j:vals[j])]!=g:continue
    x,y=ternary_xy(*vals);quality='Source totals differ; shares normalised to candidate sum' if 'reconciles' in r and not r.reconciles else 'Shares sum to 100%'
    data.append(dict(id=r.electorate,name=r.electorate,value=[x,y,*vals,quality,r.electorate]))
   series.append(dict(type='custom',name=g,renderItem=render,data=data,itemStyle=dict(color=COLORS[g]),encode=dict(x=0,y=1),universalTransition=True,z=3))
  opts.append(dict(title=dict(text=str(year),left=20,top=40,textStyle=dict(color='#d7e3f4',fontSize=22)),series=series))
 return dict(baseOption=base,options=opts)
def windsock_rows(final,centres,focus,basis,half=False):
 d=final.merge(centres,on='electorate',how='inner',validate='many_to_one');tag='tpp' if basis=='Labor–Coalition 2PP' else 'tcp';g=focus.lower()
 d=d[d[tag+'_status']=='Published'].copy()
 # A candidate eliminated before the actual final two has no final margin.
 d=d[d[tag+'_'+g+'_votes']>0].copy();d['focus_pct']=d[tag+'_'+g+'_pct'];d['opponent_pct']=100-d.focus_pct;d['signed_margin']=2*d.focus_pct-100
 if half:d['signed_margin']/=2
 d['angle']=d.signed_margin.apply(lambda n:45 if n>=0 else 135)
 return d

def map_options(df,years,start,play,speed,focus,scale,zoom):
 render=JsCode("""function(p,a){var q=a.coord([a.value(0),a.value(1)]),m=a.value(2),len=Math.abs(m)*SCALE,theta=(m>=0?45:135)*Math.PI/180,dx=Math.cos(theta),dy=-Math.sin(theta),x=q[0]+len*dx,y=q[1]+len*dy,c=m>=0?FOCUS:'#8795ac';return {type:'group',id:a.value(5),children:[{type:'circle',shape:{cx:q[0],cy:q[1],r:2.5},style:{fill:c}},{type:'line',shape:{x1:q[0],y1:q[1],x2:x,y2:y},style:{stroke:c,lineWidth:2.4},transition:['shape']},{type:'polygon',shape:{points:[[x,y],[x-5*dx+3*dy,y-5*dy-3*dx],[x-5*dx-3*dy,y-5*dy+3*dx]]},style:{fill:c},transition:['shape']} ]};}""".replace('SCALE',str(scale)).replace('FOCUS',repr(COLORS[focus]))).js_code
 tip=JsCode("""function(p){var v=p.value;return v[5]+'<br>'+FOCUS+' '+v[3].toFixed(2)+'%<br>Opponent '+v[4].toFixed(2)+'%<br>Margin '+Math.abs(v[2]).toFixed(2)+' pp<br>'+(v[2]>=0?'45° · focus wins':'135° · opponent wins');}""".replace('FOCUS',repr(focus))).js_code
 base=common();base.update(timeline=timeline(years,start,play,speed),geo=dict(map='Victoria',roam=True,center=[144.96,-37.81] if zoom=='Melbourne' else [145.4691,-36.5589],zoom=16 if zoom=='Melbourne' else .8,top=60,bottom=70,itemStyle=dict(areaColor='#1e2d42',borderColor='#617189',borderWidth=.6),emphasis=dict(itemStyle=dict(areaColor='#344b66')),silent=True),tooltip=dict(trigger='item',formatter=tip,confine=True))
 opts=[]
 for year in years:
  sub=df[df.election_year==year];data=[dict(id=r.electorate,name=r.electorate,value=[r.longitude,r.latitude,r.signed_margin,r.focus_pct,r.opponent_pct,r.electorate]) for _,r in sub.iterrows()]
  opts.append(dict(title=dict(text=f'{year} · {len(sub)} seats shown',left=20,top=16,textStyle=dict(color='#d7e3f4',fontSize=18)),series=[dict(type='custom',coordinateSystem='geo',renderItem=render,data=data,encode=dict(lng=0,lat=1),universalTransition=True,z=5)]))
 return dict(baseOption=base,options=opts)
