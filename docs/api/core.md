## Core Modules

### Logging, Exceptions, Middleware

```1:135:/workspace/routstr/core/main.py
from ..balance import balance_router, deprecated_wallet_router
from ..discovery import providers_router
from ..payment.models import MODELS, models_router, update_sats_pricing
from ..proxy import proxy_router
from ..wallet import periodic_payout
from .admin import admin_router
from .db import init_db, run_migrations
```

```1:116:/workspace/routstr/core/db.py
class ApiKey(SQLModel, table=True):  # type: ignore
    __tablename__ = "api_keys"

    hashed_key: str = Field(primary_key=True)
    balance: int = Field(default=0, description="Balance in millisatoshis (msats)")
```

```1:127:/workspace/routstr/core/middleware.py
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
```

```1:58:/workspace/routstr/core/exceptions.py
async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
```
