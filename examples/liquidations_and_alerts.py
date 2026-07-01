"""New in v1.1 — real liquidation feeds, on-chain DeFi liqs, alerts, webhooks."""
from smartmoneyapi import SmartMoneyClient, verify_webhook_signature

c = SmartMoneyClient()  # reads SMARTMONEY_API_KEY (X-API-Key auth)

# 1) REAL executed liquidation heatmap (Binance/OKX/Bybit/Bitget/BitMEX)
liq = c.get_liquidations("BTC")
rh = liq.get("realized_heatmap")            # may be absent in a very calm market
if rh:
    print("Executed BTC liqs (24h window):", rh["totals"])
print("Leverage-projected cascade risk:", liq.get("cascade_risk"))

# 2) Executed on-chain DeFi lending liquidations (Trader+), from local BSC/AVAX nodes
oc = c.get_onchain_liquidations(chain="bsc", limit=20)
print(f"{oc['count']} recent BSC lending liquidations")
for row in oc["liquidations"][:3]:
    print(" ", row["protocol"], row.get("repay_usd"), row["tx_hash"])

# 3) Custom alert (Pro): notify when BTC 8h funding spikes above 5 bps
#    Metrics/operators: see c.list_alerts()["available_metrics" / "available_operators"]
# created = c.create_alert("BTC funding spike", "funding_rate", "gt", 0.05, symbol="BTC")

# 4) Register an HMAC-signed outbound webhook (Pro)
# wh = c.register_webhook("https://yourapp.com/hook", ["HIGH", "MEDIUM"], ["BTC", "ETH"],
#                         secret="a-long-random-secret-16+chars")

# Verifying a delivery on your receiver (Flask-style):
#   sig = request.headers["X-SmartMoney-Signature"]
#   ok = verify_webhook_signature(request.get_data(), sig, "a-long-random-secret-16+chars")

# Not financial advice. Crypto trading involves risk.
