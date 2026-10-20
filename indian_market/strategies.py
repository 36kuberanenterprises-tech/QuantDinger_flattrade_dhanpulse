"""Indian market research strategies. Pure calculations; no broker orders."""
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class Signal:
    action: str
    reason: str
    levels: tuple[float, ...] = ()

def grid_levels(lower: float, upper: float, steps: int) -> tuple[float, ...]:
    """Price levels for a bounded, non-martingale grid."""
    if lower <= 0 or upper <= lower or not 2 <= steps <= 100:
        raise ValueError("invalid grid")
    return tuple(round(lower + (upper-lower)*i/steps, 4) for i in range(steps+1))

def dca_plan(total_budget: float, weights: Sequence[float]) -> tuple[float, ...]:
    """Budget allocations only; never automatic averaging down."""
    if total_budget <= 0 or not weights or any(w <= 0 for w in weights):
        raise ValueError("invalid allocation")
    total = sum(weights)
    return tuple(round(total_budget*w/total, 2) for w in weights)

def martingale_exposure(initial_qty: int, multiplier: float, steps: int) -> tuple[int, ...]:
    """Risk illustration only; NOT executable and never used for trade recommendations."""
    if initial_qty <= 0 or not 1 <= multiplier <= 3 or not 1 <= steps <= 8:
        raise ValueError("invalid inputs")
    return tuple(round(initial_qty * multiplier**i) for i in range(steps))

def footprint(buy_volume: Sequence[float], sell_volume: Sequence[float]) -> dict:
    """Trade-side classified executed volumes; never infer from candles or OI."""
    if len(buy_volume) != len(sell_volume) or not buy_volume:
        raise ValueError("missing matched trade-side data")
    if any(v < 0 for v in (*buy_volume, *sell_volume)):
        raise ValueError("negative volume")
    delta = [b-s for b,s in zip(buy_volume,sell_volume)]
    cvd = []
    running = 0.0
    for d in delta:
        running += d
        cvd.append(running)
    return {"delta": delta, "cvd": cvd, "buy_volume": list(buy_volume), "sell_volume": list(sell_volume)}

def orderflow_imbalance(buy: float, sell: float, threshold: float = 3.0) -> Signal:
    if min(buy, sell) < 0 or threshold <= 1:
        raise ValueError("invalid trade volumes or threshold")
    if buy == 0 and sell == 0:
        return Signal("WAIT", "no executed trades")
    if buy > threshold * sell:
        return Signal("BULLISH_IMBALANCE", "aggressive buying dominates")
    if sell > threshold * buy:
        return Signal("BEARISH_IMBALANCE", "aggressive selling dominates")
    return Signal("WAIT", "no qualifying imbalance")

def absorption(price_change: float, traded_volume: float, min_volume: float, max_abs_change: float) -> Signal:
    """Flags a candidate only; full absorption needs level/DOM context."""
    if traded_volume < 0 or min_volume <= 0 or max_abs_change < 0:
        raise ValueError("invalid thresholds")
    if traded_volume >= min_volume and abs(price_change) <= max_abs_change:
        return Signal("REVIEW", "high executed volume with limited price movement; confirm at price level")
    return Signal("WAIT", "no absorption candidate")
