from pathlib import Path
from types import ModuleType
from typing import Any
import json

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Victoria’s changing vote", page_icon=":material/how_to_vote:", layout="wide")

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
    with st.container(width=1440, gap="medium"):
        with st.container(gap="xsmall"):
            st.caption("VICTORIA  /  STATE ELECTIONS  /  1982–2022")
            st.title("Forty years of first choices")
            st.markdown("How has support shifted between **Labor**, **Liberal–National** and **Other**? Each circle is one seat. Its position shows first preferences; its colour shows who ultimately won.")

        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
            st.markdown(" &nbsp; &nbsp; ".join(f'<span style="color:{color}">●</span> {group}' for group, color in charts.WINNER_COLORS.items()), unsafe_allow_html=True)
            with st.popover("Reading the charts", icon=":material/info:"):
                st.markdown("Closer to a corner means a larger first-preference share for that group. The shaded regions show which group has the most first preferences. **Hover a circle** for its seat name and reference lines to the three axes.")
                st.caption("Each edge has unlabelled ticks at 20, 40, 60 and 80%. Circles show the winning group after preferences, at 80% opacity.")
                include = st.checkbox("Include flagged historical vote totals", value=True, key="include_flagged")
                st.caption("19 historical tables have candidate sums that differ from published formal totals. Shares use the candidate sum; an asterisk on hover flags these seats.")

        visible = first if include else first[first.reconciles]
        for chapter in chapters:
            with st.container(gap="xsmall"):
                st.subheader(f"{chapter['years'][0]}–{chapter['years'][-1]} · {chapter['title']}")
                # Four across at laptop widths; progressively wrap on smaller screens.
                with st.grid(4, min_column_width=245, gap=12, width="stretch"):
                    for year in chapter["years"]:
                        st_echarts(charts.ternary_options(visible, year), height="320px", key=f"ternary-{year}")
                with st.container(width=1080, gap="xxsmall"):
                    st.markdown(chapter["text"])
                    st.caption("Sources: " + " · ".join(f"[{source['label']}]({source['url']})" for source in chapter["sources"]))

        st.caption("Legislative Assembly general elections. Other includes Greens, minor parties and independents. Seats and candidate choices change between elections; the charts do not track the same voters over time. 2022 includes the January 2023 Narracan supplementary poll.")
