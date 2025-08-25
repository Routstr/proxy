## Operations

### Running and health

- Start with Docker or `fastapi run routstr`
- Check `/v1/info` for node metadata and advertised URLs

### Logs

- JSON logs are written to `logs/app_YYYY-MM-DD.log`
- Use `LOG_LEVEL` and `ENABLE_CONSOLE_LOGGING` to tune verbosity
- Admin UI provides a simple per-request log viewer by request ID

### Database migrations

Migrations run automatically on startup. Manual controls via `make`:

```bash
make db-upgrade
make db-downgrade
make db-current
make db-history
make db-migrate   # autogenerate from model changes
```

### Payouts

If `RECEIVE_LN_ADDRESS` is set, `wallet.periodic_payout` periodically sends excess owner balance to the specified LNURL/Lightning address.
