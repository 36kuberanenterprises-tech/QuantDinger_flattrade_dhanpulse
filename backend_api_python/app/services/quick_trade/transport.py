"""Request-scoped transport lifecycle for Quick Trade routes."""

from flask import g
import requests


def open_quick_trade_transport() -> None:
    """Open one TLS session for the current request."""
    g.quick_trade_session = requests.Session()


def close_quick_trade_transport(error=None) -> None:
    """Close the request-scoped TLS session when present."""
    session = g.pop("quick_trade_session", None)
    if session is not None:
        session.close()
