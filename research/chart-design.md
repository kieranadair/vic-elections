# Explorer line chart

The explorer uses three coloured lines for first-preference shares, with an
equal-sized circle at each election. The elected group for a selected seat has
a filled circle; the other groups have a white interior and coloured outline.
The fill distinction leaves party colours intact and does not imply that a
larger symbol represents a greater vote. Tooltips also name the actual winning
party, including Greens and Independent winners within the combined group.

This encoding is a design choice informed by these references, rather than a
claim that one source prescribes it for election results:

- [ONS line-chart guidance](https://service-manual.ons.gov.uk/data-visualisation/chart-types/line-chart)
  recommends markers for irregular intervals and gaps for missing observations.
  Elections occur at irregular intervals, so their positions use a numeric year
  scale and each observed election has a marker.
- [Datawrapper's line-chart editing guidance](https://www.datawrapper.de/blog/improved-line-chart-editing)
  documents filled and hollow symbol styles and direct series labels.
- [Government Analysis Function line-chart guidance](https://analysisfunction.civilservice.gov.uk/support/communicating-analysis/introduction-to-data-visualisation-e-learning/module-8-line-charts/)
  cautions against oversized or excessive markers and recommends direct labels
  and a text or table alternative. Only 12 elections and three groups are shown;
  the native Streamlit chart also exposes its underlying data table.

Statewide shares sum the recorded group vote counts before calculating shares.
They use hollow markers because there is no individual seat winner to encode.
In particular, a statewide first-preference leader, the group with the most
seats, and the party forming government need not coincide. The selected-seat
view uses the recorded winner after preferences, even when that group did not
lead on first preferences.

Electorates are matched by name, with no redistribution harmonisation. Missing
seat-years stay missing and are not connected. Statewide trends and bars retain
all recorded seats when the historical discrepancy filter hides flagged dots.
