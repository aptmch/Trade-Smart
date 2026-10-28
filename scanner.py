from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

NIFTY500_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"

def get_symbols():
    table = pd.read_csv(NIFTY500_URL)
    col = next((c for c in table.columns if c.strip().lower() in ("symbol", "ticker")), None)
    if col is None:
        raise ValueError("Could not find the Symbol column in the Nifty 500 constituents file.")
    return sorted(set(s.strip() + ".NS" for s in table[col].dropna().astype(str)))

def _extract(data, ticker, multi):
    try:
        if multi:
            if ticker not in data.columns.get_level_values(0):
                return pd.DataFrame()
            frame = data[ticker].copy()
        else:
            frame = data.copy()
        return frame.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).sort_index()
    except Exception:
        return pd.DataFrame()

def _indicators(frame):
    x = frame.copy()
    c = x["Close"].astype(float)
    x["EMA5"] = c.ewm(span=5, adjust=False).mean()
    x["EMA20"] = c.ewm(span=20, adjust=False).mean()
    x["EMA50"] = c.ewm(span=50, adjust=False).mean()
    x["EMA200"] = c.ewm(span=200, adjust=False).mean()
    x["ATR14"] = (pd.concat([
        x["High"] - x["Low"],
        (x["High"] - x["Close"].shift()).abs(),
        (x["Low"] - x["Close"].shift()).abs()
    ], axis=1).max(axis=1).rolling(14).mean())
    x["Vol20"] = x["Volume"].rolling(20).mean()
    x["High20"] = x["High"].rolling(20).max().shift(1)
    x["High50"] = x["High"].rolling(50).max().shift(1)
    return x

def _candidate(symbol, frame, timeframe):
    x = _indicators(frame).dropna(subset=["ATR14", "EMA20", "EMA50"])
    if len(x) < 55:
        return None
    r = x.iloc[-1]
    prev = x.iloc[-2]
    close = float(r["Close"])
    atr = float(r["ATR14"])
    if close <= 0 or atr <= 0:
        return None
    trend = bool(r["EMA20"] > r["EMA50"])
    volume_ok = float(r["Volume"]) >= 100000
    # Long-only candidate plans: breakout trigger, stop below nearby support/ATR,
    # targets are risk multiples. These are conditional levels, not promises.
    if timeframe == "Intraday (next session)":
        trigger = max(float(r["High"]), float(r["High20"]) if pd.notna(r["High20"]) else float(r["High"])) * 1.001
        stop = min(float(r["Low"]), trigger - 0.8 * atr)
        strategy = "Next-session opening-range/breakout plan"
        rationale = "Daily trend and momentum filters; entry only if price breaks above the trigger."
    elif timeframe == "Weekly swing":
        trigger = max(float(r["High"]), float(r["High20"]) if pd.notna(r["High20"]) else float(r["High"])) * 1.002
        stop = max(0.01, min(float(r["Low"]), trigger - 1.5 * atr))
        strategy = "Weekly breakout candidate"
        rationale = "Daily EMA20 above EMA50 with price-strength confirmation; wait for breakout."
    else:
        trigger = max(float(r["High"]), float(r["High50"]) if pd.notna(r["High50"]) else float(r["High"])) * 1.003
        stop = max(0.01, min(float(r["Low"]), trigger - 2.0 * atr))
        strategy = "Monthly trend / base breakout candidate"
        rationale = "Longer lookback breakout with positive trend; use smaller position size for wider stop."
    risk = trigger - stop
    if risk <= 0 or risk / trigger > 0.12:
        return None
    target1 = trigger + risk * 2
    target2 = trigger + risk * 3
    day_change = (close / float(prev["Close"]) - 1) * 100 if float(prev["Close"]) else 0
    # Avoid returning every ticker: require trend, liquidity, and a close near/above a short-term reference.
    if not (trend and volume_ok and close >= 50 and day_change > -1.5):
        return None
    return {
        "Symbol": symbol.replace(".NS", ""),
        "Timeframe": timeframe,
        "As of": x.index[-1].strftime("%Y-%m-%d"),
        "Last close (₹)": round(close, 2),
        "Entry trigger (₹)": round(trigger, 2),
        "Stop-loss (₹)": round(stop, 2),
        "Target 1 (₹, 2R)": round(target1, 2),
        "Target 2 (₹, 3R)": round(target2, 2),
        "Risk per share (₹)": round(risk, 2),
        "Day change (%)": round(day_change, 2),
        "Volume": int(float(r["Volume"])),
        "Setup": strategy,
        "Reason / trigger": rationale,
    }

def scan_market(universe_limit=None):
    symbols = get_symbols()
    if universe_limit:
        symbols = symbols[:int(universe_limit)]
    data = yf.download(
        tickers=symbols, period="5y", interval="1d", group_by="ticker",
        auto_adjust=False, progress=False, threads=True, timeout=30
    )
    if data is None or data.empty:
        raise RuntimeError("No price data received. Check the internet connection or retry later.")
    multi = isinstance(data.columns, pd.MultiIndex)
    day_rows, week_rows, month_rows = [], [], []
    checked = 0
    for ticker in symbols:
        frame = _extract(data, ticker, multi)
        if len(frame) < 210:
            continue
        checked += 1
        # Next-session intraday plan is generated from completed daily bars after close.
        candidate = _candidate(ticker, frame, "Intraday (next session)")
        if candidate:
            day_rows.append(candidate)
        weekly = frame.resample("W-FRI").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
        }).dropna()
        candidate = _candidate(ticker, weekly, "Weekly swing")
        if candidate:
            week_rows.append(candidate)
        monthly = frame.resample("M").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
        }).dropna()
        candidate = _candidate(ticker, monthly, "Monthly swing")
        if candidate:
            month_rows.append(candidate)
    def frame(rows):
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(["Day change (%)"], ascending=False).reset_index(drop=True)
        return df
    return {
        "intraday": frame(day_rows),
        "weekly": frame(week_rows),
        "monthly": frame(month_rows),
        "checked": checked,
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
