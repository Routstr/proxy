## Auth & Proxy

### Authentication

```1:140:/workspace/routstr/auth.py
async def validate_bearer_key(
    bearer_key: str,
    session: AsyncSession,
    refund_address: Optional[str] = None,
    key_expiry_time: Optional[int] = None,
) -> ApiKey:
    """Validates sk- keys or Cashu tokens, redeeming and persisting balances."""
```

### Pre-charge and adjustment

```270:371:/workspace/routstr/auth.py
async def pay_for_request(key: ApiKey, cost_per_request: int, session: AsyncSession) -> int:
    ...

async def adjust_payment_for_tokens(key: ApiKey, response_data: dict, session: AsyncSession, deducted_max_cost: int) -> dict:
    ...
```

### Proxy routing

```245:615:/workspace/routstr/proxy.py
async def forward_to_upstream(...):
    ...

@proxy_router.api_route("/{path:path}", methods=["GET", "POST"], response_model=None)
async def proxy(...):
    ...
```
