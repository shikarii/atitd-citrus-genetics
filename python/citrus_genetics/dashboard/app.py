"""ATITD Citrus Genetics — Analysis Dashboard.

Main Streamlit entry point. Sets page config and shows a landing overview.
Individual analysis views are in the pages/ subdirectory.

Launch:
    streamlit run python/citrus_genetics/dashboard/app.py
"""

import streamlit as st

from citrus_genetics.dashboard.data_loader import missing_artifacts, results_available

st.set_page_config(
    page_title="ATITD Citrus Genetics",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("ATITD Citrus Genetics — Analysis Dashboard")
st.caption("Reverse-engineering citrus tree breeding mechanics in A Tale in the Desert")

st.markdown("""
This dashboard visualizes the results of the ATITD citrus genetics research methodology
([docs/research_methodology.md](../../docs/research_methodology.md)).

---

**Data:** 692 children from 14 litters (Hive1–Hive11, Hive1a/b/c), 4 observable traits each.

**Methodology:** Compare the CLAIM model (2 hidden genes/trait, slot-preserving inheritance,
one-of-8 uniform ±150 mutation, clone component) against 29 rivals using exact likelihood fitting.
Multiple analysis methods probe what CLAIM explains and where it fails.

---
""")

if not results_available():
    st.error(
        "No results found in `results/current/`. "
        "Run the full pipeline first:\n\n"
        "```bash\npython -m citrus_genetics.cli.run_all --allow-dirty\n```"
    )
else:
    missing = missing_artifacts()
    if missing:
        st.warning(
            f"Some analysis artifacts are missing (run `run_all` to generate them): "
            f"{', '.join(missing)}"
        )
    else:
        st.success("All analysis artifacts found. Use the sidebar to explore results.")

st.markdown("### Navigation")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
**Model Comparison**
- [1 Overview](1_Overview) — 30-model leaderboard
- [5 R Sweep](5_R_Sweep) — nudge range sensitivity
- [7 Mixture Models](7_Mixture_Models) — CLAIM+INDEP mixture

**Goodness of Fit**
- [6 Distribution Tests](6_Distribution_Tests) — KS/AD per litter×trait
- [4 Residuals](4_Residuals) — residual histograms & sibling correlations
""")

with col2:
    st.markdown("""
**Information & Causality**
- [2 MI Matrix](2_MI_Matrix) — mutual information heatmap
- [3 Anomalies](3_Anomalies) — most puzzling children

**Deep Dives**
- [8 Litter Deep Dive](8_Litter_Deep_Dive) — per-litter exploration
- [9 Gene Landscape](9_Gene_Landscape) — hidden gene pairs
""")

with col3:
    st.markdown("""
**How to run:**
```bash
# Full analysis (~5 min)
python -m citrus_genetics.cli.run_all --allow-dirty

# Fast (skip profile likelihoods)
python -m citrus_genetics.cli.run_all --allow-dirty --fast

# Launch dashboard
streamlit run python/citrus_genetics/dashboard/app.py
```
""")
