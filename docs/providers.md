## Providers and discovery

Routstr can discover provider announcements over Nostr (RIP-02) via `GET /v1/providers`.

- Queries default relays like `wss://relay.nostr.band`, `wss://relay.damus.io`, `wss://relay.routstr.com`
- Parses kind `31338` events for endpoint metadata and supported models
- Optional `?include_json=true` triggers a basic health check of `/v1/models` or `/`

Configure `.onion` access with `TOR_PROXY_URL` (e.g., `socks5://tor:9050`).
