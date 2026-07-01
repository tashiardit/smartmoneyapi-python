"""Minimal SmartMoneyAPI client. Not financial advice."""
import os, requests
__all__ = ["SmartMoneyClient", "verify_webhook_signature"]
__version__ = "1.1.0"

class SmartMoneyClient:
    def __init__(self, api_key=None, base="https://api.smartmoneyapi.com", timeout=10):
        self.api_key = api_key or os.environ["SMARTMONEY_API_KEY"]
        self.base = base.rstrip("/")
        self.timeout = timeout

    # -- internal helpers ---------------------------------------------------
    def _headers(self):
        # X-API-Key is the primary auth header.
        return {"X-API-Key": self.api_key}

    def _get(self, path, params=None):
        r = requests.get(self.base + path, params=params,
                         headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path, body):
        r = requests.post(self.base + path, json=body,
                          headers={**self._headers(), "Content-Type": "application/json"},
                          timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _delete(self, path):
        r = requests.delete(self.base + path, headers=self._headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # -- trade confirmation -------------------------------------------------
    def confirm(self, symbol, direction, source=None):
        """Confirm/reduce/skip a trade idea. direction: 'long' | 'short'.

        Returns a multi-factor confluence result: `composite` (-1..1),
        `confidence` (HIGH/MEDIUM/LOW/VETO/NO_DATA), `action`
        (CONFIRM_FULL/CONFIRM_REDUCED/CONFIRM_MINIMAL/VETO_SKIP/NO_DATA_SKIP),
        `size_mult`, plus a transparent `factors` breakdown. Not a win-rate.
        """
        params = {"symbol": symbol, "direction": direction}
        if source:
            params["source"] = source
        return self._get("/v1/confirm", params)

    # -- liquidations -------------------------------------------------------
    def get_liquidations(self, symbol="BTC"):
        """Liquidation levels + `realized_heatmap` of REAL executed forced
        liquidations (Binance/OKX/Bybit/Bitget/BitMEX)."""
        return self._get("/v1/liquidations", {"symbol": symbol})

    def get_onchain_liquidations(self, chain=None, limit=100):
        """Executed on-chain DeFi lending liquidations from local BSC/AVAX
        nodes. chain: 'bsc' | 'avax' (None = all). Requires Trader+ key."""
        params = {"limit": limit}
        if chain:
            params["chain"] = chain
        return self._get("/v1/liquidations/onchain", params)

    # -- alerts (Pro) -------------------------------------------------------
    def list_alerts(self):
        """List your alert conditions + available_metrics / available_operators."""
        return self._get("/v1/alerts/conditions")

    def create_alert(self, name, metric, operator, threshold,
                     symbol="BTC", delivery="telegram", cooldown_minutes=60):
        """Create a threshold alert (Pro). operator: lt|gt|eq|crosses_above|crosses_below."""
        return self._post("/v1/alerts/conditions", {
            "name": name, "metric": metric, "symbol": symbol,
            "operator": operator, "threshold": threshold,
            "delivery": delivery, "cooldown_minutes": cooldown_minutes,
        })

    def delete_alert(self, condition_id):
        """Delete an alert condition by id (Pro)."""
        return self._delete(f"/v1/alerts/conditions/{int(condition_id)}")

    def alert_history(self):
        """Recent alert trigger events (Pro)."""
        return self._get("/v1/alerts/history")

    # -- webhooks (Pro) -----------------------------------------------------
    def register_webhook(self, url, events, symbols, secret):
        """Register an outbound webhook (Pro). Deliveries are HMAC-SHA256
        signed in the X-SmartMoney-Signature header.

        events: e.g. ["HIGH","MEDIUM","VETO"] or ["*"].
        symbols: e.g. ["BTC","ETH"] or ["*"].
        secret: your signing secret, >= 16 chars (stored hashed)."""
        return self._post("/v1/webhooks", {
            "url": url, "events": events, "symbols": symbols, "secret": secret,
        })

    # -- account ------------------------------------------------------------
    def usage(self):
        return self._get("/v1/usage")


def verify_webhook_signature(raw_body, signature_header, secret):
    """Verify an inbound webhook delivery.

    The HMAC key is the SHA-256 hex digest of your registered `secret`.
    raw_body: the exact bytes of the request body. Returns True if valid.
    """
    import hashlib, hmac
    if isinstance(raw_body, str):
        raw_body = raw_body.encode()
    key = hashlib.sha256(secret.encode()).hexdigest()
    expected = hmac.new(key.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")
