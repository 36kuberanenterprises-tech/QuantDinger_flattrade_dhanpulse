# Flattrade integration: Phase 1

Read only broker connector for QuantDinger India.

## Scope
* Server side authenticated REST calls for limits, positions, orders, symbol search and quotes
* No live order placement
* No credential storage or hardcoded secrets
* Session token must be obtained via Flattrade authorised authentication

## Example
```python
import os
from integrations.flattrade import FlattradeClient

client = FlattradeClient(
    user_id=os.environ["FLATTRADE_USER_ID"],
    session_token=os.environ["FLATTRADE_SESSION_TOKEN"],
)
print(client.search("NSE", "RELIANCE"))
```

Do not print credentials or commit a .env file. Validate actual broker payloads and exchange entitlements before connecting this module to trading workers.

## Next milestones
1. Confirm authentication and API response schemas against current Flattrade documentation.
2. Add instrument master synchronisation and contract expiry validation.
3. Add WebSocket subscriptions, reconnects and stale quote handling.
4. Implement paper execution and a separate hard risk gate before any live orders.
