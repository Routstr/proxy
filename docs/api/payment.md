## Payments & Pricing

### Pricing helpers and model caps

```1:204:/workspace/routstr/payment/helpers.py
UPSTREAM_BASE_URL = os.environ.get("UPSTREAM_BASE_URL", "")
UPSTREAM_API_KEY = os.environ.get("UPSTREAM_API_KEY", "")

def get_max_cost_for_model(model: str, tolerance_percentage: int = 1) -> int:
    ...
```

```1:171:/workspace/routstr/payment/cost_caculation.py
class CostData(BaseModel):
    base_msats: int
    input_msats: int
    output_msats: int
    total_msats: int

def calculate_cost(response_data: dict, max_cost: int) -> CostData | ...
```

```1:182:/workspace/routstr/payment/models.py
def load_models() -> list[Model]:
    """Load model definitions from a JSON file or auto-generate from OpenRouter API."""
```

### Per-request X-Cashu flow

```1:200:/workspace/routstr/payment/x_cashu.py
async def x_cashu_handler(request: Request, x_cashu_token: str, path: str, max_cost_for_model: int) -> Response | StreamingResponse:
    ...
```

### Wallet operations

```1:200:/workspace/routstr/wallet.py
async def recieve_token(token: str) -> tuple[int, str, str]:
    ...

async def send_token(amount: int, unit: str, mint_url: str | None = None) -> str:
    ...
```
