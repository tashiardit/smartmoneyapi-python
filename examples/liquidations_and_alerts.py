"""Liquidations — the keyless feeds first, then the keyed ones.

Every field read below was observed on a real response on 2026-08-28.
"""
from smartmoneyapi import SmartMoneyClient, SmartMoneyError

pub = SmartMoneyClient()   # no key needed for steps 1-3

# 1) Executed forced liquidations, bucketed by price x time.
heat = pub.liquidation_heatmap("BTC")
print(f"{heat['symbol']}: {heat['price_buckets']} price buckets over "
      f"{heat['window_minutes']} min, {heat['price_min']}-{heat['price_max']}")

# 2) Which symbols have a realized feed at all, and how deep it runs.
for s in pub.liquidation_symbols()["symbols"][:5]:
    print(f"  {s['symbol']}: {s['count']} events, ${s['total_notional']:,.0f}")

# 3) What a move would trigger. `oi_band_status` reports "ok" or "split_assumed"
#    per venue, and `by_exchange[venue]['split_measured']` says whether the
#    long/short split was measured — an assumed split is never dressed up as one.
sim = pub.simulate_liquidations("BTC")
print(f"cascade_risk={sim['cascade_risk']} depth={sim['cascade_depth']} "
      f"triggered=${sim['triggered_notional_usd']:,.0f} "
      f"oi_bands={sim['oi_band_status']}")

# 4) The full book. Needs a Trader+ key. `withheld` / `withheld_reason` report
#    what your tier does not include, rather than silently truncating the ladder.
keyed = SmartMoneyClient()   # raises if SMARTMONEY_API_KEY is unset
try:
    liq = keyed.liquidations("BTC")
    print("oi_split_source:", liq.get("oi_split_source"),
          "bands_status:", liq.get("bands_status"),
          "withheld:", liq.get("withheld"), liq.get("withheld_reason"))
except SmartMoneyError as e:
    print("needs a key or a higher tier:", e)

# 5) Alerts and webhooks (Pro). Metrics and operators come from the API itself:
#    keyed.list_alerts()["available_metrics"] / ["available_operators"]
# created = keyed.create_alert("BTC funding spike", "funding_rate", "gt", 0.05)
# wh = keyed.register_webhook("https://yourapp.example/hook",
#                             ["HIGH", "MEDIUM"], ["BTC", "ETH"],
#                             secret="a-long-random-secret-16+chars")
#
# Verifying a delivery on your receiver (Flask-style):
#   from smartmoneyapi import verify_webhook_signature
#   ok = verify_webhook_signature(request.get_data(),           # raw bytes
#                                 request.headers["X-SmartMoney-Signature"],
#                                 "a-long-random-secret-16+chars")
# Not financial advice.
