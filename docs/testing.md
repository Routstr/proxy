## Testing

### Local tests

```bash
uv run pytest
```

Markers:

- `unit` and `integration`
- `requires_docker` for tests using services
- `performance` for load tests

### Integration with Docker services

```bash
make docker-up
make test-integration-docker
```

This starts a mock OpenAI server, a Cashu mint, and a Nostr relay from `compose.testing.yml` and runs the suite that requires them.
