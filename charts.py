"""ECharts option builders. Geometry and vote calculations are testable in Python."""
import math
from typing import Any
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
var side = Math.min(api.getWidth() - 48, (api.getHeight() - 164) / height);
var left = (api.getWidth() - side) / 2;
var top = 74;
var bottom = top + side * height;
function point(x, y) { return [left + side * x, bottom - side * y]; }
"""

MINOR_LABEL = 'Minor Parties / Independents'
CHART_HEIGHT = 380
EXAMPLE_HEIGHT = 330
WINNER_COLORS = {'Labor': '#cc4359', 'Liberal–National': '#377db8', MINOR_LABEL: '#50555a'}
WINNER_KEYS = {'Labor': 'Labor', 'Liberal–National': 'Coalition', MINOR_LABEL: 'Other'}


def chart_title(text):
    """Shared header treatment for the historical charts and vote trend."""
    return dict(text=text,left='center',top=4,padding=0,textStyle=dict(color='#252b33',fontSize=22,fontWeight=500,fontFamily='Georgia, serif'))


def election_summary(df, year):
    """Statewide seat shares and vote-weighted first preferences, in legend order."""
    seats = df[df.election_year == year]
    total_seats = len(seats)
    counts = [int((seats.winner_group == key).sum()) for key in WINNER_KEYS.values()]
    votes = [int(seats[key + '_votes'].sum()) for key in ['labor', 'coalition', 'other']]
    total_votes = sum(votes)
    return {
        'seat_shares': [100 * count / total_seats if total_seats else 0 for count in counts],
        'vote_shares': [100 * count / total_votes if total_votes else 0 for count in votes],
    }


def ternary_options(df, year, highlight=None, summary_df=None, show_summary=True):
    """First-choice positions, winner colours, optional persistent seat guides."""
    background = JsCode("""function(params, api) {
    GEOMETRY
    var h = Math.sqrt(3) / 2;
    var L=point(0,0),C=point(1,0),O=point(.5,h);
    var LC=point(.5,0),LO=point(.25,h/2),CO=point(.75,h/2),centre=point(.5,h/3);
    function region(points,color,x,y,x2,y2) {
      return {type:'polygon',shape:{points:points},style:{fill:{type:'linear',x:x,y:y,x2:x2,y2:y2,
      colorStops:[{offset:0,color:color},{offset:1,color:'#fafafa'}],global:false}}};
    }
    function line(a,b,color,width) {return {type:'line',shape:{x1:a[0],y1:a[1],x2:b[0],y2:b[1]},style:{stroke:color||'#c7cbd0',lineWidth:width||.8}};}
    function text(x,y,label,color,align) {return {type:'text',style:{x:x,y:y,text:label,fill:color,font:'12px sans-serif',align:align,verticalAlign:'middle'}};}
    var children=[region([L,LC,centre,LO],'#efb0ba',0,1,1,0),region([C,CO,centre,LC],'#a9c4e7',1,1,0,0),region([O,LO,centre,CO],'#c2c5c9',.5,0,.5,1),
      {type:'polygon',name:'triangle-outline',shape:{points:[L,C,O]},style:{fill:'none',stroke:'#bec3ca',lineWidth:.8}}];
    [.2,.4,.6,.8].forEach(function(v) {
      children.push(line(point(1-v,0),point((1-v)/2,h*(1-v)),'#cbd0d6',.6),line(point(v,0),point((1+v)/2,h*(1-v)),'#cbd0d6',.6),line(point(v/2,h*v),point(1-v/2,h*v),'#cbd0d6',.6));
      var labor=point(1-v,0),coalition=point((1+v)/2,h*(1-v)),other=point(v/2,h*v);
      [[labor,[0,4]],[coalition,[3.46,-2]],[other,[-3.46,-2]]].forEach(function(tick) {
        var a=tick[0],offset=tick[1],mark=line(a,[a[0]+offset[0],a[1]+offset[1]],'#8c949f',.8);mark.name='axis-tick';children.push(mark);
      });
    });
    children.push(line(LC,centre),line(LO,centre),line(CO,centre),text(O[0],O[1]-23,'Minor Parties / Independents','#51565e','center'),text(L[0],L[1]+28,'Labor','#bd344e','left'),text(C[0],C[1]+28,'Liberal–National','#2b68af','right'));
    return {type:'group',children:children};
    }""".replace('GEOMETRY', TERNARY_GEOMETRY_JS).replace('\n', ' ')).js_code
    render = JsCode("""function(params, api) {
    GEOMETRY
    var p=point(api.value(0),api.value(1)),selected=!!api.value(9),tracking=!!api.value(10),r=selected?4.4:2.8;
    var normal=selected?1:0,hover=(!tracking||selected)?1:0;
    var labor=api.value(2)/100,coalition=api.value(3)/100,other=api.value(4)/100;
    var ends=[point(1-labor,0),point((1+coalition)/2,height*(1-coalition)),point(other/2,height*other)],color=api.visual('color');
    function guide(end,axis) {return {type:'line',name:axis+'-reference',silent:true,shape:{x1:p[0],y1:p[1],x2:end[0],y2:end[1]},style:{stroke:'#626c79',lineWidth:1,opacity:normal},emphasis:{style:{opacity:hover}},z2:selected?40:20};}
    function label(x,y,txt,align,name) {return {type:'text',name:name,silent:true,style:{x:x,y:y,text:txt,fill:'#303b49',font:'11px sans-serif',align:align,verticalAlign:'middle',backgroundColor:'rgba(255,255,255,.95)',padding:[2,3],borderRadius:2,opacity:normal},emphasis:{style:{opacity:hover}},z2:selected?60:30};}
    var right=ends[1],leftEnd=ends[2];
    return {type:'group',children:[
      {type:'circle',name:api.value(6),shape:{cx:p[0],cy:p[1],r:r},style:{fill:color,opacity:.8,stroke:selected?'#26313b':'none',lineWidth:selected?2:0},emphasis:{style:{fill:color,opacity:.8,stroke:'#344051',lineWidth:1}},z2:selected?50:10},
      guide(ends[0],'labor'),guide(ends[1],'coalition'),guide(ends[2],'other'),
      label(Math.max(62,Math.min(api.getWidth()-62,ends[0][0])),bottom+16,'Labor '+api.value(2).toFixed(0)+'%','center','labor-result'),
      label(right[0]+(right[0]<api.getWidth()-130?8:-8),right[1],'Liberal–National '+api.value(3).toFixed(0)+'%',right[0]<api.getWidth()-130?'left':'right','coalition-result'),
      label(Math.max(100,Math.min(api.getWidth()-100,leftEnd[0])),leftEnd[1]+16,'Minor Parties / Independents\\n'+api.value(4).toFixed(0)+'%','center','other-result'),
      label(Math.max(100,Math.min(api.getWidth()-100,p[0])),p[1]-16,api.value(6)+(api.value(5)?' *':''),'center','seat-name')
    ]};
    }""".replace('GEOMETRY', TERNARY_GEOMETRY_JS).replace('\n', ' ')).js_code
    series = [dict(type='custom',name='Dominance regions',coordinateSystem='none',renderItem=background,data=[0],silent=True,z=0,tooltip=dict(show=False))]
    sub = df[df.election_year == year]
    for group, color in WINNER_COLORS.items():
        data = []
        for _, row in sub[sub.winner_group == WINNER_KEYS[group]].iterrows():
            values = [float(row[key + '_pct']) for key in ['labor', 'coalition', 'other']]
            x, y = ternary_xy(*values)
            quality = 'Source totals differ; shares normalised to candidate sum' if not bool(row.get('reconciles', True)) else ''
            data.append(dict(name=row.electorate,value=[x,y,*values,quality,row.electorate,row.winner_party,row.winner,int(row.electorate==highlight),int(bool(highlight))]))
        series.append(dict(type='custom',name=group,coordinateSystem='none',renderItem=render,data=data,itemStyle=dict(color=color),emphasis=dict(focus='none'),z=3))
    if show_summary:
        summary = election_summary(df if summary_df is None else summary_df, year)
        for index, (name, shares) in enumerate([('Seats won', summary['seat_shares']), ('First-preference vote', summary['vote_shares'])]):
            bar = JsCode("""function(params,api) {
            GEOMETRY
            var y=api.getHeight()-32+ROW*14,offset=0,colors=PALETTE,children=[],order=[0,2,1];
            for(var j=0;j<3;j++){var i=order[j],width=side*api.value(i)/100;children.push({type:'rect',name:'segment-'+i,shape:{x:left+offset,y:y,width:width,height:8},style:{fill:colors[i]}});offset+=width;}
            if(ROW===0)children.push({type:'line',name:'fifty-percent-reference',shape:{x1:left+side/2,y1:api.getHeight()-35,x2:left+side/2,y2:api.getHeight()-7},style:{stroke:'#17191c',lineWidth:1.2},silent:true,z2:10});
            return {type:'group',children:children};
            }""".replace('GEOMETRY',TERNARY_GEOMETRY_JS).replace('ROW',str(index)).replace('PALETTE',repr(list(WINNER_COLORS.values()))).replace('\n',' ')).js_code
            series.append(dict(type='custom',name=name,coordinateSystem='none',renderItem=bar,data=[shares],silent=True,z=1,tooltip=dict(show=False)))
    options = dict(backgroundColor='#ffffff',animation=False,title=chart_title(str(year)),tooltip=dict(show=False),series=series)
    if highlight and not (sub.electorate == highlight).any():
        options['graphic'] = [dict(type='text',left='center',top=330,style=dict(text='No displayed result under this name',fill='#68727e',font='10px sans-serif'))]
    return options


def bar_legend_options():
    """Native ECharts key: illustrative, normalised rows using the chart bar order."""
    import pandas as pd
    data = pd.DataFrame({'Measure': ['% seats', '% votes'], 'Labor': [55, 40], MINOR_LABEL: [15, 20], 'Liberal–National': [30, 40]})
    series = []
    for group in ['Labor', MINOR_LABEL, 'Liberal–National']:
        bar: dict[str, Any] = dict(type='bar',name=group,stack='total',barWidth=8,encode=dict(x=group,y='Measure'),itemStyle=dict(color=WINNER_COLORS[group]),silent=True)
        if not series:
            bar['markLine'] = dict(silent=True,symbol='none',lineStyle=dict(color='#17191c',width=1.2,type='solid'),label=dict(show=True,formatter='50%',position='start',color='#51565e',fontSize=10),data=[dict(xAxis=50)])
        series.append(bar)
    return dict(animation=False,backgroundColor='#ffffff',dataset=dict(source=data),grid=dict(left=65,right=8,top=20,bottom=4),xAxis=dict(type='value',min=0,max=100,show=False),yAxis=dict(type='category',inverse=True,axisTick=dict(show=False),axisLine=dict(show=False),axisLabel=dict(fontSize=12,color='#26313b')),tooltip=dict(show=False),series=series)


def primary_trend_data(df, electorate=None):
    """Vote-weighted statewide shares, or a named seat with genuine data gaps."""
    import pandas as pd
    records = []
    for year in sorted(df.election_year.unique()):
        seats = df[df.election_year == year]
        if electorate:
            seats = seats[seats.electorate == electorate]
        record = {'Year': int(year), 'Election date': pd.Timestamp(year=int(year),month=1,day=1)}
        if electorate and not seats.empty:
            seat = seats.iloc[0]
            shares = [float(seat[key + '_pct']) for key in ['labor', 'coalition', 'other']]
            winner = seat.winner_group
            record['Outcome'] = 'Elected: ' + seat.winner_party
        elif not electorate:
            shares = election_summary(df, year)['vote_shares']
            winner = None
            record['Outcome'] = 'Statewide first-preference votes'
        else:
            shares = [None, None, None]
            winner = None
            record['Outcome'] = 'No result under this electorate name'
        for (group, key), share in zip(WINNER_KEYS.items(), shares):
            record[group] = share
            record[group + ' label'] = f'{share:.0f}%' if share is not None else '—'
            record[group + ' winner'] = share if winner == key else None
        records.append(record)
    return pd.DataFrame(records)


def primary_trend_options(df, electorate=None):
    """Three vote-share lines; equal-sized filled markers encode seat winners."""
    series = []
    for group, color in WINNER_COLORS.items():
        series.append(dict(
            type='line',name=group,encode=dict(x='Election date',y=group),
            showSymbol=True,symbol='circle',symbolSize=8,connectNulls=False,
            lineStyle=dict(color=color,width=2.4),
            itemStyle=dict(color='#ffffff',borderColor=color,borderWidth=2),
            endLabel=dict(show=False),emphasis=dict(focus='none',scale=False),z=3,
        ))
        if electorate:
            series.append(dict(
                type='scatter',name=group+' · elected',
                encode=dict(x='Election date',y=group+' winner'),symbol='circle',symbolSize=8,
                itemStyle=dict(color=color,borderColor=color,borderWidth=2,opacity=1),
                silent=True,tooltip=dict(show=False),z=4,
            ))
    tooltip = '<strong>{@Year}</strong><br/>Labor: {@Labor label}<br/>Liberal–National: {@Liberal–National label}<br/>Minor Parties / Independents: {@Minor Parties / Independents label}<br/>{@Outcome}'
    # Match the outer triangles, including the y-axis labels in the left inset.
    # Three chart tracks contain two 8px gaps. Native media rules approximate
    # their responsive inset to within half a pixel across the bounded page.
    triangle_side = (CHART_HEIGHT - 164) / (math.sqrt(3) / 2)
    media = []
    for width in range(908, 1214, 6):
        inset = max(24, (width + 3 - 16) / 6 - triangle_side / 2)
        media.append(dict(query=dict(minWidth=width,maxWidth=width+6),option=dict(grid=dict(left=inset,right=inset))))
    # ECharts needs a default media option to reset padding after narrowing.
    media.append(dict(option=dict(grid=dict(left=24,right=24))))
    return dict(
        animation=False,backgroundColor='#ffffff',textStyle=dict(fontFamily='Inter, sans-serif'),
        title=chart_title(f'{electorate or "Victoria overall"} · first-preference vote, 1982–2022'),
        dataset=dict(source=primary_trend_data(df,electorate)),
        grid=dict(left=24,right=24,top=52,bottom=24,containLabel=True),media=media,
        xAxis=dict(type='time',min='1982-01-01',max='2022-01-01',splitNumber=8,axisLabel=dict(formatter='{yyyy}',color='#51565e',showMinLabel=True,showMaxLabel=True,hideOverlap=True),axisLine=dict(lineStyle=dict(color='#c7cbd0')),axisTick=dict(show=False),splitLine=dict(show=False)),
        yAxis=dict(type='value',min=0,max=100,interval=20,axisLabel=dict(formatter='{value}%',color='#51565e'),axisLine=dict(show=False),axisTick=dict(show=False),splitLine=dict(lineStyle=dict(color='#e9ecef'))),
        tooltip=dict(trigger='axis',confine=True,formatter=tooltip,axisPointer=dict(type='line',lineStyle=dict(color='#aeb5bd',type='dashed'))),
        series=series,
    )


def example_options():
    """Clearly fictional, permanently annotated 40/35/25 example for the guide."""
    import pandas as pd
    dummy = pd.DataFrame([dict(election_year=0,electorate='Example seat',labor_pct=40.,coalition_pct=35.,other_pct=25.,winner_group='Labor',winner_party='Labor',winner='Illustration',reconciles=True)])
    options = ternary_options(dummy,0,highlight='Example seat',show_summary=False)
    options['title']['text'] = 'Illustrative example'
    options['title']['textStyle']['fontSize'] = 15
    return options

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
