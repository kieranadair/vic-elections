# The Rise of Minor Parties and Independents in Victorian Elections

An interactive Streamlit and Apache ECharts app exploring Victorian Legislative Assembly elections from 1982 to 2022.

[Open the app](https://vic-elections-9swp3uymychdeytcjpuyvj.streamlit.app/)

Each election has a ternary chart of seat-level first-preference shares for Labor, Liberal–National and Minor Parties / Independents. Circle colour identifies the winning group after preferences. Stacked bars compare statewide vote and seat shares. The electorate explorer links a primary-vote trend chart to highlights in the historical triangles.

## Run locally

Python 3.12 recommended.

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy on Streamlit Community Cloud

Connect this repository, select the `main` branch, and use `app.py` as the entry point. Dependencies are installed from `requirements.txt`. No API keys, external database or data-generation step is required.

## Application files

- `app.py`: page layout, controls and data loading.
- `charts.py`: ECharts options and vote-share calculations.
- `data/first_preferences.csv`: 1,049 seat-election records across 12 elections, including vote counts, shares, winners and source URLs.
- `data/election_context.json`: historical descriptions and their research references.
- `.streamlit/config.toml`: application configuration.
- `.streamlit/editorial-theme.toml`: fonts, colours and spacing.
- `requirements.txt`: deployment dependencies.

The app executes the current chart-helper source on each run to avoid stale imports after Community Cloud updates. Data-file versions are included in the cache key.

## Data notes

Historical primary figures come from electorate tables citing election reports; official VEC preference distributions supply the 2022 first preferences. Source URLs remain in the data. The 2022 figures include Narracan’s January 2023 supplementary election.

In 19 historical records, candidate sums differ from published formal totals. Shares use candidate sums, and hover annotations flag these seats. The reading guide can hide flagged dots; statewide bars and trends retain all recorded votes. Statewide vote shares are calculated from summed counts rather than averaged electorate percentages.

Electorates are matched by name, with gaps for missing years. Boundaries, candidates and turnout change, so the charts do not follow a fixed group of voters. Minor Parties / Independents combines candidates with different political outlooks.

Research downloads, preparation scripts, development tests and screenshots are excluded from the deployment repository. Earlier versions remain available in Git history.
