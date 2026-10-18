"""Late fee reconciliation for Quick Trade fills."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from app.services.live_trading.gate import GateUsdtFuturesClient
from app.services.live_trading.symbols import to_gate_currency_pair
from app.services.pending_orders.fee_reconciliation import (
    fee_breakdown_to_quote,
    fee_storage_values,
)


def gate_swap_order_fees(
    client: Any,
    symbol: str,
    order_ids: Iterable[str],
) -> Dict[str, Dict[str, Any]]:
    """Return authoritative Gate swap fees grouped by exchange order ID."""
    if not isinstance(client, GateUsdtFuturesClient):
        return {}

    wanted = {str(order_id or "").strip() for order_id in order_ids}
    wanted.discard("")
    if not wanted:
        return {}

    contract = to_gate_currency_pair(symbol)
    rows = client._signed_request(
        "GET",
        "/api/v4/futures/usdt/my_trades",
        params={"contract": contract, "limit": 100},
    )
    if not isinstance(rows, list):
        return {}

    totals: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict) or str(row.get("contract") or "") != contract:
            continue
        order_id = str(row.get("order_id") or row.get("order") or "").strip()
        if order_id not in wanted:
            continue
        try:
            fee = float(row.get("fee") or 0.0)
        except (TypeError, ValueError):
            continue
        totals[order_id] = totals.get(order_id, 0.0) + fee

    return {
        order_id: {
            "commission": abs(total),
            "commission_ccy": "USDT",
            "commission_quote": abs(total),
        }
        for order_id, total in totals.items()
    }


def fee_update_from_fill(
    client: Any,
    symbol: str,
    fill: Dict[str, Any],
    *,
    fallback_price: float = 0.0,
) -> Dict[str, Any]:
    """Normalize one fill snapshot into Quick Trade fee storage fields."""
    raw_fees = fill.get("fees_by_ccy") if isinstance(fill, dict) else None
    fees: Dict[str, float] = {}
    if isinstance(raw_fees, dict):
        for currency, amount in raw_fees.items():
            try:
                value = float(amount or 0.0)
            except (TypeError, ValueError):
                continue
            fees[str(currency or "").strip().upper() or "UNKNOWN"] = value
    if not fees:
        currency = str(fill.get("fee_ccy") or "").strip().upper()
        if currency and "fee" in fill:
            fees[currency] = float(fill.get("fee") or 0.0)

    status = str(fill.get("fee_status") or "pending").strip().lower()
    if status not in {"actual", "actual_zero"}:
        if fees:
            status = "actual" if any(abs(value) > 1e-18 for value in fees.values()) else "actual_zero"
        else:
            return {}

    commission, commission_ccy = fee_storage_values(fees)
    fill_price = float(fill.get("avg_price") or fallback_price or 0.0)
    commission_quote = fee_breakdown_to_quote(
        client,
        symbol=symbol,
        fees=fees,
        fill_price=fill_price,
    )
    if status == "actual_zero" and commission_quote is None:
        commission_quote = 0.0
    return {
        "commission": abs(float(commission or 0.0)),
        "commission_ccy": commission_ccy,
        "commission_quote": None if commission_quote is None else abs(float(commission_quote)),
        "fees_by_ccy": fees,
        "fee_status": status,
    }


def quick_trade_fee_updates(
    client: Any,
    symbol: str,
    market_type: str,
    rows: Iterable[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Fetch late exchange fees for multiple Quick Trade rows."""
    candidates = [dict(row or {}) for row in rows]
    updates: Dict[str, Dict[str, Any]] = {}

    if isinstance(client, GateUsdtFuturesClient) and str(market_type or "").lower() == "swap":
        updates.update(gate_swap_order_fees(
            client,
            symbol,
            [row.get("exchange_order_id") for row in candidates],
        ))
        for update in updates.values():
            update["fees_by_ccy"] = {"USDT": update["commission"]}
            update["fee_status"] = "actual" if update["commission"] else "actual_zero"
        candidates = [
            row for row in candidates
            if str(row.get("exchange_order_id") or "").strip() not in updates
        ]

    from app.services.quick_trade.orders import enrich_fill

    for row in candidates[:12]:
        order_id = str(row.get("exchange_order_id") or "").strip()
        if not order_id:
            continue
        fill = enrich_fill(
            client,
            order_id=order_id,
            symbol=symbol,
            market_type=market_type,
            max_wait_sec=0.0,
        )
        update = fee_update_from_fill(
            client,
            symbol,
            fill,
            fallback_price=float(row.get("avg_fill_price") or row.get("price") or 0.0),
        )
        if update:
            updates[order_id] = update
    return updates
