from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException

from .auth import validate_bearer_key
from .cashu import (
    credit_balance,
    delete_key_if_zero_balance,
    refund_balance,
    wallet,
)
from .db import ApiKey, AsyncSession, get_session

wallet_router = APIRouter(prefix="/v1/wallet")


async def get_key_from_header(
    authorization: Annotated[str, Header(...)],
    session: AsyncSession = Depends(get_session),
) -> ApiKey:
    if authorization.startswith("Bearer "):
        return await validate_bearer_key(authorization[7:], session)

    raise HTTPException(
        status_code=401,
        detail="Invalid authorization. Use 'Bearer <cashu-token>' or 'Bearer <api-key>'",
    )


# TODO: remove this endpoint when frontend is updated
@wallet_router.get("/")
async def account_info(key: ApiKey = Depends(get_key_from_header)) -> dict:
    return {
        "api_key": "sk-" + key.hashed_key,
        "balance": key.balance,
    }


@wallet_router.get("/info")
async def wallet_info(key: ApiKey = Depends(get_key_from_header)) -> dict:
    return {
        "api_key": "sk-" + key.hashed_key,
        "balance": key.balance,
    }


@wallet_router.post("/topup")
async def topup_wallet_endpoint(
    cashu_token: str,
    key: ApiKey = Depends(get_key_from_header),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    # Validate token format first
    if not cashu_token or not cashu_token.startswith("cashu"):
        raise HTTPException(status_code=400, detail="Invalid token format")

    # Check for obviously invalid tokens
    if len(cashu_token) < 10:  # Too short to be valid
        raise HTTPException(status_code=400, detail="Invalid token format")

    # Check for malformed base64 in token
    if "cashuA" in cashu_token:
        try:
            import base64

            # Extract base64 part after 'cashuA'
            base64_part = cashu_token[6:]
            if base64_part:
                # Try to decode - will raise exception if invalid
                base64.urlsafe_b64decode(base64_part + "=" * (4 - len(base64_part) % 4))
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid token format: malformed base64"
            )

    # Check for newlines or other invalid characters
    if any(char in cashu_token for char in ["\n", "\r", "\t"]):
        raise HTTPException(status_code=400, detail="Invalid token format")

    # Try to redeem the token
    try:
        amount_msats = await credit_balance(cashu_token, key, session)
    except ValueError as e:
        # Token redemption failed (invalid token, already spent, network error, etc.)
        error_msg = str(e)
        if "already spent" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Token already spent")
        elif "invalid" in error_msg.lower() or "decode" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Invalid token format")
        else:
            raise HTTPException(status_code=400, detail="Failed to redeem token")
    except Exception:
        # Unexpected error
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"msats": amount_msats}


@wallet_router.post("/refund")
async def refund_wallet_endpoint(
    key: ApiKey = Depends(get_key_from_header),
    session: AsyncSession = Depends(get_session),
) -> dict:
    remaining_balance_msats = key.balance

    if remaining_balance_msats == 0:
        raise HTTPException(status_code=400, detail="No balance to refund")

    # Perform refund operation first, before modifying balance
    if key.refund_address:
        # refund_balance handles balance update and key deletion
        await refund_balance(remaining_balance_msats, key, session)
        return {"recipient": key.refund_address, "msats": remaining_balance_msats}
    else:
        # Convert msats to sats for cashu wallet
        remaining_balance_sats = remaining_balance_msats // 1000
        if remaining_balance_sats == 0:
            raise HTTPException(
                status_code=400, detail="Balance too small to refund (less than 1 sat)"
            )

        # TODO: choose currency and mint based on what user has configured
        try:
            token = await wallet().send(remaining_balance_sats)
        except Exception as e:
            # Handle mint service errors
            raise HTTPException(
                status_code=503, detail=f"Mint service unavailable: {str(e)}"
            )

        # Only for token refunds, we need to manually update balance and delete key
        key.balance = 0
        session.add(key)
        await session.commit()
        await delete_key_if_zero_balance(key, session)

        return {"msats": remaining_balance_msats, "recipient": None, "token": token}


@wallet_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    include_in_schema=False,
    response_model=None,
)
async def wallet_catch_all(path: str) -> NoReturn:
    raise HTTPException(
        status_code=404, detail="Not found check /docs for available endpoints"
    )
