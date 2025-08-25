## Using the proxy

### 1) Per-request payments (X-Cashu header)

Send a redeemable eCash token with each request:

```bash
curl -sS http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Cashu: <ecash_token>" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

If actual cost is lower than the token amount, change is returned in the `X-Cashu` response header.

### 2) Funded API key (Bearer)

Create or top up balance by sending a Cashu token as the bearer once, then reuse the `sk-` key the proxy returns:

```bash
curl -sS "http://localhost:8000/v1/balance/create?initial_balance_token=<ecash_token>"
# => { "api_key": "sk-<hash>", "balance": 12345 }

curl -sS http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-<hash>" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

### OpenAI SDK example

Use `example.py`:

```bash
CASHU_TOKEN=<ecash_token> ROUTSTR_API_URL=http://localhost:8000/v1 python example.py
```

### Admin dashboard

Navigate to `/admin/` and log in with `ADMIN_PASSWORD` to view balances and withdraw.