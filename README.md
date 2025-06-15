# Routstr Payment Proxy

Routstr is a FastAPI based reverse proxy that sits in front of any OpenAI
compatible API. It handles pay-per-request billing using the
[Cashu](https://cashu.space/) protocol on Bitcoin and tracks usage in a local
SQL database.

The server exposes the same endpoints as the upstream API and deducts sats from
user accounts for each call. Pricing can be static or model specific by loading
`models.json` (falls back to `models.example.json`).

## Features

- **Cashu Wallet integration** – accept Lightning payments and redeem tokens
  before forwarding requests.
- **API key management** – hashed keys stored in SQLite with balance tracking
  and optional expiry / refund address.
- **Model based pricing** – convert USD prices in `models.json` to sats using
  live BTC/USD rates.
- **Admin dashboard** – simple HTML interface at `/admin` to view balances and
  API keys.
- **Discovery** – fetch available providers from Nostr relays.
- **Docker support** – provided `Dockerfile` and `compose.yml` for running with
  an optional Tor hidden service.

## Getting started

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager (used in development)
- A Cashu wallet secret (`NSEC`) and Lightning address for receiving payments

### Installation

```bash
uv sync --dev  # install dependencies
```

Create a `.env` file based on `.env.example` and fill in the required values:

```bash
cp .env.example .env
```

### Running locally

```bash
fastapi run router --host 0.0.0.0 --port 8000
```

The service forwards requests to `UPSTREAM_BASE_URL`. Supply the upstream API
key via the `UPSTREAM_API_KEY` environment variable if required.

### Docker

```bash
docker compose up --build
```

This builds the image and also starts a Tor container exposing the API as a
hidden service.

## Environment variables

The most common settings are shown below. See `.env.example` for the full list.

- `UPSTREAM_BASE_URL` – URL of the OpenAI compatible service
- `UPSTREAM_API_KEY` – API key for the upstream service (optional)
- `RECEIVE_LN_ADDRESS` – Lightning address that receives payouts
- `MINIMUM_PAYOUT` – minimum sats before forwarding earnings
- `MODEL_BASED_PRICING` – set to `true` to use pricing from `models.json`
- `REFUND_PROCESSING_INTERVAL` – seconds between automatic refunds
- `ADMIN_PASSWORD` – password for the `/admin` dashboard

## Example client

`example.py` shows how to use the proxy with the official OpenAI client:

```bash
CASHU_TOKEN=<redeemable token> python example.py
```

The script sends streaming chat completions and pays for each request using the
provided token.

## Running tests

```bash
uv run pytest
```

The tests create a temporary SQLite database and mock the Cashu wallet. See
`tests/README.md` for more details.

## License

This project is licensed under the terms of the GPLv3. See the `LICENSE` file
for the full license text.
