# Indian market research modules (phase 1)

These modules are pure, deterministic building blocks for Indian stock/F&O research. They do **not** connect to Flattrade, place orders, promise profitability, or implement a working chart UI.

- Grid: bounded grid price levels. Research only; avoid blindly using grids in trending markets or options.
- DCA: fixed-budget allocation schedule; no automatic averaging down.
- Martingale: **risk illustration only**, never used for execution. Loss-escalating martingale is intentionally disabled.
- Footprint: per-price-level aggressive buy/sell executed volumes provided by a genuine trade-side classifier.
- CVD: cumulative sum of classified executed buy-minus-sell volume.
- Imbalance: threshold comparison on classified volumes.
- Absorption: high-volume/low-movement *candidate*; requires additional order book and level validation.

## Data prerequisites
A reliable, exchange-permitted executed-trade stream with timestamps, prices, sizes and aggressor-side classification (or quote-matched inference with coverage/confidence) is essential for footprint/CVD. Candles, OI and top-of-book quotes alone are insufficient. Validate Flattrade entitlements and feed coverage before enabling these features. For stock and index options, evaluate liquidity, expiry and spread separately.

## Next stages
1. Add market-specific instruments, lot sizes, session calendars and data adapters.
2. Add tests using real, licensed historical Indian market data.
3. Implement backtesting with charges, spreads, latency and slippage.
4. Integrate QuantDinger strategy API V2 and the recommendation ranking pipeline.
5. Add live market feed and Android/Web visualization after data validation.
6. Paper trade first; require explicit approval and compliance checks for any live execution.
