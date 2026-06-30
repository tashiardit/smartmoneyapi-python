# smartmoneyapi-python

Tiny Python client for **[SmartMoneyAPI](https://smartmoneyapi.com)** — the trade confirmation API for crypto bots. Confirm a long/short idea against derivatives, funding, open interest, liquidations, and whale positioning before your bot enters.

```bash
pip install requests   # (client is dependency-light)
export SMARTMONEY_API_KEY=sm_your_key   # get one free at https://smartmoneyapi.com/signup
```

```python
from smartmoneyapi import SmartMoneyClient
c = SmartMoneyClient()                 # reads SMARTMONEY_API_KEY
res = c.confirm("BTC", "long")
print(res["action"], res["confidence"], res["size_multiplier"])
```

- Docs: https://smartmoneyapi.com/docs · Performance: https://smartmoneyapi.com/performance · Pricing: https://smartmoneyapi.com/pricing
- `action` ∈ `CONFIRM` / `REDUCE` / `SKIP`; `confidence` ∈ `HIGH` / `MEDIUM` / `LOW`.

> Not financial advice. Crypto trading involves substantial risk. Past signal accuracy does not guarantee future results.

## License
MIT
