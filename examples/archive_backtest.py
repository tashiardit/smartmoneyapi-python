"""Pull the public archive — no API key required.

The federated archive holds 115,706,185 rows across 9 tables back to
2026-03-18 (measured against /v1/history/coverage on 2026-08-28). Verify that
for yourself with step 1 rather than taking this comment's word for it.
"""
from smartmoneyapi import SmartMoneyClient, SmartMoneyError

c = SmartMoneyClient()   # keyless

# 1) What is in there, and how far back.
cov = c.history_coverage()["tables"]
total = sum((t.get("live") or {}).get("rows", 0) +
            (t.get("archive") or {}).get("rows", 0) for t in cov.values())
print(f"{total:,} rows across {len(cov)} tables")
for name, t in sorted(cov.items()):
    print(f"  {name:22} filterable={t.get('filterable')}")

# 2) Read one table across the live DB and the cold archive in one call.
#    `sources` names every shard the answer came from; `truncated` says whether
#    you hit the row cap (max 5000 per call — page with `until`).
rows = c.history("whale_positions", symbol="BTC", days=7, limit=1000)
print(f"{rows['count']} rows, truncated={rows['truncated']}, "
      f"sources={[s['source'] for s in rows['sources']]}")

# 3) A filter the archive cannot serve from an index is REJECTED, not dropped —
#    a dropped filter would answer a wider question than you asked while looking
#    like a valid result.
try:
    c.history("whale_positions", direction="long", days=200)
except SmartMoneyError as e:
    print("rejected as designed:", e.body["message"])
