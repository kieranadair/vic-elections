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
