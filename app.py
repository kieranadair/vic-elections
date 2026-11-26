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
                include = st.checkbox("Include flagged historical vote totals", value=True, key="include_flagged")
                st.caption("19 historical tables have candidate sums that differ from published formal totals. Shares use the candidate sum; an asterisk on hover flags these seats. This control filters the circles, while statewide bars and trends retain all recorded votes.")

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

        with st.container(width=1100):
            st.caption("The circles show seats, not a panel of the same voters. Boundaries, candidates and turnout change between elections, so a changing pattern can reflect both voter preferences and the choices available. The Minor Parties / Independents group brings together candidates with different political outlooks; it is not a single movement. Figures cover Legislative Assembly general elections, with the January 2023 Narracan supplementary poll included in 2022.")

        st.divider()
        st.header("Explore Your Electorate")
        explanation, trend = st.columns([1, 3], gap="large")
        with explanation:
            st.markdown("The statewide story brings together many local contests. Has support for minor parties and independents grown in your electorate, or have the major parties held their ground?")
            highlight = st.selectbox("Highlight an electorate", sorted(first.electorate.unique().tolist()), index=None, placeholder="All Victoria · choose an electorate", key="highlight_electorate")
            st.markdown("Choose a seat to follow its three first-preference shares through time. Its dot and reference lines will also appear in the triangles above, letting you place the local story within the wider pattern. Clear your selection to return to Victoria overall.")
        with trend:
            st.markdown(f"**{highlight or 'Victoria overall'} · first-preference vote, 1982–2022**")
            st.echarts_chart(charts.primary_trend_options(first,highlight),height=380,theme=None,key="primary_trend",alt=f"First-preference vote shares for {highlight or 'Victoria overall'} across elections from 1982 to 2022. Labor, Liberal–National and minor parties and independents are shown separately.")
            if highlight:
                st.caption("● Filled circle: the group that won this seat after preferences. ○ Hollow circle: the other groups. Every circle marks an election; the winning group need not lead on first preferences.")
            else:
                st.caption("Each hollow circle marks an election. Statewide shares combine vote counts from all electorates; they are not an average of seat percentages. Select an electorate to see its winners marked with filled circles.")
        with st.container(width=1100):
            st.caption("Electorates are matched by name. A gap means no result is recorded under that name for that election; lines do not bridge missing results. Boundaries can change even when a name stays the same, so these are histories of named seats rather than a fixed set of voters.")
