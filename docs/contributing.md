## Contributing

Follow the repo's `CONTRIBUTING.md` for full details. Quick highlights:

1. Install dev deps and tooling

```bash
make setup
```

2. Run quality checks

```bash
make lint
make type-check
make test
```

3. Code style

- Python 3.11+, full type hints
- Ruff for lint + format, Mypy for types
- Conventional Commits for messages

4. Project structure

- `routstr/core`: app, db, logging, admin
- `routstr/payment`: pricing and models
- `routstr/proxy.py`: request forwarding and cost handling
- `routstr/auth.py`: bearer and token auth

Open a PR against `main` with tests and docs when ready.
