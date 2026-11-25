# Victoria · Electoral currents

Streamlit + Apache ECharts exploration of Victorian Legislative Assembly elections, 1982–2022.

## Run

Python 3.12 recommended.

```sh
cd vic-elections
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Use the chart timeline to choose an election or play through the series. `Start year` sets the initial timeline position. To animate the full series, choose 1982. Each chart has independent timeline controls. The table year is selected independently.

## Views

- **Ternary:** first-preference shares, aggregated to Labor / Liberal and National Coalition / Other. Dot colour shows the largest bloc. The alternate three-candidate stage is available for 2022.
- **Windsock:** choose Labor–Coalition 2PP or actual final-two 2CP, focus group, margin definition, map zoom and length scale. 45 degrees up-right means focus wins; 135 degrees up-left means opposition wins. Length defaults to the vote-share lead (focus minus opponent); the optional swing-to-tie measure is half the lead. Zero is a tie and has zero length.
- **Data:** inspect source links, coverage and CSV exports.

## Geography

The app deliberately uses **fixed 2022 boundaries and geometric centroids in every election**, as requested. Historical seats match by name only. An abolished/renamed seat absent from the 2022 map is omitted; a new 2022 seat appears when its name first occurs. No historical boundary reconstruction or successor-seat matching is implied. Centroids use longitude/latitude polygon geometry; they are not population centres and can lie outside irregular polygons. Zoom into Melbourne to inspect crowded seats. Geometric shapes are simplified for display.

Files: https://github.com/jwood74/geographic_boundaries/tree/main/au/sed/sed_vic
The original 2021 redistribution geometry is the boundary set used in 2022; upstream links identify the Electoral Boundaries Commission as the source. Attribution remains with the original data owners. The 2014 boundary file is retained as source material but is not used by the app.

## Data and limits

- 1,049 seat-election rows, 12 elections, 1982–2022.
- First preferences: historical Wikipedia tables, citing electoral reports; official VEC 2022 distributions supersede all 2022 primary figures. Exact sources are recorded on rows.
- **19 historical primary tables fail candidate-sum versus published-formal-total reconciliation.** Their shares use the candidate sum and are flagged in tooltips and exports. Include/exclude them with the sidebar checkbox. This retains provisional historical coverage without representing those raw counts as verified.
- All 88 seats have three-candidate and two-candidate progressive totals for 2022, including later indicative statistical counts and Narracan's supplementary election. There is **no historical intermediate-count coverage before 2022** yet.
- The actual last three candidates can include two candidates from the same bloc. This is not a synthetic three-bloc recount; such a recount cannot generally be inferred from aggregate exclusion-round totals.
- 2PP = Labor versus Coalition. 2CP = the actual final pair. Actual 2022 final-two figures are official full-distribution totals. Other historical final figures and alternate 2022 2PP are secondary-source published counts and are not all independently verified against original reports.
- Missing published 2PP in the compiled tables: Preston 1982, Mildura 1988, Richmond 2018, Narracan 2022. Missing values stay missing. Narracan had no Labor candidate in its January 2023 supplementary election.
- A focus group absent from the actual final pair has no final 2CP margin; the app omits its windsock rather than assigning a fictional margin.
- No 2026 result is included; the general election had not occurred at compilation (25 November 2026).

Official results: https://www.vec.vic.gov.au/results/state-election-results

Full distributions: https://www.vec.vic.gov.au/results/electoral-statistics/state-election-statistics/full-preference-distributions

## Tables and reproducibility

`victoria_chart_inputs.xlsx` and `data/chart_inputs.csv` combine first preferences, last-three totals where available, final counts, map centroids and source links. Individual data files are also supplied. Unavailable fields are blank, never filled with first preferences or estimated transfers.

`prepare_data.py` is an optional source-rebuild helper. It uses the included `research/` source directory and additionally requires the packages in `requirements-dev.txt`. App runtime does not need these or an external service.

## Validation

```sh
python -m unittest discover -p 'test_charts.py'
```

Checks cover ternary vertices and sums, final margins, absent focus groups, and conservation through all 88 2022 distributions. Streamlit AppTest checks page execution and switching count stages and focus groups. ECharts JavaScript callbacks were syntax-checked with Node. The app was run internally in Chromium. Ternary and windsock rendering, switching chart tabs, Melbourne zoom, and selecting 1982 were checked with screenshots. A hidden-tab chart initialisation bug was fixed. Screenshots are included in `screenshots/`; continuous playback has not been separately timed.

Deploy on a Python-capable service (for example Streamlit Community Cloud), with `app.py` as the entry point. This is a runnable source delivery, not a hosted deployment; static/Cloudflare Worker hosting does not run a Streamlit Python server.
