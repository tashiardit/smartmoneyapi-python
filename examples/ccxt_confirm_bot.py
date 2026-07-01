"""Generate a signal with ccxt, confirm it with SmartMoneyAPI before ordering."""
import ccxt
from smartmoneyapi import SmartMoneyClient

sm = SmartMoneyClient()
ex = ccxt.binance()
ohlcv = ex.fetch_ohlcv("BTC/USDT", "1h", limit=50)
closes = [c[4] for c in ohlcv]
direction = "long" if closes[-1] > closes[-20] else "short"   # your strategy here

res = sm.confirm("BTC", direction)
if res["action"].startswith("CONFIRM"):
    print(f"Enter {direction} size x{res['size_mult']} ({res['confidence']})")
    # ex.create_order(...)  # place your real order, scaled by size_mult
else:
    print(f"SmartMoneyAPI says {res['action']}:", res["reasons"])  # VETO_SKIP / NO_DATA_SKIP
# Not financial advice. Crypto trading involves risk.
