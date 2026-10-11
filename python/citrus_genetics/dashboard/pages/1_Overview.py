"""Model Comparison Overview — 30-model leaderboard and per-litter breakdown."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_children, load_model_comparison

st.set_page_config(page_title="Overview — ATITD Citrus", layout="wide")
st.title("Model Comparison Overview")
st.caption("30 models compared by in-sample fit and cross-validated log-likelihood")

comp = load_model_comparison()
children = load_children()

if comp is None:
    st.error("Model comparison results not found. Run `python -m citrus_genetics.cli.run_all --allow-dirty`.")
    st.stop()

# --- Summary stats ---
col1, col2, col3, col4 = st.columns(4)
claim_row = comp[comp["model"].str.startswith("CLAIM")].iloc[0]
col1.metric("CLAIM fit_ll", f"{claim_row['fit_ll']:,.1f}")
col2.metric("CLAIM cv_ll", f"{claim_row['cv_ll']:,.1f}")
if children is not None:
    col3.metric("Total children", f"{len(children):,}")
    col4.metric("Litters", str(children["litter"].nunique()))

st.markdown("---")

# --- Leaderboard table ---
tab1, tab2 = st.tabs(["Leaderboard", "Per-Litter Heatmap"])

with tab1:
    st.subheader("30-Model Leaderboard")

    show_cols = ["model", "fit_ll", "cv_ll", "cv_vs_claim", "children_impossible"]
    display_df = comp[show_cols].copy()
    display_df = display_df.sort_values("fit_ll", ascending=False).reset_index(drop=True)
    display_df.index += 1

    # Horizontal bar chart sorted by fit_ll
    fig = px.bar(
        display_df.iloc[::-1],
        x="fit_ll",
        y="model",
        orientation="h",
        color=display_df.iloc[::-1]["model"].str.startswith("CLAIM"),
        color_discrete_map={True: "#e07b39", False: "#4c78a8"},
        labels={"fit_ll": "Fit log-likelihood", "model": ""},
        title="In-sample fit log-likelihood (higher = better)",
        height=700,
    )
    fig.update_layout(showlegend=False, yaxis={"tickfont": {"size": 10}})
    fig.add_vline(x=float(claim_row["fit_ll"]), line_dash="dot", line_color="#e07b39", opacity=0.5)
    st.plotly_chart(fig, use_container_width=True)

    # CV vs CLAIM bar chart
    fig2 = px.bar(
        display_df.iloc[::-1],
        x="cv_vs_claim",
        y="model",
        orientation="h",
        color=display_df.iloc[::-1]["cv_vs_claim"] > 0,
        color_discrete_map={True: "#54a24b", False: "#e45756"},
        labels={"cv_vs_claim": "CV delta vs CLAIM", "model": ""},
        title="Cross-validated log-likelihood delta vs CLAIM (positive = better than CLAIM on CV)",
        height=700,
    )
    fig2.update_layout(showlegend=False, yaxis={"tickfont": {"size": 10}})
    fig2.add_vline(x=0, line_color="gray")
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(
        display_df.style.highlight_max(subset=["fit_ll", "cv_ll"], color="#ffe5cc"),
        use_container_width=True,
    )

with tab2:
    st.subheader("Per-Litter Log-Likelihood Heatmap")
    ll_cols = [c for c in comp.columns if c.startswith("ll_")]
    if ll_cols:
        litter_names = [c.replace("ll_", "") for c in ll_cols]
        heatmap_df = comp[["model", *ll_cols]].set_index("model")
        heatmap_df.columns = litter_names

        fig3 = px.imshow(
            heatmap_df,
            color_continuous_scale="RdBu",
            color_continuous_midpoint=float(heatmap_df.values.mean()),
            labels={"color": "log-lik", "x": "Litter", "y": "Model"},
            title="Per-litter log-likelihood (brighter red = fits better)",
            aspect="auto",
            height=600,
        )
        fig3.update_xaxes(tickangle=45)
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            "Rows = models (30 total), columns = litters (14 total). "
            "Relative brightness shows which model wins each litter."
        )
    else:
        st.info("Per-litter columns not found in model_comparison.csv.")

# --- Impossible children ---
st.markdown("---")
st.subheader("Children Impossible Under Each Model")
st.caption("Number of children with likelihood < 1e-9 (model assigns effectively zero probability)")
fig4 = px.bar(
    display_df.sort_values("children_impossible"),
    x="children_impossible",
    y="model",
    orientation="h",
    color=display_df.sort_values("children_impossible")["model"].str.startswith("CLAIM"),
    color_discrete_map={True: "#e07b39", False: "#4c78a8"},
    labels={"children_impossible": "Impossible children", "model": ""},
    height=500,
)
fig4.update_layout(showlegend=False)
st.plotly_chart(fig4, use_container_width=True)
