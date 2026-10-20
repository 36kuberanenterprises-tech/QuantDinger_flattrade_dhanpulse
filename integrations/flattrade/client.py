"""Minimal read only Flattrade Pi API client.

Authentication token must be generated through the broker authorised login flow.
No order placement methods are provided in this phase.
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://piconnect.flattrade.in/PiConnectAPI/"


class FlattradeError(RuntimeError):
    pass


@dataclass
class FlattradeClient:
    user_id: str
    session_token: str
    base_url: str = BASE_URL
    timeout: int = 12

    def _post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        if not self.user_id or not self.session_token:
            raise FlattradeError("Missing authenticated user ID or session token")
        body = urlencode({
            "jData": json.dumps({"uid": self.user_id, **payload}, separators=(",", ":")),
            "jKey": self.session_token,
        }).encode()
        request = Request(
            self.base_url.rstrip("/") + "/" + endpoint,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode())
        except Exception as exc:
            raise FlattradeError(f"{endpoint} request failed: {type(exc).__name__}") from exc
        if isinstance(result, dict) and result.get("stat") == "Not_Ok":
            raise FlattradeError(f"{endpoint}: {result.get('emsg', 'Broker rejected request')}")
        return result

    def limits(self) -> Any:
        return self._post("Limits", {"actid": self.user_id})

    def positions(self) -> Any:
        return self._post("PositionBook", {"actid": self.user_id})

    def order_book(self) -> Any:
        return self._post("OrderBook", {})

    def search(self, exchange: str, query: str) -> Any:
        if exchange not in {"NSE", "BSE", "NFO", "BFO", "MCX"}:
            raise ValueError("Unsupported exchange")
        return self._post("SearchScrip", {"exch": exchange, "stext": query})

    def quote(self, exchange: str, token: str) -> Any:
        return self._post("GetQuotes", {"exch": exchange, "token": token})
