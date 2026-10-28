TRADE COMPANION — ANDROID-FRIENDLY NSE SCANNER

This package is a phone-friendly web app that can be added to the Android home screen after deployment. It is not a compiled APK and is not already hosted; it requires one-time deployment to your own accounts.

FEATURES
- Nifty 500 universe.
- Separate candidate lists for:
  1. Intraday plan for the NEXT trading session (prepared after close)
  2. Weekly swing
  3. Monthly swing
- Entry trigger, stop-loss, 2R target, 3R target, last close, daily change and volume.
- Manual scan plus GitHub Actions weekday schedule intended for 15:50 India time.
- CSV downloads.

DATA LIMITATION
Uses Yahoo Finance through yfinance and Nifty Indices constituent CSV, not an official NSE data feed. Data can be delayed, incomplete, blocked or rate-limited. GitHub schedule can run late and does not know exchange holidays.

HOW TO DEPLOY (ONE-TIME)
1. Create/sign into GitHub: https://github.com
2. Create a repository, e.g. trade-companion.
3. Upload every file and folder from this ZIP, preserving .github/workflows/daily-scan.yml.
4. In repository Settings → Actions → General, allow GitHub Actions read/write access to repository contents.
5. Open Actions → Daily NSE trading plans → Run workflow to test.
6. Open https://share.streamlit.io/, sign in with GitHub, deploy your repository with main file path app.py.
7. Open the deployed Streamlit URL in Chrome on Android. Chrome menu (⋮) → Add to Home screen (wording may vary).

SCHEDULE
GitHub cron target: 10:20 UTC = 15:50 IST, Monday–Friday. Scheduled tasks can be delayed, may run on exchange holidays, and are not guaranteed to execute at exactly 15:50.

TRADING-LEVEL DEFINITIONS
Entry is a conditional breakout trigger above a recent high. Stop is below a recent low / ATR-based level. Targets are calculated at 2R and 3R. The intraday plan is for the next session because the scan is run after the close; it does not provide same-day live intraday entries. These are screening candidates, not personalized recommendations or guarantees. Verify levels with a broker and consider gap risk, slippage, position size, and risk tolerance.
