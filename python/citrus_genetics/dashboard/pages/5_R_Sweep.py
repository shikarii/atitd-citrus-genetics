"""R Sweep — nudge range sensitivity analysis."""

import plotly.graph_objects as go
import streamlit as st

from citrus_genetics.dashboard.data_loader import load_r_sweep

st.set_page_config(page_title="R Sweep — ATITD Citrus", layout="wide")
st.title("Nudge Range (R) Parameter Sweep")
st.caption(
    "CLAIM uses R=150: each gene is nudged by a uniform random value in [-150, +150]. "
    "This sweep tests how fit quality changes across R=50..300. "
    "A narrow peak means R=150 is precisely determined; a broad plateau means it is sloppy."
)

sweep_df = load_r_sweep()
if sweep_df is None:
    st.error("R sweep results not found. Run the full pipeline first.")
    st.stop()

CLAIM_R = 150

best_fit_r = int(sweep_df.loc[sweep_df["fit_ll"].idxmax(), "R"])
best_cv_r = int(sweep_df.loc[sweep_df["cv_ll"].idxmax(), "R"])
claim_fit = float(sweep_df.loc[sweep_df["R"] == CLAIM_R, "fit_ll"].iloc[0]) if CLAIM_R in sweep_df["R"].values else None

col1, col2, col3 = st.columns(3)
col1.metric("Best R (fit_ll)", str(best_fit_r))
col2.metric("Best R (cv_ll)", str(best_cv_r))
if claim_fit is not None:
    col3.metric("CLAIM R=150 fit_ll", f"{claim_fit:,.1f}")

# Main line chart
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=sweep_df["R"], y=sweep_df["fit_ll"],
    name="fit_ll (in-sample)",
    mode="lines+markers",
    marker={"size": 4},
    line={"color": "#4c78a8"},
))
fig.add_trace(go.Scatter(
    x=sweep_df["R"], y=sweep_df["cv_ll"],
    name="cv_ll (cross-validated)",
    mode="lines+markers",
    marker={"size": 4},
    line={"color": "#f58518", "dash": "dash"},
))
fig.add_vline(x=CLAIM_R, line_dash="dot", line_color="#e45756", annotation_text=f"CLAIM R={CLAIM_R}")
fig.add_vline(x=best_fit_r, line_dash="dash", line_color="#4c78a8",
              annotation_text=f"Best fit R={best_fit_r}", annotation_position="top left")
fig.update_layout(
    title="Log-likelihood vs nudge range R",
    xaxis_title="R (nudge range ±R)",
    yaxis_title="Log-likelihood",
    height=500,
    legend={"yanchor": "bottom", "y": 0.05, "xanchor": "right", "x": 0.99},
)
st.plotly_chart(fig, use_container_width=True)

# Delta from CLAIM
col1, col2 = st.columns(2)
with col1:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=sweep_df["R"], y=sweep_df["delta_fit"],
        name="delta fit_ll",
        fill="tozeroy",
        mode="lines",
        line={"color": "#4c78a8"},
    ))
    fig2.add_vline(x=CLAIM_R, line_dash="dot", line_color="#e45756", annotation_text="CLAIM R=150")
    fig2.add_hline(y=0, line_color="black")
    fig2.update_layout(
        title="Fit log-lik delta vs CLAIM (R=150)",
        xaxis_title="R",
        yaxis_title="Delta fit_ll",
        height=350,
    )
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=sweep_df["R"], y=sweep_df["delta_cv"],
        name="delta cv_ll",
        fill="tozeroy",
        mode="lines",
        line={"color": "#f58518"},
    ))
    fig3.add_vline(x=CLAIM_R, line_dash="dot", line_color="#e45756", annotation_text="CLAIM R=150")
    fig3.add_hline(y=0, line_color="black")
    fig3.update_layout(
        title="CV log-lik delta vs CLAIM (R=150)",
        xaxis_title="R",
        yaxis_title="Delta cv_ll",
        height=350,
    )
    st.plotly_chart(fig3, use_container_width=True)

# Raw table
with st.expander("Raw sweep data"):
    st.dataframe(sweep_df, use_container_width=True)

# Interpretation
best_delta_fit = float(sweep_df["delta_fit"].max())
best_delta_cv = float(sweep_df["delta_cv"].max())
st.markdown("---")
st.subheader("Interpretation")
st.markdown(f"""
- **Best fit_ll at R={best_fit_r}** (delta: {best_delta_fit:+.1f} vs CLAIM R=150)
- **Best cv_ll at R={best_cv_r}** (delta: {best_delta_cv:+.1f} vs CLAIM R=150)
- If |delta| < 5, R=150 is indistinguishable within log-likelihood noise.
- If the curve has a sharp peak at R=150, the mutation range is well-identified.
- If the curve is flat over a wide range (e.g., R=100–250 differ by < 10), R is sloppy.
""")
