from pathlib import Path
import pandas as pd
import streamlit as st
from scanner import scan_market

st.set_page_config(page_title="Trade Companion", page_icon="📈", layout="centered")
st.markdown("""
<style>
.block-container{padding-top:1rem;padding-bottom:2rem;max-width:950px}
div[data-testid="stMetric"]{background:#f2f5fa;padding:12px;border-radius:12px}
.stButton button,.stDownloadButton button{width:100%;min-height:44px}
</style>
""", unsafe_allow_html=True)

st.title("📈 Trade Companion")
st.caption("NSE · Intraday plan + weekly and monthly swing candidates")
st.info("The scheduled scan is designed for 3:50 PM India time on weekdays. The intraday section creates a plan for the NEXT session from completed daily candles; it does not scan live intraday prices after the market closes.")

with st.expander("⚙️ Scan settings", expanded=False):
    limit = st.selectbox("Universe", ["Nifty 500", "First 100 symbols (quick test)"], index=0)
    st.caption("The quick-test universe is alphabetical and is for testing only, not a representative market scan.")

run = st.button("🔎 Scan now", type="primary")
show_latest = st.button("📄 Show latest scheduled results")

if run:
    try:
        with st.spinner("Downloading daily prices and calculating three trading plans… This may take several minutes."):
            results = scan_market(100 if limit.startswith("First 100") else None)
        st.session_state["results"] = results
        st.session_state["source"] = "Manual scan"
    except Exception as exc:
        st.error(f"Scan failed: {exc}. Data providers may be temporarily unavailable or rate-limited.")

if show_latest:
    loaded = {}
    for key, fname in [("intraday","intraday_candidates.csv"),("weekly","weekly_candidates.csv"),("monthly","monthly_candidates.csv")]:
        p = Path(fname)
        if p.exists():
            loaded[key] = pd.read_csv(p)
    if loaded:
        summary = Path("scan_summary.txt")
        st.session_state["results"] = {
            **loaded,
            "checked": "Scheduled run",
            "run_utc": summary.read_text(encoding="utf-8") if summary.exists() else "Latest saved report",
        }
        st.session_state["source"] = "Latest scheduled scan"
    else:
        st.warning("No scheduled results found yet. Run the GitHub Actions workflow once after setup.")

if "results" in st.session_state:
    res = st.session_state["results"]
    st.caption(f"{st.session_state.get('source','Results')} · {res.get('run_utc','')}")
    st.metric("Stocks with enough history", res.get("checked", "—"))
    tabs = st.tabs(["Intraday — next session", "Weekly swing", "Monthly swing"])
    for tab, key, title in zip(tabs, ["intraday","weekly","monthly"], ["Intraday candidates", "Weekly swing candidates", "Monthly swing candidates"]):
        with tab:
            df = res.get(key, pd.DataFrame())
            st.subheader(title)
            if df is None or df.empty:
                st.warning("No stocks matched the current candidate rules in this category.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button(f"Download {key} CSV", df.to_csv(index=False).encode("utf-8"),
                                   f"{key}_candidates.csv", "text/csv", key=f"download_{key}")
else:
    st.subheader("What each plan shows")
    st.markdown("""
- **Entry trigger:** conditional price level; do not buy before it triggers.
- **Stop-loss:** a risk-control level, not a guaranteed execution price.
- **Target 1 / Target 2:** calculated at 2R and 3R (two or three times the entry-to-stop risk).
- **Intraday:** levels prepared after market close for the next trading session.
- **Weekly / monthly:** trend and breakout candidates from resampled daily history.
""")

st.divider()
st.warning("Educational screening tool only. These are algorithmic candidates, not personalized financial advice or guaranteed profitable trades. Third-party data can be delayed, missing or inaccurate. Verify price levels with your broker before trading. Gap risk can cause execution beyond a stop.")
st.caption("Data source: Yahoo Finance via yfinance and Nifty Indices constituent CSV. Not an official NSE feed.")
