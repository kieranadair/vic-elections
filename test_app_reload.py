"""Regression checks for updating a running Community Cloud process."""
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parent


class LiveUpdateChecks(unittest.TestCase):
    def test_old_cached_module_does_not_break_current_app(self):
        stale = types.ModuleType('charts')

        def original_animated_renderer(df, years, start, play, speed):
            raise AssertionError('App used the old animated renderer')

        stale.ternary_options = original_animated_renderer
        # This reproduces both logged errors: the old signature and no PARTY_COLORS.
        with patch.dict(sys.modules, {'charts': stale}):
            app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
            self.assertFalse(app.exception, [e.message for e in app.exception])
            self.assertEqual(len(app.subheader), 3)
            self.assertFalse(app.tabs)
            self.assertIs(sys.modules['charts'], stale)

    def test_same_session_loads_changed_chart_source_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ['app.py', 'charts.py']:
                shutil.copy2(ROOT / filename, root / filename)
            (root / 'data').mkdir()
            for filename in ['first_preferences.csv', 'election_context.json']:
                shutil.copy2(ROOT / 'data' / filename, root / 'data' / filename)
            app = AppTest.from_file(str(root / 'app.py'), default_timeout=30).run()
            self.assertFalse(app.exception)
            # Simulate a deploy while this AppTest session and its data cache stay warm.
            with (root / 'charts.py').open('a') as source:
                source.write("\nWINNER_COLORS['Labor'] = '#010203'\n")
            path = root / 'data' / 'first_preferences.csv'
            data = pd.read_csv(path)
            row = (data.election_year == 2022) & (data.electorate == 'Northcote')
            data.loc[row, 'other_pct'] = 42.0
            data.to_csv(path, index=False)
            app.run()
            self.assertFalse(app.exception, [e.message for e in app.exception])
            self.assertTrue(any('#010203' in item.value for item in app.markdown))
            charts = app.get('component_instance')
            self.assertEqual(len(charts), 12)
            import json
            option = json.loads(charts[-1].proto.json_args)['options']
            northcote = next(point for series in option['series'][1:] for point in series['data'] if point['name'] == 'Northcote')
            self.assertEqual(northcote['value'][4], 42.0)


if __name__ == '__main__':
    unittest.main()
