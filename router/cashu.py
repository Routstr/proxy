import asyncio
import os
import time
from typing import cast

from sixty_nuts import Wallet
from sixty_nuts.types import CurrencyUnit
from sqlmodel import col, func, select, update

from .db import ApiKey, AsyncSession, get_session
from .logging.logging_config import get_logger

logger = get_logger(__name__)

RECEIVE_LN_ADDRESS = os.environ["RECEIVE_LN_ADDRESS"]
MINT = os.environ.get("MINT", "https://mint.minibits.cash/Bitcoin")
MINIMUM_PAYOUT = int(os.environ.get("MINIMUM_PAYOUT", 100))
REFUND_PROCESSING_INTERVAL = int(os.environ.get("REFUND_PROCESSING_INTERVAL", 3600))
PAYOUT_INTERVAL = int(os.environ.get("PAYOUT_INTERVAL", 300))  # Default 5 minutes
DEV_LN_ADDRESS = "routstr@minibits.cash"
DEVS_DONATION_RATE = float(os.environ.get("DEVS_DONATION_RATE", 0.021))  # 2.1%
NSEC = os.environ["NSEC"]  # Nostr private key for the wallet

logger.info(
    "Cashu module initialized",
    extra={
        "mint": MINT,
        "minimum_payout": MINIMUM_PAYOUT,
        "refund_processing_interval": REFUND_PROCESSING_INTERVAL,
        "payout_interval": PAYOUT_INTERVAL,
        "devs_donation_rate": DEVS_DONATION_RATE,
    },
)

wallet_instance: Wallet | None = None


async def init_wallet() -> None:
    """Initialize the Cashu wallet."""
    global wallet_instance
    try:
        logger.info("Initializing Cashu wallet", extra={"mint": MINT})
        wallet_instance = await Wallet.create(nsec=NSEC)
        logger.info("Cashu wallet initialized successfully")
    except Exception as e:
        logger.error(
            "Failed to initialize Cashu wallet",
            extra={"error": str(e), "error_type": type(e).__name__, "mint": MINT},
        )
        raise


def wallet() -> Wallet:
    """Get the wallet instance."""
    global wallet_instance
    if wallet_instance is None:
        logger.error("Wallet not initialized - call init_wallet() first")
        raise ValueError("Wallet not initialized")
    return wallet_instance


async def delete_key_if_zero_balance(key: ApiKey, session: AsyncSession) -> None:
    """Delete the given API key if its balance is zero."""
    if key.balance == 0:
        logger.info(
            "Deleting API key with zero balance",
            extra={"key_hash": key.hashed_key[:8] + "...", "balance": key.balance},
        )
        await session.delete(key)
        await session.commit()


async def pay_out() -> None:
    """
    Calculates the pay-out amount based on the spent balance, profit, and donation rate.
    """
    try:
        logger.debug("Starting payout process")
        from .db import create_session

        async with create_session() as session:
            result = await session.exec(
                select(func.sum(col(ApiKey.balance))).where(ApiKey.balance > 0)
            )
            balance = result.one_or_none()
            if not balance:
                logger.debug("No balance to pay out")
                return

            user_balance_sats = balance // 1000
            wallet_balance_sats = await wallet().get_balance()

            logger.debug(
                "Payout calculation",
                extra={
                    "user_balance_sats": user_balance_sats,
                    "wallet_balance_sats": wallet_balance_sats,
                },
            )

            # Handle edge cases more gracefully
            if wallet_balance_sats < user_balance_sats:
                logger.warning(
                    "Insufficient wallet balance for payout",
                    extra={
                        "wallet_balance_sats": wallet_balance_sats,
                        "user_balance_sats": user_balance_sats,
                        "shortfall_sats": user_balance_sats - wallet_balance_sats,
                    },
                )
                return

            if (revenue := wallet_balance_sats - user_balance_sats) <= MINIMUM_PAYOUT:
                logger.debug(
                    "Revenue below minimum payout threshold",
                    extra={"revenue_sats": revenue, "minimum_payout": MINIMUM_PAYOUT},
                )
                return

            devs_donation = int(revenue * DEVS_DONATION_RATE)
            owners_draw = revenue - devs_donation

            logger.info(
                "Processing payout",
                extra={
                    "revenue_sats": revenue,
                    "devs_donation_sats": devs_donation,
                    "owners_draw_sats": owners_draw,
                    "donation_rate": DEVS_DONATION_RATE,
                },
            )

            # Send payouts
            try:
                await wallet().send_to_lnurl(RECEIVE_LN_ADDRESS, owners_draw)
                logger.info(
                    "Owner payout sent successfully",
                    extra={
                        "amount_sats": owners_draw,
                        "address": RECEIVE_LN_ADDRESS[:10] + "...",
                    },
                )

                await wallet().send_to_lnurl(DEV_LN_ADDRESS, devs_donation)
                logger.info(
                    "Developer donation sent successfully",
                    extra={"amount_sats": devs_donation, "address": DEV_LN_ADDRESS},
                )
            except Exception as payout_error:
                logger.error(
                    "Failed to send payouts",
                    extra={
                        "error": str(payout_error),
                        "error_type": type(payout_error).__name__,
                        "owners_draw_sats": owners_draw,
                        "devs_donation_sats": devs_donation,
                    },
                )
                raise

    except Exception as e:
        logger.error(
            "Error in payout process",
            extra={"error": str(e), "error_type": type(e).__name__},
        )


