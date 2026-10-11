"""Distribution Tests — KS/AD goodness-of-fit per litter × trait."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_distribution_tests

TRAITS = ["color", "sweet", "size", "length"]

st.set_page_config(page_title="Distribution Tests — ATITD Citrus", layout="wide")
st.title("Distribution Goodness-of-Fit Tests")
st.caption(
    "For each (litter, trait) pair: simulate 500 children from CLAIM MLE fitted genes, "
    "then run a 2-sample KS test and Anderson-Darling test comparing observed vs simulated. "
    "Significant results indicate CLAIM cannot reproduce the observed distribution."
)

tests_df = load_distribution_tests()
if tests_df is None:
    st.error("Distribution test results not found. Run the full pipeline first.")
    st.stop()

FDR_ALPHA = 0.05
n_sig_fdr = int(tests_df["ks_sig_fdr"].sum())
n_sig_raw = int((tests_df["ks_pvalue"] < FDR_ALPHA).sum())
n_ad_sig = int(tests_df["ad_sig_5pct"].sum()) if "ad_sig_5pct" in tests_df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total tests", "56 (14 litters × 4 traits)")
col2.metric("KS significant (raw α=0.05)", str(n_sig_raw))
col3.metric("KS significant (BH-FDR)", str(n_sig_fdr))
col4.metric("AD significant (5%)", str(n_ad_sig))

tab1, tab2, tab3 = st.tabs(["Heatmap", "Volcano Plot", "Test Results Table"])

with tab1:
    st.subheader("KS Statistic Heatmap (litter × trait)")
    pivot = tests_df.pivot(index="litter", columns="trait", values="ks_stat")[TRAITS]
    fig = px.imshow(
        pivot,
        color_continuous_scale="YlOrRd",
        labels={"color": "KS statistic", "x": "Trait", "y": "Litter"},
        title="2-sample KS statistic (higher = larger distributional discrepancy)",
        text_auto=".3f",
        aspect="auto",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # FDR significance overlay
    sig_pivot = tests_df.pivot(index="litter", columns="trait", values="ks_sig_fdr")[TRAITS]
    st.subheader("Significance (BH-FDR corrected, α=0.05)")
    fig2 = px.imshow(
        sig_pivot.astype(int),
        color_continuous_scale=[[0, "#cccccc"], [1, "#e45756"]],
        labels={"color": "Significant", "x": "Trait", "y": "Litter"},
        title="KS test significant after BH-FDR correction (red = significant)",
        text_auto=True,
        aspect="auto",
        height=450,
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Volcano-Style Plot")
    st.caption("-log10(p) on y-axis; KS statistic on x-axis. Points above dashed line = FDR-significant.")
    import numpy as np
    tests_df = tests_df.copy()
    tests_df["neg_log10_p"] = -np.log10(tests_df["ks_pvalue"].clip(1e-10))
    tests_df["label"] = tests_df["litter"] + " / " + tests_df["trait"]

    fdr_threshold = -np.log10(FDR_ALPHA)
    fig3 = px.scatter(
        tests_df,
        x="ks_stat",
        y="neg_log10_p",
        color="trait",
        symbol="ks_sig_fdr",
        hover_data=["litter", "trait", "ks_stat", "ks_pvalue", "ks_pvalue_fdr"],
        labels={"ks_stat": "KS statistic", "neg_log10_p": "-log10(KS p-value)", "trait": "Trait"},
        title="Volcano plot: KS statistic vs significance",
        height=500,
    )
    fig3.add_hline(y=fdr_threshold, line_dash="dash", line_color="red",
                   annotation_text=f"α={FDR_ALPHA} (raw)")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("All Test Results")
    show_cols = ["litter", "trait", "n_observed", "ks_stat", "ks_pvalue", "ks_pvalue_fdr", "ks_sig_fdr",
                 "ad_stat", "ad_sig_5pct"]
    show_cols = [c for c in show_cols if c in tests_df.columns]
    display = tests_df[show_cols].copy()

    # Color significant rows
    st.dataframe(
        display.style
        .background_gradient(subset=["ks_stat"], cmap="YlOrRd")
        .applymap(lambda v: "background-color: #ffe5cc" if v else "", subset=["ks_sig_fdr"]),
        use_container_width=True,
    )

st.markdown("---")
st.subheader("Interpretation")
st.markdown(f"""
- **{n_sig_fdr}/56** tests are significant after Benjamini-Hochberg FDR correction at α={FDR_ALPHA}.
- A high KS statistic means the simulated CLAIM distribution looks systematically different from the observed one.
- Check which traits fail in the most litters — those traits' display rules or mutation parameters may be wrong.
- Note: p-values assume i.i.d. observations; litter structure may slightly inflate false-positive rates.
""")
