"""Protect statewide weighting, local winners, and missing-seat years."""
from pathlib import Path
import unittest

import pandas as pd

from charts import MINOR_LABEL, WINNER_COLORS, primary_trend_data, primary_trend_options


class PrimaryTrendChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.votes = pd.read_csv(Path(__file__).parent / 'data/first_preferences.csv')

    def test_statewide_is_weighted_and_does_not_invent_an_electorate_winner(self):
        votes = pd.DataFrame([
            dict(election_year=2022,electorate='Small',labor_votes=90,coalition_votes=10,other_votes=0,winner_group='Labor'),
            dict(election_year=2022,electorate='Large',labor_votes=90,coalition_votes=810,other_votes=0,winner_group='Coalition'),
        ])
        trend = primary_trend_data(votes)
        self.assertEqual(trend.Labor.iloc[0], 18)
        self.assertTrue(trend['Labor winner'].isna().all())
        self.assertEqual(len(primary_trend_options(votes)['series']), 3)
        statewide = primary_trend_data(self.votes)
        self.assertEqual(len(statewide), 12)
        self.assertTrue(((statewide[list(WINNER_COLORS)].sum(axis=1) - 100).abs() < 1e-6).all())

    def test_fill_uses_elected_group_even_when_primary_votes_lead_elsewhere(self):
        trend = primary_trend_data(self.votes, 'Northcote').set_index('Year')
        self.assertGreater(trend.loc[2022, MINOR_LABEL], trend.loc[2022, 'Labor'])
        self.assertEqual(trend.loc[2022, 'Labor winner'], trend.loc[2022, 'Labor'])
        self.assertTrue(pd.isna(trend.loc[2022, MINOR_LABEL + ' winner']))
        self.assertEqual(trend.loc[2022, 'Outcome'], 'Elected: Labor')
        prahran = primary_trend_data(self.votes, 'Prahran').set_index('Year')
        self.assertEqual(prahran.loc[2014, 'Outcome'], 'Elected: Greens')
        self.assertEqual(prahran.loc[2014, MINOR_LABEL + ' winner'], prahran.loc[2014, MINOR_LABEL])
        options = primary_trend_options(self.votes, 'Northcote')
        for line, winner in zip(options['series'][::2], options['series'][1::2]):
            self.assertEqual(line['symbolSize'], winner['symbolSize'])
            self.assertEqual(line['lineStyle']['color'], winner['itemStyle']['color'])
            self.assertFalse(line['connectNulls'])

    def test_new_seat_has_gaps_and_no_fabricated_winners(self):
        trend = primary_trend_data(self.votes, 'Ashwood')
        absent = trend[trend.Year < 2022]
        self.assertTrue(absent[list(WINNER_COLORS)].isna().all().all())
        self.assertTrue(absent[[group+' winner' for group in WINNER_COLORS]].isna().all().all())
        self.assertEqual(trend.Year.tolist(), sorted(self.votes.election_year.unique()))
        self.assertEqual(trend.Labor.notna().sum(), 1)


if __name__ == '__main__':
    unittest.main()
