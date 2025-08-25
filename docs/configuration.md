## Configuration

Environment variables control runtime behavior. See `.env.example` for a full template.

- Core
  - `UPSTREAM_BASE_URL`: Required. Base URL of the upstream OpenAI-compatible API
  - `UPSTREAM_API_KEY`: Optional upstream key to inject into forwarded requests
- Pricing
  - `COST_PER_REQUEST`: Base cost per request in sats (converted to msats)
  - `COST_PER_1K_INPUT_TOKENS`, `COST_PER_1K_OUTPUT_TOKENS`: additional token-based costs in sats
  - `MODEL_BASED_PRICING`: Enable model-specific caps from `routstr/payment/models.py`
  - `MODELS_PATH`: Path to `models.json`. If absent, models are fetched from OpenRouter
  - `SOURCE`: Optional filter for OpenRouter model IDs
- Node metadata
  - `NAME`, `DESCRIPTION`, `NPUB`, `HTTP_URL`, `ONION_URL`, `CORS_ORIGINS`
- Wallet
  - `CASHU_MINTS`: Comma-separated list of Cashu mint URLs
  - `RECEIVE_LN_ADDRESS`: LNURL or Lightning Address for periodic payouts
- Database
  - `DATABASE_URL`: Defaults to `sqlite+aiosqlite:///keys.db`
- Logging
  - `LOG_LEVEL` (TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL)
  - `ENABLE_CONSOLE_LOGGING` (true|false)
- Pricing aggregation tuning
  - `EXCHANGE_FEE`, `UPSTREAM_PROVIDER_FEE`

## Models configuration

If `MODELS_PATH` points to a `models.json` file, Routstr loads models and computes sats pricing caps. If not set, it auto-fetches models from OpenRouter in memory (no file required). See `models.example.json` for structure.

## Docker Compose

`compose.yml` defines services:

- `routstr`: main app. Mounts `./logs` and reads `.env`
- `tor`: optional Tor hidden service, configured via `HS_ROUTER`

Expose the proxy on `:8000` and set `TOR_PROXY_URL` if calling `.onion` providers.
