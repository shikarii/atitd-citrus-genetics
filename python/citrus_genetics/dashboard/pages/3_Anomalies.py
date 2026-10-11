"""Per-Child Anomaly Scores — children hardest for CLAIM to explain."""

import plotly.express as px
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_anomaly_scores, load_children

TRAITS = ["color", "sweet", "size", "length"]

st.set_page_config(page_title="Anomalies — ATITD Citrus", layout="wide")
st.title("Per-Child Anomaly Scores")
st.caption(
    "Children ranked by log-likelihood under CLAIM. Lowest = hardest for the model to explain. "
    "These are the most informative children for theory testing."
)

anomaly_df = load_anomaly_scores()
children_df = load_children()

if anomaly_df is None:
    st.error("Anomaly scores not found. Run the full pipeline first.")
    st.stop()

n_worst = st.slider("Show worst N children", min_value=5, max_value=50, value=20)

# Summary scatter: all children
st.subheader("All Children by CLAIM Log-Likelihood")
fig = px.scatter(
    anomaly_df,
    x="child_num",
    y="log_lik",
    color="litter",
    symbol="litter",
    hover_data=["litter", "child_num", "log_lik", "rank"],
    labels={"child_num": "Child position in litter", "log_lik": "CLAIM log-likelihood", "litter": "Litter"},
    title="Per-child CLAIM log-likelihood (lower = more anomalous)",
    height=450,
)
fig.update_traces(marker={"size": 6})
# Add FLOOR reference line
fig.add_hline(y=-34.5, line_dash="dot", line_color="red", annotation_text="FLOOR (1e-15)")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Histogram of log-likelihood
col1, col2 = st.columns(2)
with col1:
    fig2 = px.histogram(
        anomaly_df,
        x="log_lik",
        nbins=50,
        color="litter",
        labels={"log_lik": "CLAIM log-likelihood"},
        title="Distribution of per-child CLAIM log-likelihoods",
        height=350,
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    per_litter = anomaly_df.groupby("litter")["log_lik"].mean().sort_values().reset_index()
    fig3 = px.bar(
        per_litter,
        x="log_lik",
        y="litter",
        orientation="h",
        labels={"log_lik": "Mean child log-lik", "litter": ""},
        title="Mean child log-likelihood per litter (lower = harder litter)",
        height=350,
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# Worst N children table
st.subheader(f"Worst {n_worst} Children (most anomalous)")
worst = anomaly_df.nsmallest(n_worst, "log_lik")[
    ["rank", "litter", "child_num", "log_lik"]
].reset_index(drop=True)

# Attach trait values if available
if children_df is not None:
    # Build an index on (litter, child_num)
    child_pos_map = {}
    for litter, group in children_df.groupby("litter", sort=False):
        for pos, (_, row) in enumerate(group.iterrows(), start=1):
            child_pos_map[(litter, pos)] = row

    for col in TRAITS + [f"A_{t}" for t in TRAITS] + [f"B_{t}" for t in TRAITS]:
        worst[col] = worst.apply(
            lambda r: child_pos_map.get((r["litter"], r["child_num"]), {}).get(col, None),
            axis=1,
        )

st.dataframe(worst.style.background_gradient(subset=["log_lik"], cmap="RdYlGn"), use_container_width=True)

st.caption(
    "Rank 1 = worst (CLAIM assigns lowest probability). "
    "Children near FLOOR (-34.5) are combinations of parent genes that CLAIM says are nearly impossible. "
    "These are strong candidates for theory-falsifying observations."
)
