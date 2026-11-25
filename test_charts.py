import unittest
from pathlib import Path
import pandas as pd
from charts import ternary_xy,windsock_rows,ternary_options,map_options
D=Path(__file__).parent/'data'
class ChartChecks(unittest.TestCase):
 def test_corners(self):
  self.assertEqual(ternary_xy(100,0,0),(0,0));self.assertEqual(ternary_xy(0,100,0),(1,0));self.assertAlmostEqual(ternary_xy(0,0,100)[0],.5)
 def test_vote_shares(self):
  d=pd.read_csv(D/'first_preferences.csv');self.assertEqual(len(d),1049)
  self.assertTrue(((d.labor_pct+d.coalition_pct+d.other_pct-100).abs()<1e-6).all())
 def test_static_ternary_contract(self):
  d=pd.read_csv(D/'first_preferences.csv');options=ternary_options(d,2022)
  self.assertFalse(options['animation']);self.assertNotIn('timeline',options)
  self.assertEqual(sum(len(s['data']) for s in options['series'][1:]),88)
  # The component's JS callback decoder cannot read multiline functions.
  for series in options['series']:self.assertNotIn('\n',series['renderItem'])
 def test_screen_geometry_is_equilateral(self):
  import subprocess,shutil,json
  if not shutil.which('node'):self.skipTest('Node is needed to execute the chart renderer')
  options=ternary_options(pd.read_csv(D/'first_preferences.csv'),2022)
  callback=options['series'][0]['renderItem'].replace('--x_x--0_0--','')
  script='const render=('+callback+');'+"""
  for (const width of [320,420,520,680]) {
   const scene=render({}, {getWidth:()=>width,getHeight:()=>460});
   const points=scene.children[3].shape.points;
   const sides=points.map((p,i)=>Math.hypot(p[0]-points[(i+1)%3][0],p[1]-points[(i+1)%3][1]));
   if(Math.max(...sides)-Math.min(...sides)>1e-8)throw Error('Triangle stretched at '+width);
   if(points.some(p=>p[0]<0||p[0]>width||p[1]<0||p[1]>460))throw Error('Triangle clipped');
  }
  """
  subprocess.run(['node','-e',script],check=True,capture_output=True,text=True)
 def test_colour_uses_elected_party_not_primary_leader(self):
  from charts import PARTY_COLORS
  d=pd.read_csv(D/'first_preferences.csv')
  # Labor beat the Greens after preferences despite Other leading primary votes.
  northcote=d.query('election_year==2022 and electorate=="Northcote"').iloc[0]
  self.assertGreater(northcote.other_pct,northcote.labor_pct)
  options=ternary_options(d,2022)
  labor=next(s for s in options['series'] if s['name']=='Labor')
  self.assertIn('Northcote',[p['name'] for p in labor['data']])
  # The 2014 Prahran winner was Greens, although Coalition led on primaries.
  options=ternary_options(d,2014)
  greens=next(s for s in options['series'] if s['name']=='Greens')
  self.assertIn('Prahran',[p['name'] for p in greens['data']])
  self.assertEqual(greens['itemStyle']['color'],PARTY_COLORS['Greens'])
 def test_hover_guides_and_axis_ticks(self):
  import subprocess,shutil,json
  if not shutil.which('node'):self.skipTest('Node is needed to execute the chart renderer')
  options=ternary_options(pd.read_csv(D/'first_preferences.csv'),2022)
  series=next(s for s in options['series'] if s['name']=='Labor')
  value=next(p['value'] for p in series['data'] if p['name']=='Northcote')
  render=series['renderItem'].replace('--x_x--0_0--','')
  background=options['series'][0]['renderItem'].replace('--x_x--0_0--','')
  script='const render=('+render+');const background=('+background+');const value='+json.dumps(value)+';'+"""
  function check(x,msg){if(!x)throw Error(msg);}
  for(const width of [320,520]) {
   const api={getWidth:()=>width,getHeight:()=>460,value:i=>value[i],visual:()=> '#d34a59'};
   const scene=render({},api), bg=background({},api);
   check(bg.children.filter(x=>x.name==='axis-tick').length===12,'Four ticks on every edge');
   const marks=scene.children.filter(x=>x.type==='circle');
   check(marks.length===1&&marks[0].style.opacity===.8,'One 80% opaque circle');
   const outline=bg.children.find(x=>x.name==='triangle-outline').shape.points;
   const L=outline[0],C=outline[1],O=outline[2],side=C[0]-L[0],height=L[1]-O[1];
   const refs=['labor','coalition','other'].map(axis=>scene.children.find(x=>x.name===axis+'-reference'));
   check(refs.every(x=>x.style.opacity===0&&x.emphasis.style.opacity===1),'Hover only references');
   const a=refs[0].shape,b=refs[1].shape,c=refs[2].shape;
   check(Math.abs(a.y2-L[1])<1e-8&&Math.abs(100*(1-(a.x2-L[0])/side)-value[2])<1e-8,'Labor projection');
   check(Math.abs((b.y2-L[1])+2*height*(1-(b.x2-L[0])/side))<1e-8,'Coalition on right edge');
   check(Math.abs(100*(2*(b.x2-L[0])/side-1)-value[3])<1e-8,'Coalition projection');
   check(Math.abs((c.x2-L[0])*2/side-(L[1]-c.y2)/height)<1e-8,'Other on left edge');
   check(Math.abs(100*(L[1]-c.y2)/height-value[4])<1e-8,'Other projection');
   const name=scene.children.find(x=>x.name==='seat-name');
   check(name.style.text==='Northcote'&&name.style.y<marks[0].shape.cy,'Seat name above circle');
   for(const [i,axis] of ['labor','coalition','other'].entries()){
    const label=scene.children.find(x=>x.name===axis+'-result');
    check(label.style.text.includes(value[i+2].toFixed(1)+'%'),'Share at reference end');
   }
  }
  """
  subprocess.run(['node','-e',script],check=True,capture_output=True,text=True)
 def test_margins_and_absent_focus(self):
  f=pd.read_csv(D/'final_counts.csv');c=pd.read_csv(D/'centroids.csv').query('boundary_year==2022').drop(columns='boundary_year')
  d=windsock_rows(f,c,'Labor','Labor–Coalition 2PP');r=d.query('election_year==2022 and electorate=="Albert Park"').iloc[0]
  self.assertAlmostEqual(r.signed_margin,2*(23916/39110*100)-100,places=3);self.assertEqual(r.angle,45)
  self.assertTrue(d.query('electorate=="Narracan" and election_year==2022').empty)
  x=windsock_rows(f,c,'Other','Actual final two (2CP)');self.assertTrue((x.tcp_other_votes>0).all())
 def test_round_conservation(self):
  d=pd.read_csv(D/'rounds_2022.csv');self.assertEqual(d.electorate.nunique(),88)
  self.assertTrue((d.groupby('electorate').total_votes.nunique()==1).all())
  self.assertEqual(len(d[d.candidates_remaining==3]),88)
  self.assertTrue((d.labor_votes+d.coalition_votes+d.other_votes==d.total_votes).all())
if __name__=='__main__':unittest.main()