# Periodic payout task
async def periodic_payout() -> None:
    """Periodically process payouts."""
    logger.info("Starting periodic payout task", extra={"interval_seconds": 300})
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await pay_out()
        except asyncio.CancelledError:
            logger.info("Periodic payout task cancelled")
            break
        except Exception as e:
            logger.error(
                "Error in periodic payout",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            # Continue running even if payout fails


async def credit_balance(cashu_token: str, key: ApiKey, session: AsyncSession) -> int:
    """Redeem a Cashu token and credit the amount to the API key balance."""
    logger.debug(
        "Starting token redemption",
        extra={
            "key_hash": key.hashed_key[:8] + "...",
            "token_preview": cashu_token[:20] + "..."
            if len(cashu_token) > 20
            else cashu_token,
        },
    )

    try:
        amount, unit = await wallet().redeem(cashu_token)
        logger.info(
            "Token redeemed successfully",
            extra={
                "amount": amount,
                "unit": unit,
                "key_hash": key.hashed_key[:8] + "...",
            },
        )
    except Exception as e:
        logger.error(
            "Token redemption failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "key_hash": key.hashed_key[:8] + "...",
                "token_preview": cashu_token[:20] + "..."
                if len(cashu_token) > 20
                else cashu_token,
            },
        )
        # Re-raise the exception so the caller can handle invalid tokens properly
        raise ValueError(f"Token redemption failed: {str(e)}")

    if amount <= 0:
        logger.warning(
            "Zero or negative amount redeemed",
            extra={
                "amount": amount,
                "unit": unit,
                "key_hash": key.hashed_key[:8] + "...",
            },
        )
        return 0

    if unit == "msat":
        amount_msats = amount
    else:
        amount_msats = amount * 1000

    logger.debug(
        "Crediting balance",
        extra={
            "amount_msats": amount_msats,
            "original_amount": amount,
            "unit": unit,
            "key_hash": key.hashed_key[:8] + "...",
        },
    )

    # Apply the balance change atomically to avoid race conditions when topping
    # up the same key concurrently.
    stmt = (
        update(ApiKey)
        .where(col(ApiKey.hashed_key) == key.hashed_key)
        .values(balance=col(ApiKey.balance) + amount_msats)
    )
    await session.exec(stmt)  # type: ignore[call-overload]
    await session.commit()
    await session.refresh(key)

    logger.info(
        "Balance credited successfully",
        extra={
            "credited_msats": amount_msats,
            "new_balance_msats": key.balance,
            "key_hash": key.hashed_key[:8] + "...",
        },
    )

    return amount_msats


