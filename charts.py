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
# Shared pixel transform keeps x/y scales identical at every component size.
TERNARY_GEOMETRY_JS = """
var height = Math.sqrt(3) / 2;
var side = Math.min(api.getWidth() - 70, (api.getHeight() - 120) / height);
var left = (api.getWidth() - side) / 2;
var top = 72;
var bottom = top + side * height;
function point(x, y) { return [left + side * x, bottom - side * y]; }
"""

def ternary_options(df, year):
 """One static, equilateral first-preference triangle for a single election."""
 background = JsCode("""function(params, api) {
 GEOMETRY
 var h = Math.sqrt(3) / 2;
 var L = point(0, 0), C = point(1, 0), O = point(.5, h);
 var LC = point(.5, 0), LO = point(.25, h/2), CO = point(.75, h/2);
 var centre = point(.5, h/3);
 function region(points, color, x, y, x2, y2) {
  return {type:'polygon',shape:{points:points},style:{fill:{
   type:'linear',x:x,y:y,x2:x2,y2:y2,
   colorStops:[{offset:0,color:color},{offset:1,color:'#fafafa'}],global:false
  }}};
 }
 function line(a,b) { return {type:'line',shape:{x1:a[0],y1:a[1],x2:b[0],y2:b[1]},style:{stroke:'#c7cbd0',lineWidth:.8}}; }
 function text(x,y,label,color,align) { return {type:'text',style:{x:x,y:y,text:label,fill:color,font:'12px sans-serif',align:align,verticalAlign:'middle'}}; }
 return {type:'group',children:[
  region([L, LC, centre, LO], '#ef8d9c', 0,1,1,0),
  region([C, CO, centre, LC], '#80a8de', 1,1,0,0),
  region([O, LO, centre, CO], '#a9a9a9', .5,0,.5,1),
  {type:'polygon',shape:{points:[L,C,O]},style:{fill:'none',stroke:'#d9dce0',lineWidth:.8}},
  line(LC,centre),line(LO,centre),line(CO,centre),
  text(O[0],O[1]-23,'100% Other','#51565e','center'),
  text(L[0],L[1]+22,'100% Labor','#bd344e','left'),
  text(C[0],C[1]+22,'100% Coalition','#2b68af','right')
 ]};
}""".replace('GEOMETRY', TERNARY_GEOMETRY_JS).replace('\n', ' ')).js_code
 render = JsCode("""function(params, api) {
 GEOMETRY
 var p = point(api.value(0), api.value(1));
 var group = api.value(7), r = 3.4;
 var style = api.style({opacity:.78});
 if (group === 'Coalition') return {type:'rect',shape:{x:p[0]-r,y:p[1]-r,width:2*r,height:2*r},style:style};
 if (group === 'Other') return {type:'polygon',shape:{points:[[p[0],p[1]-r-1],[p[0]+r+1,p[1]],[p[0],p[1]+r+1],[p[0]-r-1,p[1]]]},style:style};
 return {type:'circle',shape:{cx:p[0],cy:p[1],r:r},style:style};
}""".replace('GEOMETRY', TERNARY_GEOMETRY_JS).replace('\n', ' ')).js_code
 tip=JsCode("""function(p){var v=p.value;return v[6]+'<br>Labor '+v[2].toFixed(2)+'%<br>Coalition '+v[3].toFixed(2)+'%<br>Other '+v[4].toFixed(2)+'%'+(v[5]?'<br>'+v[5]:'');}""").js_code
 series=[dict(type='custom',name='Dominance regions',coordinateSystem='none',renderItem=background,data=[0],silent=True,z=0,tooltip=dict(show=False))]
 sub=df[df.election_year==year]
 for g in GROUPS:
  data=[]
  for _,r in sub.iterrows():
   vals=[float(r[x+'_pct']) for x in ['labor','coalition','other']]
   if GROUPS[max(range(3),key=lambda j:vals[j])]!=g:continue
   x,y=ternary_xy(*vals)
   quality='Source totals differ; shares normalised to candidate sum' if not bool(r.get('reconciles',True)) else ''
   data.append(dict(name=r.electorate,value=[x,y,*vals,quality,r.electorate,g]))
  series.append(dict(type='custom',name=g,coordinateSystem='none',renderItem=render,data=data,itemStyle=dict(color={'Labor':'#df526b','Coalition':'#397fc6','Other':'#858585'}[g]),z=3))
 return dict(backgroundColor='#ffffff',animation=False,title=dict(text=str(year),left=16,top=16,textStyle=dict(color='#252b33',fontSize=22,fontWeight=500)),tooltip=dict(trigger='item',formatter=tip,confine=True),series=series)

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
