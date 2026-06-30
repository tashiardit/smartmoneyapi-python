"""Generate a signal with ccxt, confirm it with SmartMoneyAPI before ordering."""
import ccxt
from smartmoneyapi import SmartMoneyClient

sm = SmartMoneyClient()
ex = ccxt.binance()
ohlcv = ex.fetch_ohlcv("BTC/USDT", "1h", limit=50)
closes = [c[4] for c in ohlcv]
direction = "long" if closes[-1] > closes[-20] else "short"   # your strategy here

res = sm.confirm("BTC", direction)
if res["action"] != "SKIP":
    print(f"Enter {direction} size x{res['size_multiplier']} ({res['confidence']})")
    # ex.create_order(...)  # place your real order, scaled by size_multiplier
else:
    print("SmartMoneyAPI says SKIP:", res["reasons"])
# Not financial advice. Crypto trading involves risk.