async def check_for_refunds() -> None:
    """
    Periodically checks for API keys that are eligible for refunds and processes them.

    Raises:
        Exception: If an error occurs during the refund check process.
    """
    # Setting REFUND_PROCESSING_INTERVAL to 0 disables it
    if REFUND_PROCESSING_INTERVAL == 0:
        logger.info("Automatic refund processing is disabled")
        return

    logger.info(
        "Starting refund monitoring task",
        extra={"interval_seconds": REFUND_PROCESSING_INTERVAL},
    )

    while True:
        try:
            logger.debug("Checking for expired keys requiring refunds")
            async for session in get_session():
                result = await session.exec(select(ApiKey))
                keys = result.all()
                current_time = int(time.time())

                expired_keys = []
                for key in keys:
                    if (
                        key.balance > 0
                        and key.refund_address
                        and key.key_expiry_time
                        and key.key_expiry_time < current_time
                    ):
                        expired_keys.append(key)

                if expired_keys:
                    logger.info(
                        "Found expired keys for refund",
                        extra={
                            "expired_count": len(expired_keys),
                            "current_time": current_time,
                        },
                    )

                for key in expired_keys:
                    logger.info(
                        "Processing refund for expired key",
                        extra={
                            "key_hash": key.hashed_key[:8] + "...",
                            "balance_msats": key.balance,
                            "expiry_time": key.key_expiry_time,
                            "current_time": current_time,
                            "expired_seconds": current_time
                            - (key.key_expiry_time or 0),
                        },
                    )

                    try:
                        await refund_balance(key.balance, key, session)
                        await delete_key_if_zero_balance(key, session)
                        logger.info(
                            "Refund processed successfully",
                            extra={"key_hash": key.hashed_key[:8] + "..."},
                        )
                    except Exception as refund_error:
                        logger.error(
                            "Failed to process refund",
                            extra={
                                "error": str(refund_error),
                                "error_type": type(refund_error).__name__,
                                "key_hash": key.hashed_key[:8] + "...",
                                "balance_msats": key.balance,
                            },
                        )

            # Sleep for the specified interval before checking again
            await asyncio.sleep(REFUND_PROCESSING_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Refund monitoring task cancelled")
            break
        except Exception as e:
            logger.error(
                "Error during refund check",
                extra={"error": str(e), "error_type": type(e).__name__},
            )


async def refund_balance(amount_msats: int, key: ApiKey, session: AsyncSession) -> int:
    """Process a refund for an API key."""
    if amount_msats <= 0:
        amount_msats = key.balance

    logger.info(
        "Processing balance refund",
        extra={
            "amount_msats": amount_msats,
            "key_hash": key.hashed_key[:8] + "...",
            "refund_address": key.refund_address[:20] + "..."
            if key.refund_address and len(key.refund_address) > 20
            else key.refund_address,
        },
    )

    # Convert msats to sats for cashu wallet
    amount_sats = amount_msats // 1000
    if amount_sats == 0:
        logger.error(
            "Amount too small to refund",
            extra={
                "amount_msats": amount_msats,
                "amount_sats": amount_sats,
                "key_hash": key.hashed_key[:8] + "...",
            },
        )
        raise ValueError("Amount too small to refund (less than 1 sat)")

    # Atomically deduct the balance to avoid race conditions when multiple
    # refunds are triggered concurrently.
    stmt = (
        update(ApiKey)
        .where(col(ApiKey.hashed_key) == key.hashed_key)
        .where(col(ApiKey.balance) >= amount_msats)
        .values(balance=col(ApiKey.balance) - amount_msats)
    )
    result = await session.exec(stmt)  # type: ignore[call-overload]
    await session.commit()

    if result.rowcount == 0:
        logger.error(
            "Insufficient balance for refund",
            extra={
                "requested_msats": amount_msats,
                "key_hash": key.hashed_key[:8] + "...",
                "current_balance": key.balance,
            },
        )
        raise ValueError("Insufficient balance.")

    await session.refresh(key)
    await delete_key_if_zero_balance(key, session)

    if key.refund_address is None:
        logger.error(
            "Refund address not set", extra={"key_hash": key.hashed_key[:8] + "..."}
        )
        raise ValueError("Refund address not set.")

    try:
        result = await wallet().send_to_lnurl(key.refund_address, amount=amount_sats)
        logger.info(
            "Refund sent successfully",
            extra={
                "amount_sats": amount_sats,
                "refund_address": key.refund_address[:20] + "..."
                if len(key.refund_address) > 20
                else key.refund_address,
                "key_hash": key.hashed_key[:8] + "...",
                "transaction_result": str(result),
            },
        )
        return result
    except Exception as e:
        logger.error(
            "Failed to send refund",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "amount_sats": amount_sats,
                "refund_address": key.refund_address,
                "key_hash": key.hashed_key[:8] + "...",
            },
        )
        raise


async def x_cashu_refund(key: ApiKey, session: AsyncSession, unit: CurrencyUnit) -> str:
    """Process an X-Cashu refund token."""
    logger.info(
        "Processing X-Cashu refund",
        extra={
            "balance_msats": key.balance,
            "unit": unit,
            "key_hash": key.hashed_key[:8] + "...",
        },
    )

    try:
        refund_token = await wallet().send(key.balance, unit=unit)
        logger.info(
            "X-Cashu refund token created",
            extra={
                "amount": key.balance,
                "unit": unit,
                "key_hash": key.hashed_key[:8] + "...",
                "token_preview": refund_token[:20] + "..."
                if len(refund_token) > 20
                else refund_token,
            },
        )

        await session.delete(key)
        await session.commit()

        logger.info(
            "X-Cashu refund completed", extra={"key_hash": key.hashed_key[:8] + "..."}
        )

        return refund_token
    except Exception as e:
        logger.error(
            "Failed to create X-Cashu refund",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "balance": key.balance,
                "unit": unit,
                "key_hash": key.hashed_key[:8] + "...",
            },
        )
        raise


async def redeem(cashu_token: str, lnurl: str) -> int:
    """Redeem a Cashu token and send to LNURL."""
    logger.info(
        "Starting token redemption for LNURL",
        extra={
            "token_preview": cashu_token[:20] + "..."
            if len(cashu_token) > 20
            else cashu_token,
            "lnurl_preview": lnurl[:20] + "..." if len(lnurl) > 20 else lnurl,
        },
    )

    try:
        amount, unit = await wallet().redeem(cashu_token)
        logger.info("Token redeemed for LNURL", extra={"amount": amount, "unit": unit})

        unit = cast(CurrencyUnit, unit)
        result = await wallet().send_to_lnurl(lnurl, amount=amount, unit=unit)

        logger.info(
            "Successfully sent to LNURL",
            extra={
                "amount": amount,
                "unit": unit,
                "lnurl_preview": lnurl[:20] + "..." if len(lnurl) > 20 else lnurl,
                "transaction_result": str(result),
            },
        )

        return amount
    except Exception as e:
        logger.error(
            "Failed to redeem and send to LNURL",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "token_preview": cashu_token[:20] + "..."
                if len(cashu_token) > 20
                else cashu_token,
                "lnurl_preview": lnurl[:20] + "..." if len(lnurl) > 20 else lnurl,
            },
        )
        raise
