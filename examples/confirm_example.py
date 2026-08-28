"""Confirm a trade idea. Needs an API key (the Free tier covers BTC/ETH/SOL)."""
from smartmoneyapi import SmartMoneyClient

c = SmartMoneyClient()          # reads SMARTMONEY_API_KEY
res = c.confirm("BTC", "long")

if res["action"] == "NO_DATA_SKIP":
    # Explicit absence of coverage, NOT a weak or neutral read: the symbol is
    # outside the tracked derivatives/whale universe, so nothing was measured.
    print("no coverage —", res["reasons"][0])
elif res["action"].startswith("CONFIRM"):
    print(f"{res['action']} {res['confidence']} — size x{res['size_mult']} "
          f"(composite {res['composite']})")
    print("coverage:", res["coverage"])   # which legs actually had data
else:
    print(f"{res['action']} —", res["reasons"])
# Not financial advice. `composite` is a confluence read, not a win-rate.
