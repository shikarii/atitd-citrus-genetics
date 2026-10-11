"""Gene Landscape — hidden gene pair visualization."""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_children, load_fitted_genes, load_profile_likelihoods

TRAITS = ["color", "sweet", "size", "length"]
DISPLAY_RULES = {"color": "mean", "sweet": "min", "size": "max", "length": "g1"}

st.set_page_config(page_title="Gene Landscape — ATITD Citrus", layout="wide")
st.title("Hidden Gene Landscape")
st.caption(
    "Visualizes the CLAIM MLE-fitted hidden gene pairs for each litter and trait. "
    "Under CLAIM, each parent carries 2 hidden genes per trait; the displayed trait "
    "is derived from these via a display rule (mean/min/max/g1)."
)

genes_df = load_fitted_genes()
children_df = load_children()
profile_df = load_profile_likelihoods()

if genes_df is None:
    st.error("Fitted genes not found. Run the full pipeline first.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Gene Pairs by Litter", "Gene Value Distribution", "Profile Likelihoods"])

with tab1:
    st.subheader("Fitted Hidden Gene Pairs")
    trait_sel = st.selectbox("Trait", TRAITS, key="gene_trait")
    rule = DISPLAY_RULES[trait_sel]
    st.caption(f"Display rule for {trait_sel}: **{rule}** — the shown value is the {rule} of g1 and g2.")

    # Parse gene pairs from "g1/g2" string format
    import pandas as pd

    plot_rows = []
    for _, row in genes_df.iterrows():
        for parent in ("A", "B"):
            gene_str = str(row.get(f"{parent}_{trait_sel}_genes", "500/500"))
            parts = gene_str.split("/")
            if len(parts) == 2:
                g1, g2 = int(parts[0]), int(parts[1])
                parent_observed = None
                if children_df is not None:
                    child_row = children_df[children_df["litter"] == row["litter"]].iloc[0]
                    parent_observed = int(child_row.get(f"{parent}_{trait_sel}", 0))
                plot_rows.append({
                    "litter": row["litter"],
                    "parent": parent,
                    "g1": g1,
                    "g2": g2,
                    "parent_observed": parent_observed,
                    "clone_share": float(row.get("clone_share", 0)),
                })

    plot_df = pd.DataFrame(plot_rows)

    # Scatter: g1 vs g2 for each parent/litter pair
    fig = px.scatter(
        plot_df,
        x="g1",
        y="g2",
        color="litter",
        symbol="parent",
        hover_data=["litter", "parent", "g1", "g2", "parent_observed"],
        labels={"g1": f"{trait_sel} gene 1", "g2": f"{trait_sel} gene 2"},
        title=f"Fitted hidden gene pairs for {trait_sel} (all litters, both parents)",
        height=500,
    )

    # Add identity line and feasibility constraint for display rule
    if rule == "mean":
        # Show lines of constant mean: g1 + g2 = 2*parent_observed
        for val in range(100, 1000, 100):
            fig.add_shape(
                type="line", x0=max(0, 2*val-1000), x1=min(1000, 2*val),
                y0=min(1000, 2*val), y1=max(0, 2*val-1000),
                line={"color": "lightgray", "width": 1, "dash": "dot"},
            )
    elif rule == "min":
        # min(g1,g2) = v -> one of them equals v, other >= v
        fig.add_shape(type="line", x0=0, x1=1000, y0=0, y1=1000, line={"color": "lightgray", "dash": "dot"})
    elif rule == "max":
        fig.add_shape(type="line", x0=0, x1=1000, y0=0, y1=1000, line={"color": "lightgray", "dash": "dot"})

    fig.update_xaxes(range=[0, 1000])
    fig.update_yaxes(range=[0, 1000])
    st.plotly_chart(fig, use_container_width=True)

    if rule == "g1":
        st.caption("For the g1 display rule, g2 is unconstrained (fixed at 500 by convention). Only g1 matters.")
    elif rule == "mean":
        st.caption("Gray diagonal lines connect gene pairs with the same mean (same displayed value).")
    else:
        st.caption(f"For the {rule} display rule, gene pairs lie on constrained lines.")

