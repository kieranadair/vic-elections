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
