from pathlib import Path
from types import ModuleType
from typing import Any
import json

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Victorian Elections · 1982–2022", page_icon=":material/how_to_vote:", layout="wide")

# Read current trusted source on each run: Community Cloud can retain imported
# helpers across deploys. An isolated module avoids stale code and shared reloads.
chart_path = Path(__file__).with_name("charts.py")
charts: Any = ModuleType("_vic_elections_charts")
charts.__file__ = str(chart_path)
exec(compile(chart_path.read_bytes(), str(chart_path), "exec"), charts.__dict__)
DATA = Path(__file__).parent / "data"


@st.cache_data
def load(file_versions):
    return pd.read_csv(DATA / "first_preferences.csv"), json.loads((DATA / "election_context.json").read_text())


file_versions = tuple(
    (str(path), path.stat().st_mtime_ns, path.stat().st_size)
    for path in (DATA / "first_preferences.csv", DATA / "election_context.json")
)
first, chapters = load(file_versions)
# The selector is deliberately last on the page. Its persisted value is available
# before rendering the gallery, so one selection updates every historical chart.
highlight = st.session_state.get("highlight_electorate")

with st.container(horizontal=True, horizontal_alignment="center"):
    with st.container(width=1600, gap="medium"):
        with st.container(gap="xsmall"):
            with st.container(width=960):
                st.title("The Rise of Minor Parties and Independents in Victorian Elections")
            with st.container(width=1100):
                st.markdown("For much of the 1980s, Victoria’s lower-house elections were contests between two big party blocs. Over the next four decades, more voters gave their first choice to the Greens, other minor parties or independent candidates. These charts follow that widening field, seat by seat—and show why growing first-choice support does not always mean more seats in Parliament.")

        with st.container(gap="xxsmall"):
            st.caption("Party legend")
            st.markdown(" &nbsp; &nbsp; ".join(f'<span style="color:{charts.WINNER_COLORS[group]}">●</span> {group}' for group in ['Labor', charts.MINOR_LABEL, 'Liberal–National']), unsafe_allow_html=True)

        with st.expander("Reading the charts", icon=":material/info:", key="reading_guide", on_change="rerun") as guide:
            ternary_guide, bar_guide = st.columns([1, 1], gap="large")
            with ternary_guide:
                st.markdown("**The triangle: first choices, seat by seat**")
                with st.container(width=650):
                    st.markdown("**Each election is represented using a ternary chart, this is a chart that shows three shares that add to 100%.** Here, the corners represent Labor, Liberal–National, and Minor Parties / Independents. Each circle is a seat, positioned using its first-preference vote shares.")
                    st.markdown("Moving closer to a corner means a larger share for that group. The bottom edge represents no minor-party or independent votes; moving upward means a larger combined share for those candidates. The centre represents an equal three-way split.")
                    st.markdown("The shaded regions show which group leads on first preferences. **Circle colour shows the winning group after preferences**, which can differ. Hover for the seat name and whole-percentage shares; the unlabelled edge ticks mark 20, 40, 60 and 80%.")
                    if guide.open:
                        st_echarts(charts.example_options(),height=f"{charts.EXAMPLE_HEIGHT}px",key="ternary-example")
                    st.caption("Dummy data: Labor 40%, Liberal–National 35%, Minor Parties / Independents 25%. The reference lines meet each edge at that share.")
            with bar_guide:
                st.markdown("**The bars: votes and representation**")
                st.markdown("Two horizontal **100% stacked bars** sit beneath each triangle. The top bar shows each group’s share of seats won after preferences; the bottom bar shows its share of first-preference votes across Victoria. Each full bar represents 100%, so the coloured lengths show how the total is divided.")
                st.markdown("The colours match the circles: Labor is red, Liberal–National blue, and Minor Parties / Independents dark grey. In both bars, Labor starts at the left, Minor Parties / Independents sit in the middle, and Liberal–National ends at the right. The thin vertical reference line marks **50%** of the total.")
                st.markdown("Compare the two bars to see how votes translate into representation. A group can attract a substantial share of first choices yet win few seats when its support is spread widely. A longer segment in the seats bar than in the votes bar shows a larger share of seats than of primary votes. Vote shares use summed vote counts, rather than an average of seat percentages; both bars always include every recorded seat.")
                if guide.open:
                    with st.container(width=600):
                        st.echarts_chart(charts.bar_legend_options(),height=110,theme=None,key="summary_key",alt="Dummy example: seats are Labor 55%, minor parties and independents 15%, Liberal–National 30%; votes are 40%, 20%, 40%. A vertical line marks 50%.")
                st.caption("Dummy data: Labor has 40% of votes but 55% of seats; Minor Parties / Independents have 20% of votes and 15% of seats; Liberal–National has 40% of votes and 30% of seats.")
                include = st.checkbox("Include flagged historical vote totals", value=True, key="include_flagged", help="Filter flagged seat circles. Statewide bars and the trend chart retain all recorded votes; see the data note at the bottom.")

        visible = first if include else first[first.reconciles]
        for chapter in chapters:
            # Equal-width context + chart columns preserve the previous chart size.
            description, *plots = st.columns([1, 1, 1, 1], gap="xsmall")
            with description:
                with st.container(gap="xsmall"):
                    st.subheader(chapter["title"])
                    st.markdown(chapter["text"])
            for plot, year in zip(plots, chapter["years"]):
                with plot:
                    st_echarts(charts.ternary_options(visible, year, highlight=highlight, summary_df=first), height=f"{charts.CHART_HEIGHT}px", key=f"ternary-{year}")

        # The grid shares the gallery's four tracks and gaps, so the explorer
        # starts exactly at the first chart column and spans the remaining three.
        explorer = st.grid(4, min_column_width=200, gap="xsmall", key="electorate_explorer")
        with explorer.cell():
            with st.container(gap="xsmall", key="electorate_explorer_context"):
                st.subheader("Explore Your Electorate")
                highlight = st.selectbox("Highlight an electorate", sorted(first.electorate.unique().tolist()), index=None, placeholder="All Victoria · choose an electorate", key="highlight_electorate")
                st.markdown("See how the wider trend has played out locally. Choose a seat to update the line chart and its reference lines above; clear it to return to Victoria overall.")
                if highlight:
                    st.caption("● Filled: elected group after preferences. ○ Hollow: other groups. Each circle marks an election.")
                else:
                    st.caption("Each circle marks an election. Choose a seat to see its winning group marked with a filled circle.")
        with explorer.cell(column_span=3):
            st.echarts_chart(charts.primary_trend_options(first,highlight),height=charts.CHART_HEIGHT,theme=None,key="primary_trend",alt=f"First-preference vote shares for {highlight or 'Victoria overall'} across elections from 1982 to 2022. Labor, Liberal–National and minor parties and independents are shown separately.")

        st.caption("**Data notes.** Legislative Assembly general elections, 1982–2022; 2022 includes Narracan’s January 2023 supplementary poll. Statewide vote shares use summed recorded candidate votes, rather than an average of seat percentages. In 19 historical tables, candidate sums differ from published formal totals: shares use the candidate sum, and an asterisk on hover flags the seat. The guide’s checkbox filters circles only; statewide bars and trends retain all recorded votes. Electorates are matched by name, with gaps for missing years. Boundaries, candidates and turnout change, so the charts do not follow a fixed group of voters. Minor Parties / Independents combines candidates with different political outlooks.")