with tab2:
    st.subheader("Gene Value Distribution Across All Litters")
    all_genes = []
    for _, row in genes_df.iterrows():
        for parent in ("A", "B"):
            for trait in TRAITS:
                gene_str = str(row.get(f"{parent}_{trait}_genes", "500/500"))
                parts = gene_str.split("/")
                if len(parts) == 2:
                    g1, g2 = int(parts[0]), int(parts[1])
                    all_genes.append({"litter": row["litter"], "parent": parent, "trait": trait, "g1": g1, "g2": g2})
    all_genes_df = pd.DataFrame(all_genes)

    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.histogram(
            all_genes_df,
            x="g1",
            color="trait",
            facet_row="trait",
            nbins=50,
            labels={"g1": "Gene 1 value"},
            title="Distribution of fitted gene 1 values",
            height=600,
        )
        fig2.update_yaxes(matches=None)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.histogram(
            all_genes_df[all_genes_df["trait"] != "length"],  # g2 not meaningful for g1 rule
            x="g2",
            color="trait",
            facet_row="trait",
            nbins=50,
            labels={"g2": "Gene 2 value"},
            title="Distribution of fitted gene 2 values (excl. length with g1 rule)",
            height=600,
        )
        fig3.update_yaxes(matches=None)
        st.plotly_chart(fig3, use_container_width=True)

    st.caption(
        "Gene values pile up near parent observed values (the initialization). "
        "A flat distribution would mean genes are unconstrained (sloppy). "
        "Tight clusters around specific values indicate well-identified genes."
    )

with tab3:
    st.subheader("Profile Likelihoods")
    if profile_df is None:
        st.info(
            "Profile likelihoods not computed yet. "
            "Run the full pipeline without `--fast` to compute them."
        )
    else:
        litter_sel = st.selectbox("Litter", sorted(profile_df["litter"].unique()), key="prof_litter")
        parent_sel = st.selectbox("Parent", ["A", "B"], key="prof_parent")
        trait_sel2 = st.selectbox("Trait", TRAITS, key="prof_trait")
        gene_sel = st.selectbox("Gene slot", [0, 1], format_func=lambda x: f"g{x+1}", key="prof_slot")

        filtered = profile_df[
            (profile_df["litter"] == litter_sel)
            & (profile_df["parent"] == parent_sel)
            & (profile_df["trait"] == trait_sel2)
            & (profile_df["gene_slot"] == gene_sel)
        ].sort_values("fixed_value")

        if len(filtered) == 0:
            st.warning("No profile data for this selection.")
        else:
            mle_val = int(filtered["mle_value"].iloc[0])
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=filtered["fixed_value"],
                y=filtered["delta_ll"],
                mode="lines+markers",
                marker={"size": 4},
                line={"color": "#4c78a8"},
                name="Profile ΔLL",
            ))
            fig4.add_vline(x=mle_val, line_dash="dash", line_color="#e45756", annotation_text=f"MLE={mle_val}")
            fig4.add_hline(y=-1, line_dash="dot", line_color="orange", annotation_text="−1 LL interval")
            fig4.add_hline(y=-2, line_dash="dot", line_color="red", annotation_text="−2 LL interval")
            fig4.update_layout(
                title=f"Profile likelihood: {litter_sel} / Parent {parent_sel} / {trait_sel2} g{gene_sel+1}",
                xaxis_title=f"Gene value (fixed)",
                yaxis_title="Δ log-likelihood from MLE",
                height=400,
            )
            st.plotly_chart(fig4, use_container_width=True)
            st.caption(
                "Narrow curves (sharp -1 LL interval) = well-identified gene. "
                "Flat curves = sloppy parameter (many gene values are equally probable). "
                "Asymmetric curves indicate the likelihood surface is not Gaussian."
            )
