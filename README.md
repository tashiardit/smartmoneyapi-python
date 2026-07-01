# smartmoneyapi-python

Tiny Python client for **[SmartMoneyAPI](https://smartmoneyapi.com)** — the trade confirmation API for crypto bots. Confirm a long/short idea against derivatives, funding, open interest, liquidations, and whale positioning before your bot enters.

```bash
pip install requests   # (client is dependency-light)
export SMARTMONEY_API_KEY=sm_your_key   # get one free at https://smartmoneyapi.com/signup
```

```python
from smartmoneyapi import SmartMoneyClient
c = SmartMoneyClient()                 # reads SMARTMONEY_API_KEY (X-API-Key auth)
res = c.confirm("BTC", "long")
print(res["action"], res["confidence"], res["size_mult"])

# New in v1.1:
c.get_liquidations("BTC")              # levels + REAL executed-liq heatmap (multi-exchange)
c.get_onchain_liquidations("bsc")      # executed DeFi lending liqs (Venus/AAVE/…) — Trader+
c.create_alert("BTC funding spike", "funding_rate", "gt", 0.05)   # Pro
c.register_webhook("https://you/hook", ["HIGH","MEDIUM"], ["BTC"], "a-long-secret")  # Pro
```

- Docs: https://smartmoneyapi.com/docs · Performance: https://smartmoneyapi.com/performance · Pricing: https://smartmoneyapi.com/pricing
- `action` ∈ `CONFIRM_FULL` / `CONFIRM_REDUCED` / `CONFIRM_MINIMAL` / `VETO_SKIP` / `NO_DATA_SKIP`; `confidence` ∈ `HIGH` / `MEDIUM` / `LOW` / `VETO` / `NO_DATA`. `composite` runs -1.0→+1.0 (a confluence read, **not** a win-rate).
- Outbound webhooks are HMAC-SHA256 signed (`X-SmartMoney-Signature`); verify with `verify_webhook_signature(raw_body, header, secret)`.

> Not financial advice. Crypto trading involves substantial risk. Past signal accuracy does not guarantee future results.

## License
MIT
