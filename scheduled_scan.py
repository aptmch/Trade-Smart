from pathlib import Path
from datetime import datetime, timezone
from scanner import scan_market

results = scan_market()
for key, name in [
    ("intraday", "intraday_candidates.csv"),
    ("weekly", "weekly_candidates.csv"),
    ("monthly", "monthly_candidates.csv"),
]:
    results[key].to_csv(name, index=False)
summary = (
    f"Last scheduled scan: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
    f"(GitHub scheduled target is 15:50 India time on weekdays)\\n"
    f"Stocks with sufficient history: {results['checked']}\\n"
    f"Intraday next-session candidates: {len(results['intraday'])}\\n"
    f"Weekly swing candidates: {len(results['weekly'])}\\n"
    f"Monthly swing candidates: {len(results['monthly'])}\\n"
)
Path("scan_summary.txt").write_text(summary, encoding="utf-8")
print(summary)
