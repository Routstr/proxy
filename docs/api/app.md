## App & Routers

### FastAPI app and routers

```80:135:/workspace/routstr/core/main.py
app = FastAPI(
    version=__version__,
    title=os.environ.get("NAME", "ARoutstrNode" + __version__),
    description=os.environ.get("DESCRIPTION", "A Routstr Node"),
    contact={"name": os.environ.get("NAME", ""), "npub": os.environ.get("NPUB", "")},
    lifespan=lifespan,
)

app.include_router(models_router)
app.include_router(admin_router)
app.include_router(balance_router)
app.include_router(deprecated_wallet_router)
app.include_router(providers_router)
app.include_router(proxy_router)
```

### Balance endpoints

```1:60:/workspace/routstr/balance.py
balance_router = APIRouter(prefix="/v1/balance")

@router.get("/info")
async def wallet_info(key: ApiKey = Depends(get_key_from_header)) -> dict:
    return {"api_key": "sk-" + key.hashed_key, "balance": key.balance}
```

### Providers discovery

```200:273:/workspace/routstr/discovery.py
@providers_router.get("/")
async def get_providers(include_json: bool = False, pubkey: str | None = None) -> dict[str, list[dict[str, Any]]]:
    ...
```
