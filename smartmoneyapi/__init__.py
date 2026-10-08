"""SmartMoneyAPI Python client.

Thin, dependency-light wrapper over https://api.smartmoneyapi.com. Every method
maps to one documented endpoint; nothing is reshaped or renamed on the way
through, so what you get back is exactly what the API returned and the published
contract (github.com/tashiardit/smartmoneyapi-docs) describes it.

Most of this surface needs NO key: construct the client with no arguments and
the keyless endpoints work at a reduced row cap and a per-IP throttle. Methods
that require a key say so, and raise before the request if you have not set one.

Not financial advice. `composite` is a multi-factor confluence read, not a
win-rate; past signal accuracy does not guarantee future results.
"""
import os

import requests

__all__ = ["SmartMoneyClient", "SmartMoneyError", "verify_webhook_signature"]
__version__ = "1.2.1"

#: Contract this client was generated against.
SPEC_VERSION = "2026-08-28"


class SmartMoneyError(RuntimeError):
    """An API call failed. `status` and `body` carry the server's own answer."""

    def __init__(self, status, body, path):
        self.status, self.body, self.path = status, body, path
        msg = body.get("message") or body.get("error") if isinstance(body, dict) else body
        super().__init__(f"{path} -> HTTP {status}: {msg}")


class SmartMoneyClient:
    """Client for the SmartMoneyAPI.

        >>> SmartMoneyClient().history_coverage()          # no key needed
        >>> SmartMoneyClient("sm_xxxxxxxxxxxx").confirm("BTC", "long")

    With no `api_key` argument the environment variable ``SMARTMONEY_API_KEY``
    is used when it is set, and the client stays usable without one.
    """

    def __init__(self, api_key=None, base="https://api.smartmoneyapi.com",
                 timeout=30, session=None):
        self.api_key = api_key or os.environ.get("SMARTMONEY_API_KEY")
        self.base = base.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    # ---------------------------------------------------------------- plumbing
    def _headers(self):
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def _need_key(self, path):
        if not self.api_key:
            raise SmartMoneyError(
                0, {"message": "this endpoint needs an API key; pass api_key= "
                               "or set SMARTMONEY_API_KEY"}, path)

    def _request(self, method, path, params=None, body=None):
        r = self._session.request(
            method, self.base + path, params=params, json=body,
            headers=self._headers(), timeout=self.timeout)
        if not r.ok:
            try:
                detail = r.json()
            except ValueError:
                detail = r.text[:500]
            raise SmartMoneyError(r.status_code, detail, path)
        return r.json()

    def get(self, path, **params):
        """Call any documented GET endpoint directly.

        The escape hatch: this client does not need a new release for you to
        reach an endpoint it has no named method for.

            >>> client.get("/v1/seasonality/dow", symbol="ETH")
        """
        return self._request("GET", path, params={k: v for k, v in params.items()
                                                  if v is not None})

    # ------------------------------------------------------- trade confirmation
    def confirm(self, symbol, direction, account_size=None):
        """Confirm / reduce / skip a trade idea. Needs a key (Free tier: BTC, ETH, SOL).

        ``direction`` is ``"long"`` or ``"short"``. The response carries
        ``action`` — ``CONFIRM_FULL`` / ``CONFIRM_REDUCED`` / ``CONFIRM_MINIMAL``
        (take it, at ``size_mult`` size), ``VETO_SKIP`` (stand aside), or
        ``NO_DATA_SKIP``, which means nothing was measured for that symbol and is
        an explicit absence of coverage, NOT a weak or neutral read — alongside
        ``confidence``, ``composite`` (-1.0 .. 1.0) and ``size_mult``.
        """
        self._need_key("/v1/confirm")
        return self.get("/v1/confirm", symbol=symbol, direction=direction,
                        account_size=account_size)

    def smart_stop(self, symbol, direction, entry_price=None, risk_pct=None):
        """Stop-loss and take-profit placement around measured liquidation
        clusters. Needs a Trader+ key.

        When a level cannot be measured the response withholds it and says why
        in ``withheld`` / ``withheld_reason`` rather than returning a modelled
        number that would read as measured.
        """
        self._need_key("/v1/smart-stop")
        return self.get("/v1/smart-stop", symbol=symbol, direction=direction,
                        entry_price=entry_price, risk_pct=risk_pct)

    # ----------------------------------------------------------- liquidations
    def liquidations(self, symbol="BTC"):
        """Full liquidation picture for one symbol. Needs a Trader+ key.

        Carries both the realized feed (``realized_heatmap``, ``realized_totals``,
        ``realized_by_side``) and the projected book, each labelled with where it
        came from: ``oi_split_source`` and ``bands_status`` say whether the open
        interest split was measured or assumed, ``nearest_symmetric`` /
        ``nearest_basis`` / ``nearest_status`` describe the nearest-band
        calculation, and ``withheld`` / ``withheld_reason`` / ``level_depth``
        report what your tier does not include instead of silently truncating.
        """
        self._need_key("/v1/liquidations")
        return self.get("/v1/liquidations", symbol=symbol)

    def liquidation_heatmap(self, symbol="BTC", window_minutes=None,
                            price_buckets=None):
        """Executed forced liquidations bucketed by price x time. No key needed.

        Returns ``price_levels``, ``time_buckets`` and the matrix between them,
        plus ``price_min`` / ``price_max`` / ``price_bucket_size``.
        """
        return self.get("/v1/liquidations/heatmap", symbol=symbol,
                        window_minutes=window_minutes, price_buckets=price_buckets)

    def liquidation_symbols(self):
        """Symbols with a realized liquidation feed, with per-symbol ``count``,
        ``total_notional`` and first/last event timestamps. No key needed."""
        return self.get("/v1/liquidations/symbols")

    def simulate_liquidations(self, symbol="BTC", move_pct=None):
        """What a price move would trigger. No key needed.

        ``by_exchange`` carries ``split_measured`` per venue and ``oi_band_status``
        says ``ok`` or ``split_assumed`` per exchange, so an assumed long/short
        split is never presented as a measured one.
        """
        return self.get("/v1/liquidations/simulate", symbol=symbol,
                        move_pct=move_pct)

    def onchain_liquidations(self, chain=None, limit=100):
        """Executed on-chain DeFi lending liquidations. Needs a Trader+ key.

        ``chain``: ``"bsc"``, ``"avax"``, or None for all.
        """
        self._need_key("/v1/liquidations/onchain")
        return self.get("/v1/liquidations/onchain", chain=chain, limit=limit)

    # --------------------------------------------------------- deep history
    #: Tables reachable through :meth:`history`.
    HISTORY_TABLES = ("whale_positions", "confirmations", "signal_log",
                      "derivatives_agg", "whale_consensus", "derivatives",
                      "onchain", "signal_outcomes", "wallet_relationships")

    def history_coverage(self):
        """How far back each archive table reaches, and how many rows it holds.

        No key needed. Measured 2026-08-28: 115,706,185 rows across 9 tables,
        oldest row 2026-03-18.
        """
        return self.get("/v1/history/coverage")

    def history(self, table, days=None, since=None, until=None, limit=None,
                **filters):
        """Federated newest-first read across the live DB and the cold archive.

        No key needed. ``table`` must be one of :attr:`HISTORY_TABLES`.
        ``since`` / ``until`` are epoch seconds and map to the API's ``from`` /
        ``to``. ``sources`` in the response names every shard the answer came
        from and ``truncated`` says whether you hit the row cap.

        A filter the archive cannot serve from an index is rejected with HTTP
        400 naming the ones it can, which surfaces here as
        :class:`SmartMoneyError` — the query is never silently widened.
        """
        if table not in self.HISTORY_TABLES:
            raise ValueError(f"unknown table {table!r}; "
                             f"expected one of {', '.join(self.HISTORY_TABLES)}")
        return self.get(f"/v1/history/{table}", days=days, limit=limit,
                        **{"from": since, "to": until}, **filters)

    # -------------------------------------------------------------- whales
    def whale_events(self, limit=None, hours=None, chain=None):
        """Recent large on-chain whale transfers and swaps. No key needed."""
        return self.get("/v1/whales/events", limit=limit, hours=hours, chain=chain)

    def whale_consensus(self):
        """Aggregate whale positioning, with a per-chain ``chain_flows``
        breakdown. No key needed."""
        return self.get("/v1/whale-consensus")

    def whale_summary(self):
        """Whale-flow summary: ``net_flows``, ``top_movers``, ``critical_24h``,
        and ``sources_contributing`` / ``sources_silent`` so you can tell a quiet
        market from a dead feed. No key needed."""
        return self.get("/v1/whales/summary")

    def whale_crowding(self, symbol=None):
        """How crowded whale positioning is. No key needed."""
        return self.get("/v1/whales/crowding", symbol=symbol)

    def wallet_profile(self, address):
        """Profile of one whale wallet. No key needed."""
        return self.get(f"/v1/wallet/{address}/profile")

    # --------------------------------------------------------- derivatives
    def screener(self, sort_by=None, direction=None, limit=None):
        """Cross-exchange derivatives screener. No key needed (top rows only
        without a key; a key returns the full set)."""
        return self.get("/v1/screener", sort_by=sort_by, direction=direction,
                        limit=limit)

    def funding_heatmap(self):
        """Funding rates across venues and symbols. No key needed."""
        return self.get("/v1/derivatives/funding-heatmap")

    def funding_arb(self, min_spread=None):
        """Cross-venue funding-rate arbitrage scanner. Needs a Trader+ key."""
        self._need_key("/v1/funding-arb")
        return self.get("/v1/funding-arb", min_spread=min_spread)

    def smart_money_flow(self, symbol=None):
        """Net smart-money flow. Needs a Trader+ key."""
        self._need_key("/v1/smart-money/flow")
        return self.get("/v1/smart-money/flow", symbol=symbol)

    # -------------------------------------------- signals, stats, market data
    def recent_signals(self, limit=None, symbol=None):
        """The live signal feed. No key needed."""
        return self.get("/v1/signals/recent", limit=limit, symbol=symbol)

    def signal_performance(self, days=None, symbol=None):
        """Resolved signal outcomes by horizon. No key needed."""
        return self.get("/v1/signals/performance", days=days, symbol=symbol)

    def track_record(self, horizon=None, confidence=None):
        """Forward-test track record, including ``curves_net_fees_slip`` — the
        curve after fees and slippage, which is the one worth reading. No key
        needed."""
        return self.get("/v1/performance/track-record", horizon=horizon,
                        confidence=confidence)

    def stats(self):
        """Headline accuracy statistics, with their sample sizes. No key needed."""
        return self.get("/v1/stats")

    def plans(self):
        """Live pricing and per-tier limits, straight from the pricing manifest.
        No key needed."""
        return self.get("/v1/plans")

    def symbols(self):
        """Every tracked symbol. No key needed."""
        return self.get("/v1/symbols")

    def onchain_metrics(self):
        """TVL, stablecoins, DEX volumes, BTC chain stats, gas. No key needed."""
        return self.get("/v1/onchain/metrics")

    def options_chain(self, symbol="BTC"):
        """Deribit options chain: put/call ratio, max pain, OI by strike. No key
        needed."""
        return self.get("/v1/options/chain", symbol=symbol)

    def options_gex(self, symbol="BTC"):
        """Gamma exposure profile, with ``gamma_flip`` and ``gex_regime``. No key
        needed."""
        return self.get("/v1/options/gex", symbol=symbol)

    def etf_flows(self, asset="BTC"):
        """Daily spot-ETF flows and per-fund breakdown. No key needed."""
        return self.get("/v1/etf/flows", asset=asset)

    def market_indices(self):
        """Altcoin season index, BTC dominance, CME basis. No key needed."""
        return self.get("/v1/market/indices")

    def news(self, category=None, hours=None):
        """Classified crypto / geopolitical news feed. No key needed."""
        return self.get("/v1/news/general", category=category, hours=hours)

    def fear_greed(self):
        """Fear & Greed index with its 7-day trend. No key needed."""
        return self.get("/v1/news/fear-greed")

    def seasonality(self, symbol="BTC", timeframe=None):
        """Month-of-year seasonality with per-year returns. No key needed."""
        return self.get("/v1/seasonality", symbol=symbol, timeframe=timeframe)

    def stocks(self):
        """Tracked equities universe and its signals. No key needed."""
        return self.get("/v1/stocks")

    def health(self):
        """Gateway health. No key needed."""
        return self.get("/v1/health")

    def node_health(self):
        """Health of the self-hosted BSC / Avalanche nodes behind the RPC
        product. No key needed."""
        return self.get("/v1/node/health")

    # ---------------------------------------------------------------- account
    # These act on YOUR account rather than returning market data, which is why
    # they are documented at https://smartmoneyapi.com/docs and deliberately
    # left out of the public OpenAPI mirror. They are kept here because a client
    # is the right place to call them from. All require a key.

    def usage(self):
        """Your own quota counters: calls used, remaining, and reset time."""
        self._need_key("/v1/usage")
        return self.get("/v1/usage")

    def list_alerts(self):
        """Your alert conditions, plus the available metrics and operators (Pro)."""
        self._need_key("/v1/alerts/conditions")
        return self.get("/v1/alerts/conditions")

    def create_alert(self, name, metric, operator, threshold, symbol="BTC",
                     delivery="telegram", cooldown_minutes=60):
        """Create a threshold alert (Pro).

        ``operator``: ``lt`` | ``gt`` | ``eq`` | ``crosses_above`` | ``crosses_below``.
        """
        self._need_key("/v1/alerts/conditions")
        return self._request("POST", "/v1/alerts/conditions", body={
            "name": name, "metric": metric, "symbol": symbol,
            "operator": operator, "threshold": threshold,
            "delivery": delivery, "cooldown_minutes": cooldown_minutes,
        })

    def delete_alert(self, condition_id):
        """Delete one alert condition by id (Pro)."""
        self._need_key("/v1/alerts/conditions")
        return self._request("DELETE", f"/v1/alerts/conditions/{int(condition_id)}")

    def alert_history(self):
        """Recent alert trigger events (Pro)."""
        self._need_key("/v1/alerts/history")
        return self.get("/v1/alerts/history")

    def register_webhook(self, url, events, symbols, secret):
        """Register an outbound webhook (Pro).

        Deliveries are HMAC-SHA256 signed in the ``X-SmartMoney-Signature``
        header; verify them with :func:`verify_webhook_signature`.

        ``events``: e.g. ``["HIGH", "MEDIUM", "VETO"]`` or ``["*"]``.
        ``symbols``: e.g. ``["BTC", "ETH"]`` or ``["*"]``.
        ``secret``: your signing secret, at least 16 characters (stored hashed).
        """
        self._need_key("/v1/webhooks")
        return self._request("POST", "/v1/webhooks", body={
            "url": url, "events": events, "symbols": symbols, "secret": secret,
        })


    # ------------------------------------------------- 1.1 compatibility aliases
    # Renamed in 1.2.0 for consistency with the published contract. The old
    # names still work so existing code does not break on upgrade.
    get_liquidations = liquidations
    get_onchain_liquidations = onchain_liquidations


def verify_webhook_signature(raw_body, signature_header, secret):
    """Verify an inbound webhook delivery.

    The HMAC key is the SHA-256 hex digest of your registered ``secret``.
    ``raw_body`` must be the exact bytes of the request body — re-serialising
    the parsed JSON will not match. Returns True if the signature is valid.
    """
    import hashlib
    import hmac
    if isinstance(raw_body, str):
        raw_body = raw_body.encode()
    key = hashlib.sha256(secret.encode()).hexdigest()
    expected = hmac.new(key.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")
