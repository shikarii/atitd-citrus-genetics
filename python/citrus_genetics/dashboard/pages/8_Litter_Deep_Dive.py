"""Litter Deep Dive — per-litter interactive exploration."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import (
    load_anomaly_scores,
    load_children,
    load_fitted_genes,
    load_residuals,
)

TRAITS = ["color", "sweet", "size", "length"]

st.set_page_config(page_title="Litter Deep Dive — ATITD Citrus", layout="wide")
st.title("Litter Deep Dive")
st.caption("Select a litter to explore parent genes, child trait distributions, and per-child residuals.")

children_df = load_children()
genes_df = load_fitted_genes()
residuals_df = load_residuals()
anomaly_df = load_anomaly_scores()

if children_df is None:
    st.error("Children data not found.")
    st.stop()

litters = sorted(children_df["litter"].unique())
selected_litter = st.selectbox("Select litter", litters)

litter_children = children_df[children_df["litter"] == selected_litter].reset_index(drop=True)
n_children = len(litter_children)

st.subheader(f"{selected_litter} — {n_children} children")

# Parent traits
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Parent A traits**")
    parent_a = {t: int(litter_children[f"A_{t}"].iloc[0]) for t in TRAITS}
    st.dataframe(
        {"trait": list(parent_a.keys()), "value": list(parent_a.values())},
        use_container_width=True,
    )
with col2:
    st.markdown("**Parent B traits**")
    parent_b = {t: int(litter_children[f"B_{t}"].iloc[0]) for t in TRAITS}
    st.dataframe(
        {"trait": list(parent_b.keys()), "value": list(parent_b.values())},
        use_container_width=True,
    )

# Fitted genes (if available)
if genes_df is not None:
    litter_genes = genes_df[genes_df["litter"] == selected_litter]
    if len(litter_genes) > 0:
        row = litter_genes.iloc[0]
        with st.expander("CLAIM MLE Fitted Hidden Genes"):
            gene_rows = []
            for t in TRAITS:
                gene_rows.append({
                    "trait": t,
                    "A_g1/g2": str(row.get(f"A_{t}_genes", "?")),
                    "B_g1/g2": str(row.get(f"B_{t}_genes", "?")),
                })
            import pandas as pd
            st.dataframe(pd.DataFrame(gene_rows), use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric("Log-likelihood", f"{row.get('loglik', '?'):.1f}")
            col2.metric("Clone share", f"{row.get('clone_share', 0):.3f}")

st.markdown("---")

# Child trait distributions
tab1, tab2, tab3 = st.tabs(["Trait Distributions", "Scatter Matrix", "Residuals"])

with tab1:
    st.subheader(f"Child trait distributions — {selected_litter}")
    fig = go.Figure()
    for i, trait in enumerate(TRAITS):
        vals = litter_children[trait].tolist()
        fig.add_trace(go.Box(
            y=vals,
            name=trait,
            boxpoints="all",
            jitter=0.3,
            pointpos=-1.8,
        ))
        # Add parent reference lines
        fig.add_shape(
            type="line", x0=i - 0.4, x1=i + 0.4,
            y0=parent_a[trait], y1=parent_a[trait],
            line={"color": "blue", "dash": "dash", "width": 1},
        )
        fig.add_shape(
            type="line", x0=i - 0.4, x1=i + 0.4,
            y0=parent_b[trait], y1=parent_b[trait],
            line={"color": "red", "dash": "dash", "width": 1},
        )
    fig.update_layout(
        title=f"{selected_litter}: child trait distributions (blue=parent A, red=parent B)",
        yaxis_title="Trait value (0-1000)",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"Scatter matrix — {selected_litter}")
    fig2 = px.scatter_matrix(
        litter_children[TRAITS],
        dimensions=TRAITS,
        title=f"{selected_litter}: pairwise child trait scatter",
        height=550,
    )
    fig2.update_traces(diagonal_visible=False, marker={"size": 5})
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    if residuals_df is not None:
        litter_res = residuals_df[residuals_df["litter"] == selected_litter].reset_index(drop=True)
        if len(litter_res) > 0:
            st.subheader(f"CLAIM residuals — {selected_litter}")
            fig3 = go.Figure()
            for trait in TRAITS:
                col_name = f"{trait}_residual"
                if col_name in litter_res.columns:
                    fig3.add_trace(go.Scatter(
                        x=litter_res["child_num"],
                        y=litter_res[col_name],
                        mode="markers+lines",
                        name=trait,
                        marker={"size": 6},
                    ))
            fig3.add_hline(y=0, line_color="black", line_dash="dash")
            fig3.update_layout(
                title=f"{selected_litter}: per-child residuals (observed - CLAIM predicted)",
                xaxis_title="Child #",
                yaxis_title="Residual",
                height=400,
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No residual data for this litter.")
    else:
        st.info("Residuals not computed yet.")

# Anomaly highlight
if anomaly_df is not None:
    litter_anom = anomaly_df[anomaly_df["litter"] == selected_litter].copy()
    if len(litter_anom) > 0:
        worst_child = litter_anom.nsmallest(1, "log_lik").iloc[0]
        if worst_child["log_lik"] < -5:
            st.warning(
                f"Child #{int(worst_child['child_num'])} has the worst CLAIM log-likelihood in this litter: "
                f"{worst_child['log_lik']:.2f} (overall rank: #{int(worst_child['rank'])})"
            )

# Download
st.markdown("---")
st.download_button(
    "Download litter children as CSV",
    data=litter_children.to_csv(index=False),
    file_name=f"{selected_litter}_children.csv",
    mime="text/csv",
)
