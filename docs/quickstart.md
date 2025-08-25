## Quickstart (Docker)

Run a Routstr Core instance in Docker:

```bash
docker run -d \
  --name routstr \
  -p 8000:8000 \
  -e UPSTREAM_BASE_URL=https://api.openai.com/v1 \
  -e UPSTREAM_API_KEY=your-openai-api-key \
  ghcr.io/routstr/proxy:latest
```

You can now send OpenAI-compatible requests to `http://localhost:8000/v1/...`.

Admin dashboard: `http://localhost:8000/admin/` (set `ADMIN_PASSWORD` to enable login).

## Quickstart (Docker Compose)

The repository includes a `compose.yml` that optionally runs a Tor hidden service:

```bash
docker compose up --build
```

Exposes the API at `http://localhost:8000`. If Tor is enabled, your `.onion` URL will be shown in logs.

## Environment variables

Create a `.env` from `.env.example` and customize as needed:

```bash
cp .env.example .env
```

- `UPSTREAM_BASE_URL` and `UPSTREAM_API_KEY`: point to your upstream provider
- `MODEL_BASED_PRICING=true`: enable per-model caps from `models.json` or OpenRouter auto-fetch
- `CASHU_MINTS`: comma-separated Cashu mint URLs
- `DATABASE_URL`: SQLite by default; can be any SQLAlchemy async URL
- `HTTP_URL`/`ONION_URL`: public URLs advertised in `/v1/info`

## Running locally (dev)

```bash
make setup
fastapi run routstr --host 0.0.0.0 --port 8000
```

Or with `uv` directly:

```bash
uv sync
uv run fastapi run routstr --host 0.0.0.0 --port 8000
```

## Example client

`example.py` streams chat completions through Routstr using OpenAI SDK:

```bash
CASHU_TOKEN=<redeemable token> ROUTSTR_API_URL=http://localhost:8000/v1 python example.py
```
