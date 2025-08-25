## What is Routstr Core?

Routstr Core is a FastAPI-based reverse proxy that sits in front of any OpenAI-compatible API. It enables pay-per-request access using Cashu eCash on Bitcoin, with balances tracked in a local database. Requests look like standard OpenAI API calls, so existing clients work unchanged.

- Accepts eCash tokens from users (either per-request via the `X-Cashu` header or by funding an API key)
- Enforces pricing per request and per token usage
- Forwards to the upstream model provider and returns responses transparently
- Provides an admin dashboard for balances and withdrawals

Key modules:

- `routstr/core`: app setup, DB, exceptions, logging, middleware, and admin UI
- `routstr/proxy`: request routing and upstream forwarding
- `routstr/auth`: bearer key validation and Cashu-token redemption to balances
- `routstr/payment`: pricing helpers, models, and `X-Cashu` flow
- `routstr/wallet`: Cashu wallet operations and periodic payouts

If you just want to run the proxy, start with Quickstart. If you want to contribute, see Contributing.
