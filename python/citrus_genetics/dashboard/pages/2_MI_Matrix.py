"""Mutual Information Matrix — parent vs child trait coupling."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_mi_matrix

TRAITS = ["color", "sweet", "size", "length"]
PARENT_VARS = [f"{p}_{t}" for p in ("A", "B") for t in TRAITS]

st.set_page_config(page_title="MI Matrix — ATITD Citrus", layout="wide")
st.title("Mutual Information Matrix")
st.caption(
    "Under CLAIM, MI should be block-diagonal: A_color/B_color → color only, etc. "
    "Off-diagonal entries indicate unexplained inter-trait coupling."
)

mi_df = load_mi_matrix()
if mi_df is None:
    st.error("MI matrix not found. Run the full pipeline first.")
    st.stop()

tab1, tab2 = st.tabs(["Observed MI", "MI Excess (observed - shuffled)"])

with tab1:
    st.subheader("Observed Mutual Information")
    pivot_obs = mi_df.pivot(index="parent_var", columns="child_var", values="mi_observed")[TRAITS].loc[PARENT_VARS]

    fig = px.imshow(
        pivot_obs,
        color_continuous_scale="Viridis",
        labels={"color": "MI (nats)", "x": "Child trait", "y": "Parent variable"},
        title="MI(parent_var; child_trait) — k=3 nearest-neighbor estimator",
        aspect="auto",
        height=500,
    )
    # Add diagonal marker lines
    for i, pvar in enumerate(PARENT_VARS):
        trait = pvar.split("_", 1)[1]
        if trait in TRAITS:
            j = TRAITS.index(trait)
            fig.add_shape(
                type="rect", x0=j - 0.5, x1=j + 0.5, y0=i - 0.5, y1=i + 0.5,
                line={"color": "white", "width": 2}, fillcolor="rgba(0,0,0,0)"
            )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("White boxes highlight the expected CLAIM causal pairs (on-diagonal entries).")

    # Summary table
    diag_mean = mi_df[mi_df["is_diagonal"]]["mi_observed"].mean()
    off_mean = mi_df[~mi_df["is_diagonal"]]["mi_observed"].mean()
    ratio = diag_mean / (off_mean + 1e-10)
    col1, col2, col3 = st.columns(3)
    col1.metric("Diagonal mean MI", f"{diag_mean:.4f}")
    col2.metric("Off-diagonal mean MI", f"{off_mean:.4f}")
    col3.metric("Diagonal/off-diagonal ratio", f"{ratio:.1f}x")

with tab2:
    st.subheader("MI Excess Over Shuffled Baseline")
    st.caption(
        "MI excess = observed MI minus mean of 10 shuffled baselines. "
        "Positive values indicate genuine statistical dependence beyond sampling noise. "
        "Z-score > 2 suggests a significant coupling."
    )

    pivot_excess = mi_df.pivot(index="parent_var", columns="child_var", values="mi_excess")[TRAITS].loc[PARENT_VARS]
    pivot_z = mi_df.pivot(index="parent_var", columns="child_var", values="mi_excess_z")[TRAITS].loc[PARENT_VARS]

    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.imshow(
            pivot_excess,
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            labels={"color": "MI excess", "x": "Child trait", "y": "Parent variable"},
            title="MI excess (observed - shuffled mean)",
            aspect="auto",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.imshow(
            pivot_z,
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            labels={"color": "z-score", "x": "Child trait", "y": "Parent variable"},
            title="MI excess z-score (>2 = noteworthy)",
            aspect="auto",
        )
        fig3.add_shape(type="line", x0=-0.5, x1=3.5, y0=3.5, y1=3.5, line={"color": "white", "dash": "dot"})
        st.plotly_chart(fig3, use_container_width=True)

    # Top off-diagonal surprises
    off_diag = mi_df[~mi_df["is_diagonal"]].copy()
    top_surprises = off_diag.nlargest(8, "mi_excess_z")[
        ["parent_var", "child_var", "mi_observed", "mi_excess", "mi_excess_z"]
    ].reset_index(drop=True)
    st.subheader("Strongest Off-Diagonal Couplings")
    st.dataframe(top_surprises, use_container_width=True)
    st.caption(
        "These are parent-child trait pairs that CLAIM does not predict should be correlated. "
        "High z-scores here suggest the model is missing inter-trait dependencies."
    )
