"""Residual Analysis — observed vs CLAIM-predicted trait values."""

import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import (
    load_residuals,
    load_sibling_correlations,
    load_trait_cooccurrence,
)

TRAITS = ["color", "sweet", "size", "length"]

st.set_page_config(page_title="Residuals — ATITD Citrus", layout="wide")
st.title("Residual Analysis")
st.caption(
    "Residual = observed trait value minus the most probable CLAIM-predicted value. "
    "Under a well-specified model, residuals should be roughly symmetric around zero."
)

residuals_df = load_residuals()
sib_corr_df = load_sibling_correlations()
cooccurrence_df = load_trait_cooccurrence()

if residuals_df is None:
    st.error("Residuals not found. Run the full pipeline first.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Residual Distributions", "Sibling Correlations", "Trait Co-occurrence"])

with tab1:
    st.subheader("Per-Trait Residual Distributions")
    col1, col2 = st.columns(2)
    for idx, trait in enumerate(TRAITS):
        col = col1 if idx % 2 == 0 else col2
        with col:
            col_name = f"{trait}_residual"
            if col_name in residuals_df.columns:
                fig = px.histogram(
                    residuals_df,
                    x=col_name,
                    nbins=60,
                    color="litter",
                    marginal="box",
                    labels={col_name: f"{trait} residual"},
                    title=f"{trait.title()} residuals",
                    height=350,
                )
                fig.add_vline(x=0, line_color="black", line_dash="dash")
                st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.subheader("Residual Summary Statistics")
    summary_rows = []
    for trait in TRAITS:
        col_name = f"{trait}_residual"
        if col_name in residuals_df.columns:
            col_data = residuals_df[col_name]
            summary_rows.append({
                "trait": trait,
                "mean": round(float(col_data.mean()), 2),
                "std": round(float(col_data.std()), 2),
                "median": round(float(col_data.median()), 1),
                "max_abs": int(col_data.abs().max()),
                "pct_gt_100": round(float((col_data.abs() > 100).mean() * 100), 1),
            })
    import pandas as pd
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
    st.caption("`pct_gt_100` = percentage of children with |residual| > 100 (large unexplained deviation).")

    # Scatter: residuals by litter
    st.subheader("Residuals Over Children (by litter)")
    trait_sel = st.selectbox("Trait", TRAITS, key="res_trait")
    col_name = f"{trait_sel}_residual"
    if col_name in residuals_df.columns:
        fig2 = px.scatter(
            residuals_df,
            x="child_num",
            y=col_name,
            color="litter",
            facet_col="litter",
            facet_col_wrap=4,
            labels={"child_num": "Child #", col_name: "Residual"},
            title=f"{trait_sel.title()} residuals by child within each litter",
            height=500,
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Within-Litter Sibling Correlations")
    st.caption(
        "Pearson r between adjacent siblings within each litter. "
        "Under CLAIM (children independent given parents), r should be near zero. "
        "Systematic positive r might indicate shared environmental effects or batch effects."
    )
    if sib_corr_df is not None and len(sib_corr_df) > 0:
        fig3 = px.bar(
            sib_corr_df,
            x="litter",
            y="pearson_r",
            color="trait",
            barmode="group",
            labels={"pearson_r": "Pearson r", "litter": "Litter"},
            title="Sibling Pearson correlations per litter and trait",
            height=400,
        )
        fig3.add_hline(y=0, line_color="black")
        fig3.add_hline(y=0.3, line_dash="dot", line_color="orange", annotation_text="r=0.3")
        fig3.add_hline(y=-0.3, line_dash="dot", line_color="orange")
        st.plotly_chart(fig3, use_container_width=True)

        sig = sib_corr_df[sib_corr_df["p_value"] < 0.05].sort_values("pearson_r", key=abs, ascending=False)
        if len(sig) > 0:
            st.warning(f"{len(sig)} significant sibling correlations (p < 0.05):")
            st.dataframe(sig, use_container_width=True)
        else:
            st.success("No significant sibling correlations detected (p < 0.05 uncorrected).")
    else:
        st.info("Sibling correlation data not available.")

with tab3:
    st.subheader("Trait Change Co-occurrence Matrix")
    st.caption(
        "Each cell counts how many children had both traits deviate by >50 from parental range simultaneously. "
        "Under CLAIM (one-of-8 mutation), double-trait changes should be rare (~1/7 of single-trait changes). "
        "High off-diagonal counts suggest multiple mutations or inter-trait mechanisms."
    )
    if cooccurrence_df is not None:
        fig4 = px.imshow(
            cooccurrence_df,
            color_continuous_scale="Blues",
            labels={"color": "Count", "x": "Trait 2", "y": "Trait 1"},
            title="Trait co-occurrence: count of children where both traits changed by >50",
            text_auto=True,
            aspect="auto",
        )
        st.plotly_chart(fig4, use_container_width=True)

        # Flag if diagonal >> 1/7 * off-diagonal average
        import numpy as np
        mat = cooccurrence_df.values.astype(float)
        for i in range(4):
            mat[i, i] = 0  # zero diagonal for comparison
        n_off_nonzero = int((mat > 0).sum())
        total_off = float(mat.sum())
        st.caption(
            f"Total off-diagonal co-occurrences: {total_off:.0f} across {n_off_nonzero} pairs. "
            f"Under one-of-8 mutation, expect ~0 since only 1 gene is nudged at a time."
        )
    else:
        st.info("Co-occurrence data not available.")
