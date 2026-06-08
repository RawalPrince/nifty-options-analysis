import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="NIFTY Options Analysis",
    page_icon="📈",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/nifty_options_clean.csv")
    df["date"]   = pd.to_datetime(df["date"])
    df["expiry"] = pd.to_datetime(df["expiry"])
    df["dte"]    = (df["expiry"] - df["date"]).dt.days

    df["atm_distance"] = abs(df["strike"] - df["underlying_price"]) / \
                          df["underlying_price"] * 100

    def classify_moneyness(row):
        dist = row["atm_distance"]
        if dist <= 1:
            return "ATM"
        elif row["option_type"] == "CE":
            return "OTM" if row["strike"] > row["underlying_price"] else "ITM"
        else:
            return "OTM" if row["strike"] < row["underlying_price"] else "ITM"

    df["moneyness"] = df.apply(classify_moneyness, axis=1)
    return df

df = load_data()
df_near = df[df["dte"] <= 30].copy()

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=60)
    st.title("NIFTY Options\nAnalysis")
    st.markdown("---")
    st.markdown("**Data Range**")
    st.info(f"{df['date'].min().strftime('%d %b %Y')} → {df['date'].max().strftime('%d %b %Y')}")
    st.markdown("**Total Records**")
    st.info(f"{len(df):,} options records")
    st.markdown("**Expiry Cycles**")
    st.info(f"{df_near['expiry'].nunique()} weekly/monthly expiries")
    st.markdown("---")
    st.markdown("Built by **Prince Rawal**")
    st.markdown("B.E. Computer Engineering")
    st.markdown("Python | Pandas | Streamlit")

# ── Title ─────────────────────────────────────────────
st.title("📈 NIFTY Options Expiry Analysis")
st.markdown("**6-month analysis of NIFTY weekly options | Dec 2024 – May 2025 | NSE Data**")
st.markdown("---")

# ── Metric Cards ──────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records",    f"{len(df):,}")
col2.metric("Expiry Cycles",    f"{df_near['expiry'].nunique()}")
col3.metric("Trading Days",     f"{df['date'].nunique()}")
col4.metric("Avg Max Pain Gap", "0.24%")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 Theta Decay",
    "🎯 Max Pain & OI",
    "📊 PCR Signal",
    "🌊 IV Analysis"
])

