"""Mixture Models — CLAIM + INDEP mixture weight per litter."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_mixture_weights

st.set_page_config(page_title="Mixture Models — ATITD Citrus", layout="wide")
st.title("CLAIM + INDEP Mixture Models")
st.caption(
    "For each litter, fits a mixture: π × CLAIM + (1-π) × INDEP, "
    "where INDEP assigns each trait uniformly from [0, 1000]. "
    "π ≈ 1 means CLAIM explains nearly all children; π ≈ 0 means mostly unexplained."
)

mix_df = load_mixture_weights()
if mix_df is None:
    st.error("Mixture weights not found. Run the full pipeline first.")
    st.stop()

# Summary metrics
mean_pi = float(mix_df["pi_claim"].mean())
min_pi = float(mix_df["pi_claim"].min())
n_low = int((mix_df["pi_claim"] < 0.7).sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mean CLAIM weight π", f"{mean_pi:.3f}")
col2.metric("Lowest π (most anomalous litter)", f"{min_pi:.3f}")
col3.metric("Litters with π < 0.7", str(n_low))
col4.metric("Litters", str(len(mix_df)))

st.markdown("---")

tab1, tab2 = st.tabs(["Mixture Weights", "Log-Likelihood Comparison"])

with tab1:
    st.subheader("CLAIM Mixture Weight π per Litter")
    mix_sorted = mix_df.sort_values("pi_claim").reset_index(drop=True)

    fig = go.Figure()
    fig.add_bar(
        x=mix_sorted["litter"],
        y=mix_sorted["pi_claim"],
        marker_color=mix_sorted["pi_claim"],
        marker_colorscale="RdYlGn",
        text=mix_sorted["pi_claim"].round(3),
        textposition="outside",
        name="π (CLAIM weight)",
    )
    fig.add_hline(y=0.9, line_dash="dot", line_color="green", annotation_text="π=0.9")
    fig.add_hline(y=0.7, line_dash="dash", line_color="orange", annotation_text="π=0.7")
    fig.update_layout(
        title="CLAIM mixture weight π per litter (sorted, lowest first)",
        xaxis_title="Litter",
        yaxis_title="π (CLAIM weight)",
        yaxis={"range": [0, 1.05]},
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Waterfall: children count
    fig2 = px.scatter(
        mix_sorted,
        x="litter",
        y="pi_claim",
        size="n",
        color="pi_claim",
        color_continuous_scale="RdYlGn",
        range_color=[0, 1],
        labels={"pi_claim": "π (CLAIM)", "n": "Children", "litter": "Litter"},
        title="π by litter, bubble size = number of children",
        height=400,
    )
    fig2.add_hline(y=1.0, line_dash="dot", line_color="green", opacity=0.4)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Mixture vs CLAIM-Only Log-Likelihood")
    st.caption(
        "delta_ll = log-lik(mixture) - log-lik(CLAIM-only). "
        "Positive delta means the mixture fit is better, suggesting some children look more like INDEP."
    )

    fig3 = px.bar(
        mix_df.sort_values("delta_ll", ascending=False),
        x="litter",
        y="delta_ll",
        color="delta_ll",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        labels={"delta_ll": "Δ log-lik (mixture − CLAIM)", "litter": "Litter"},
        title="Mixture model improvement over CLAIM-only log-likelihood per litter",
        height=400,
    )
    fig3.add_hline(y=0, line_color="black")
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(mix_df.sort_values("pi_claim")[
        ["litter", "n", "pi_claim", "pi_indep", "log_lik_claim_only", "log_lik_mixture", "delta_ll"]
    ], use_container_width=True)

st.markdown("---")
st.subheader("Interpretation")
st.markdown("""
- **π near 1.0**: CLAIM explains nearly all children in this litter. The mixture offers no benefit.
- **π near 0.7**: About 30% of children are better explained by INDEP (uniform noise). This litter has
  unusual children that don't fit any inheritance pattern — possible data quality issue or genuine anomaly.
- **High delta_ll**: The mixture fit is meaningfully better than CLAIM alone — some children look random.
- If most litters have π > 0.9, CLAIM is highly self-consistent across litters.
""")
