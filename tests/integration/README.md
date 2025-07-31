# Integration Tests

End-to-end tests for API endpoints, Cashu wallet operations, and database interactions.

## Running Tests

```bash
# All integration tests
pytest tests/integration/ -v

# Specific test file
pytest tests/integration/test_wallet_topup.py -v

# Skip slow tests
pytest tests/integration/ -m "not slow" -v
```

## Test Infrastructure

**TestmintWallet** - Mock Cashu wallet for generating test tokens
**DatabaseSnapshot** - Captures database state changes  
**Test Utilities** - Validators for responses, performance, and concurrency

## Real Testmint Setup (Optional)

By default, tests use a mock testmint. For testing against a real instance:

```bash
./tests/integration/setup_testmint.sh
export USE_REAL_MINT=true
export MINT_URL=http://localhost:3338
pytest tests/integration/ -v
```

## Writing Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_topup(integration_client, testmint_wallet, db_snapshot):
    await db_snapshot.capture()
    token = await testmint_wallet.mint_tokens(1000)
    
    response = await integration_client.post(
        "/v1/wallet/topup", 
        params={"cashu_token": token}
    )
    
    assert response.status_code == 200
    diff = await db_snapshot.diff()
    assert len(diff["api_keys"]["added"]) == 1
```