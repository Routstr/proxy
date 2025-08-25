## Architecture

Routstr Core is organized around a FastAPI app with layered modules:

- App lifecycle and cross-cutting concerns in `routstr/core`
  - `main.py`: FastAPI app factory, CORS, routers, background tasks
  - `db.py`: SQLModel `ApiKey` table, async engine, Alembic migrations runner
  - `middleware.py`: request/response logging with per-request IDs
  - `exceptions.py`: unified exception handlers including `request_id`
  - `logging.py`: JSON logs to `logs/` (daily-rotated) and optional rich console
  - `admin.py`: minimal admin dashboard (HTML) for balances and withdrawals
- Request handling in `routstr/proxy.py`
  - Validates auth, pre-charges base cost, forwards to upstream
  - For chat completions, adjusts cost after usage is known
- Authentication in `routstr/auth.py`
  - Supports `sk-<hash>` API keys and raw `cashu...` tokens
  - Cashu tokens are redeemed and stored as balances linked to `hashed_key`
- Wallet management in `routstr/wallet.py`
  - Cashu wallet creation/loading, token redemption and sending
  - Mint swaps to a primary mint and periodic payouts via LNURL
  - Aggregate balances across mints/units (for admin)
- Payment pricing in `routstr/payment`
  - `helpers.py`: env, upstream header filtering, model max-cost lookup
  - `cost_caculation.py`: base + token-based pricing, and model-based pricing
  - `models.py`: load models from file or OpenRouter and compute sats caps
  - `x_cashu.py`: per-request payment flow via `X-Cashu` header, with refunds
  - `lnurl.py`: LNURL payRequest utilities and invoice melt

### Request flows

1) Bearer flow (funded API keys)
   - Client sends standard OpenAI call with `Authorization: Bearer sk-...` or `Bearer cashu...`
   - `auth.validate_bearer_key` creates/loads `ApiKey`, redeeming cashu token if needed
   - `proxy` pre-charges a model-specific capped cost, forwards request
   - After response: compute actual token-based cost; refund or top-up delta

2) X-Cashu flow (per-request tokens)
   - Client sends `X-Cashu: <token>` on each request
   - `x_cashu_handler` redeems token, forwards upstream, computes cost
   - Any change is returned in `X-Cashu` response header as a new token

### Database schema

`ApiKey` table stores hashed keys, msat balances, reserved balances, refund info, and usage counters. Alembic migrations are executed automatically at startup.
