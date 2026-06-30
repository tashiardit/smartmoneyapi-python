"""Minimal SmartMoneyAPI client. Not financial advice."""
import os, requests
__all__ = ["SmartMoneyClient"]
__version__ = "1.0.0"

class SmartMoneyClient:
    def __init__(self, api_key=None, base="https://api.smartmoneyapi.com", timeout=10):
        self.api_key = api_key or os.environ["SMARTMONEY_API_KEY"]
        self.base = base.rstrip("/")
        self.timeout = timeout

    def _get(self, path, params=None):
        r = requests.get(self.base + path, params=params,
                         headers={"X-API-Key": self.api_key}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def confirm(self, symbol, direction):
        """Confirm/reduce/skip a trade idea. direction: 'long' | 'short'."""
        return self._get("/v1/confirm", {"symbol": symbol, "direction": direction})

    def usage(self):
        return self._get("/v1/usage")