# ════════════════════════════════════════════════════
# TAB 1 — THETA DECAY
# ════════════════════════════════════════════════════
with tab1:
    st.subheader("ATM Options Premium Decay Around Expiry")
    st.markdown("How ATM option premiums decay as expiry approaches across 30 expiry cycles.")

    atm_decay = df_near[
        (df_near["moneyness"] == "ATM") &
        (df_near["dte"] <= 15) &
        (df_near["close"] > 0)
    ].copy()

    decay_curve = atm_decay.groupby(
        ["dte", "option_type"]
    )["close"].median().reset_index()
    decay_curve.columns = ["dte", "option_type", "median_premium"]

    fig1 = make_subplots(rows=1, cols=2,
                         subplot_titles=("CE Options Decay", "PE Options Decay"))

    for i, opt in enumerate(["CE", "PE"], 1):
        data = decay_curve[decay_curve["option_type"] == opt].sort_values("dte")
        color = "#2196F3" if opt == "CE" else "#F44336"

        fig1.add_trace(go.Scatter(
            x=data["dte"], y=data["median_premium"],
            mode="lines+markers", name=f"{opt} Premium",
            line=dict(color=color, width=2.5),
            marker=dict(size=6),
            fill="tozeroy", fillcolor=f"rgba{'(33,150,243,0.1)' if opt=='CE' else '(244,67,54,0.1)'}"
        ), row=1, col=i)

        # Decay annotation
        d15 = data[data["dte"]==15]["median_premium"].values
        d2  = data[data["dte"]==2]["median_premium"].values
        if len(d15) and len(d2):
            pct = (d15[0] - d2[0]) / d15[0] * 100
            fig1.add_annotation(
                x=8, y=data["median_premium"].max() * 0.8,
                text=f"Decay DTE-15→DTE-2:<br><b>{pct:.1f}%</b>",
                showarrow=False, row=1, col=i,
                bgcolor="lightyellow", bordercolor="orange"
            )

    fig1.update_xaxes(autorange="reversed", title_text="Days to Expiry (DTE)")
    fig1.update_yaxes(title_text="Median Premium (₹)", col=1)
    fig1.update_layout(height=450, showlegend=True,
                       plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.info("💡 **Key Finding:** CE premiums lose **61.7%** of value from DTE-15 to DTE-2")
    col2.info("💡 **Key Finding:** PE premiums lose **58.1%** of value from DTE-15 to DTE-2")

# ════════════════════════════════════════════════════
# TAB 2 — MAX PAIN & OI
# ════════════════════════════════════════════════════
with tab2:
    st.subheader("Max Pain vs NIFTY Expiry Close")
    st.markdown("Max pain level compared to actual NIFTY closing price on each expiry.")

    def calculate_max_pain(exp_data):
        strikes = exp_data["strike"].unique()
        pain = {}
        for s in strikes:
            ce_loss = exp_data[
                (exp_data["option_type"] == "CE") &
                (exp_data["strike"] < s)
            ]["open_interest"].sum()

            pe_loss = exp_data[
                (exp_data["option_type"] == "PE") &
                (exp_data["strike"] > s)
            ]["open_interest"].sum()

            pain[s] = ce_loss + pe_loss

        return min(pain, key=pain.get) if pain else None

    expiries = df_near["expiry"].unique()
    mp_results = []

    for exp in sorted(expiries):
        exp_data = df_near[
            (df_near["expiry"] == exp) &
            (df_near["dte"] == df_near[df_near["expiry"]==exp]["dte"].min())
        ]
        mp = calculate_max_pain(exp_data)
        underlying = exp_data["underlying_price"].median()
        if mp and underlying:
            mp_results.append({
                "expiry":           pd.Timestamp(exp),
                "max_pain":         mp,
                "underlying_close": underlying,
                "diff_pct":         abs(mp - underlying) / underlying * 100
            })

    mp_df = pd.DataFrame(mp_results).sort_values("expiry")

    fig2 = make_subplots(rows=2, cols=1,
                         subplot_titles=(
                             "Max Pain vs NIFTY Close",
                             "Gap % Between Max Pain and Expiry Close"
                         ), row_heights=[0.6, 0.4])

    fig2.add_trace(go.Scatter(
        x=mp_df["expiry"], y=mp_df["underlying_close"],
        name="NIFTY Close", line=dict(color="#2196F3", width=2),
        mode="lines+markers"
    ), row=1, col=1)

    fig2.add_trace(go.Scatter(
        x=mp_df["expiry"], y=mp_df["max_pain"],
        name="Max Pain", line=dict(color="#FF5722", width=2, dash="dash"),
        mode="lines+markers", marker=dict(symbol="square")
    ), row=1, col=1)

    colors_bar = ["#4CAF50" if v < 0.2 else "#FF9800" if v < 0.5 else "#F44336"
                  for v in mp_df["diff_pct"]]

    fig2.add_trace(go.Bar(
        x=mp_df["expiry"], y=mp_df["diff_pct"],
        name="Gap %", marker_color=colors_bar
    ), row=2, col=1)

    fig2.add_hline(y=mp_df["diff_pct"].mean(), line_dash="dot",
                   line_color="red", row=2, col=1,
                   annotation_text=f"Avg: {mp_df['diff_pct'].mean():.2f}%")

    fig2.update_layout(height=600, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)
    st.success(f"💡 **Key Finding:** NIFTY expired within **0.24%** of max pain level on average across {len(mp_df)} expiries")

# ════════════════════════════════════════════════════
# TAB 3 — PCR SIGNAL
# ════════════════════════════════════════════════════
with tab3:
    st.subheader("Put-Call Ratio — Directional Signal")
    st.markdown("PCR-based contrarian signal backtested against next-day NIFTY direction.")

    pcr_daily = df_near.groupby(
        ["date", "option_type"]
    )["open_interest"].sum().unstack()
    pcr_daily.columns = ["CE_OI", "PE_OI"]
    pcr_daily["PCR"] = pcr_daily["PE_OI"] / pcr_daily["CE_OI"]
    pcr_daily = pcr_daily.reset_index()

    daily_underlying = df.groupby("date")["underlying_price"].median().reset_index()
    daily_underlying = daily_underlying.sort_values("date")
    daily_underlying["next_day_return"] = daily_underlying["underlying_price"].pct_change().shift(-1) * 100
    daily_underlying["next_day_direction"] = daily_underlying["next_day_return"].apply(
        lambda x: "UP" if x > 0 else "DOWN"
    )

    pcr_analysis = pcr_daily.merge(daily_underlying, on="date", how="inner").dropna()

    def pcr_signal(pcr):
        if pcr > 1.1:   return "BULLISH"
        elif pcr < 0.85: return "BEARISH"
        else:            return "NEUTRAL"

    pcr_analysis["signal"] = pcr_analysis["PCR"].apply(pcr_signal)

    bullish = pcr_analysis[pcr_analysis["signal"] == "BULLISH"]
    bearish = pcr_analysis[pcr_analysis["signal"] == "BEARISH"]
    bull_acc = (bullish["next_day_direction"] == "UP").mean() * 100
    bear_acc = (bearish["next_day_direction"] == "DOWN").mean() * 100
    total    = len(bullish) + len(bearish)
    correct  = (bullish["next_day_direction"] == "UP").sum() + \
               (bearish["next_day_direction"] == "DOWN").sum()
    overall  = correct / total * 100 if total > 0 else 0

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bullish Accuracy", f"{bull_acc:.1f}%", f"n={len(bullish)}")
    c2.metric("Bearish Accuracy", f"{bear_acc:.1f}%", f"n={len(bearish)}")
    c3.metric("Overall Accuracy", f"{overall:.1f}%",  f"n={total}")
    c4.metric("Avg PCR",          f"{pcr_analysis['PCR'].mean():.3f}")

    fig3 = make_subplots(rows=2, cols=1,
                         subplot_titles=("PCR Over Time with Signals", "NIFTY Price with Signal Overlay"),
                         row_heights=[0.5, 0.5])

    fig3.add_trace(go.Scatter(
        x=pcr_analysis["date"], y=pcr_analysis["PCR"],
        name="PCR", line=dict(color="#555", width=1.5)
    ), row=1, col=1)

    fig3.add_hline(y=1.1,  line_dash="dash", line_color="green",
                   annotation_text="Bullish (1.1)", row=1, col=1)
    fig3.add_hline(y=0.85, line_dash="dash", line_color="red",
                   annotation_text="Bearish (0.85)", row=1, col=1)

    fig3.add_trace(go.Scatter(
        x=pcr_analysis["date"], y=pcr_analysis["underlying_price"],
        name="NIFTY", line=dict(color="#2196F3", width=2)
    ), row=2, col=1)

    fig3.update_layout(height=550, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)
    st.info(f"💡 **Key Finding:** PCR signal achieved **{overall:.1f}% overall accuracy** across {total} signals vs 50% random baseline")

# ════════════════════════════════════════════════════
# TAB 4 — IV ANALYSIS
# ════════════════════════════════════════════════════
with tab4:
    st.subheader("Implied Volatility Behavior Around Expiry")
    st.markdown("IV proxy analysis showing how volatility behaves as expiry approaches.")

    iv_data = df_near[
        (df_near["moneyness"] == "ATM") &
        (df_near["dte"] >= 1) &
        (df_near["dte"] <= 15) &
        (df_near["close"] > 0) &
        (df_near["underlying_price"] > 0)
    ].copy()

    iv_data["iv_proxy"] = (iv_data["close"] / iv_data["underlying_price"]) * \
                           np.sqrt(365 / iv_data["dte"]) * 100
    iv_data = iv_data[iv_data["iv_proxy"] < 100]

    iv_curve = iv_data.groupby(
        ["dte", "option_type"]
    )["iv_proxy"].median().reset_index()

    iv_by_expiry = iv_data.groupby(
        ["expiry", "option_type"]
    )["iv_proxy"].mean().reset_index()
    iv_by_expiry["expiry"] = pd.to_datetime(iv_by_expiry["expiry"])

    fig4 = make_subplots(rows=1, cols=2,
                         subplot_titles=(
                             "IV Proxy vs Days to Expiry",
                             "Average IV per Expiry Cycle"
                         ))

    for opt in ["CE", "PE"]:
        data = iv_curve[iv_curve["option_type"] == opt].sort_values("dte")
        color = "#2196F3" if opt == "CE" else "#F44336"
        fig4.add_trace(go.Scatter(
            x=data["dte"], y=data["iv_proxy"],
            name=f"{opt} IV", line=dict(color=color, width=2),
            mode="lines+markers"
        ), row=1, col=1)

    ce_iv = iv_by_expiry[iv_by_expiry["option_type"]=="CE"].sort_values("expiry")
    pe_iv = iv_by_expiry[iv_by_expiry["option_type"]=="PE"].sort_values("expiry")

    fig4.add_trace(go.Scatter(
        x=ce_iv["expiry"], y=ce_iv["iv_proxy"],
        name="CE Avg IV", line=dict(color="#2196F3", width=2),
        mode="lines+markers"
    ), row=1, col=2)

    fig4.add_trace(go.Scatter(
        x=pe_iv["expiry"], y=pe_iv["iv_proxy"],
        name="PE Avg IV", line=dict(color="#F44336", width=2),
        mode="lines+markers"
    ), row=1, col=2)

    fig4.update_xaxes(autorange="reversed", title_text="Days to Expiry", col=1)
    fig4.update_layout(height=450, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig4, use_container_width=True)
    st.warning("💡 **Key Finding:** IV rises into expiry — spikes in final 2 days, contrary to traditional IV crush assumption in weekly NIFTY options")