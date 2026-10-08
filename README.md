# smartmoneyapi — Python client

Thin client for [SmartMoneyAPI](https://smartmoneyapi.com): cross-exchange
derivatives, whale positioning, executed liquidation feeds, options, ETF flows,
on-chain metrics, and a keyless deep archive.

```bash
pip install smartmoneyapi
```

**Most of this works without an API key.** Construct the client with no
arguments and every keyless endpoint answers, at a reduced row cap and a per-IP
throttle.

```python
from smartmoneyapi import SmartMoneyClient

client = SmartMoneyClient()                       # no key
cov = client.history_coverage()                   # what the archive holds
heat = client.liquidation_heatmap("BTC")          # executed liquidations
rows = client.history("whale_positions", symbol="BTC", days=7, limit=500)
```

With a key you also get trade confirmation, the full liquidation book, and the
paid feeds:

```python
client = SmartMoneyClient("sm_xxxxxxxxxxxx")      # or set SMARTMONEY_API_KEY
res = client.confirm("BTC", "long")

if res["action"] == "NO_DATA_SKIP":
    ...            # explicit "nothing measured for this symbol" — not a weak read
elif res["action"].startswith("CONFIRM"):
    size = base_size * res["size_mult"]
else:
    ...            # VETO_SKIP — stand aside
```

`composite` runs −1.0 → +1.0 and is a multi-factor confluence read, **not** a
win-rate.

## Design

- **Nothing is reshaped.** Each method returns the API's own JSON, so the
  published contract describes exactly what you hold.
- **Keys are optional, and enforced early.** A method that needs a key raises
  `SmartMoneyError` *before* the request instead of letting the server 401.
- **Errors carry the server's answer.** `SmartMoneyError` exposes `.status` and
  `.body`, so a rejected archive filter tells you which filters are supported.
- **No release needed for a new endpoint.** `client.get("/v1/anything", **params)`
  reaches any documented GET.

## What it covers

| Area | Methods |
|---|---|
| Trade confirmation | `confirm`, `smart_stop` |
| Liquidations | `liquidations`, `liquidation_heatmap`, `liquidation_symbols`, `simulate_liquidations`, `onchain_liquidations` |
| Deep archive (keyless) | `history_coverage`, `history` |
| Whales | `whale_events`, `whale_consensus`, `whale_summary`, `whale_crowding`, `wallet_profile` |
| Derivatives | `screener`, `funding_heatmap`, `funding_arb`, `smart_money_flow` |
| Signals & track record | `recent_signals`, `signal_performance`, `track_record`, `stats` |
| Market data | `onchain_metrics`, `options_chain`, `options_gex`, `etf_flows`, `market_indices`, `news`, `fear_greed`, `seasonality`, `stocks`, `symbols`, `plans` |
| Status | `health`, `node_health` |
| Your account | `usage`, `list_alerts`, `create_alert`, `delete_alert`, `alert_history`, `register_webhook` |

The account methods act on your account rather than returning market data, which
is why they are documented at <https://smartmoneyapi.com/docs> and deliberately
left out of the public OpenAPI mirror. They are here because a client is the
right place to call them from.

## The deep archive is public

`client.history(table, ...)` federates the live database and the consolidated
cold archive into one newest-first response. Measured against
`/v1/history/coverage` on 2026-08-28: **115,706,185 rows across 9 tables**,
oldest row **2026-03-18**. It is still accruing, so treat that count as a
floor and re-read the endpoint for the current figure.

```python
rows = client.history("whale_positions", symbol="BTC", days=30, limit=5000)
print(rows["count"], rows["truncated"], rows["sources"])
```

`sources` names every shard the answer came from. A filter the archive cannot
serve from an index raises `SmartMoneyError` with HTTP 400 naming the ones it
can — the query is never silently widened into a different question.

## Verified, not illustrated

Every field name in this README and in the docstrings was observed on a real
response on **2026-08-28**; the 29 keyless methods were each called against the
live API on that date. Where a shape could not be verified, the docstring says
what it does not know rather than filling the gap.

## Version

`1.2.1` — written against the published contract dated `2026-08-28`; no method calls a retired route
(`smartmoneyapi.SPEC_VERSION`).

## Links

- Machine-readable contract: <https://github.com/tashiardit/smartmoneyapi-docs>
- Interactive docs: <https://smartmoneyapi.com/docs>
- Get a key: <https://smartmoneyapi.com/signup>
- Pricing: <https://smartmoneyapi.com/pricing>

> Not financial advice. Crypto trading involves substantial risk, including loss
> of capital. Past signal accuracy does not guarantee future results.

## License

MIT
