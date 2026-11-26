from pathlib import Path
from types import ModuleType
from typing import Any
import json

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Minor parties and independents · Victoria, 1982–2022", page_icon=":material/how_to_vote:", layout="wide")

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

with st.container(horizontal=True, horizontal_alignment="center"):
    with st.container(width=1600, gap="large"):
        with st.container(gap="xsmall"):
            st.title("The rise of minor parties and independents in Victorian elections")
            st.header("1982–2022")
            with st.container(width=1100):
                st.markdown("For much of the 1980s, Victoria’s lower-house elections were contests between two big party blocs. Over the next four decades, more voters gave their first choice to the Greens, other minor parties and independents. These charts follow that widening field, seat by seat—and show why growing first-choice support does not always mean more seats in Parliament.")

        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(" &nbsp; &nbsp; ".join(f'<span style="color:{color}">●</span> {group}' for group, color in charts.WINNER_COLORS.items()), unsafe_allow_html=True)
            with st.popover("Reading the charts", icon=":material/info:"):
                st.markdown("**A ternary chart shows three shares that add to 100%.** Here, the corners represent Labor, Liberal–National, and Minor parties and Independents. Each circle is a seat, positioned using its first-preference vote shares.")
                st.markdown("Moving closer to a corner means a larger share for that group. The bottom edge represents no minor-party or independent votes; moving upward means a larger combined share for those candidates. The centre represents an equal three-way split.")
                st.markdown("**Why use it?** A two-party chart hides votes outside the major blocs. A ternary chart makes those votes visible while preserving the balance between Labor and Liberal–National. Comparing the same triangle over time reveals both shifts between the majors and the widening field of first choices.")
                st.markdown("The shaded regions show which group leads on first preferences. **Circle colour shows the winning group after preferences**, which can differ. Hover for the seat name, reference lines and percentage shares; the unlabelled edge ticks mark 20, 40, 60 and 80%.")
                include = st.checkbox("Include flagged historical vote totals", value=True, key="include_flagged")
                st.caption("19 historical tables have candidate sums that differ from published formal totals. Shares use the candidate sum; an asterisk on hover flags these seats.")

        visible = first if include else first[first.reconciles]
        for chapter in chapters:
            # Equal-width context + chart columns preserve the previous chart size.
            description, *plots = st.columns([1, 1, 1, 1], gap="xsmall")
            with description:
                with st.container(gap="xsmall"):
                    st.caption(f"{chapter['years'][0]}–{chapter['years'][-1]}")
                    st.subheader(chapter["title"])
                    st.markdown(chapter["text"])
            for plot, year in zip(plots, chapter["years"]):
                with plot:
                    st_echarts(charts.ternary_options(visible, year), height="320px", key=f"ternary-{year}")

        with st.container(width=1100):
            st.caption("The circles show seats, not a panel of the same voters. Boundaries, candidates and turnout change between elections, so a changing pattern can reflect both voter preferences and the choices available. Minor parties and Independents combines candidates with different political outlooks; it is not a single movement. Figures cover Legislative Assembly general elections, with the January 2023 Narracan supplementary poll included in 2022.")
