import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from bot.billing import BillingClient

logger = logging.getLogger(__name__)

EXPIRY_CHECK_INTERVAL_SECONDS = 6 * 60 * 60  # 6 hours


async def subscription_expiration_loop(
    billing: BillingClient,
    session_factory: Callable[[], Session],
    timezone: str,
    interval_seconds: int = EXPIRY_CHECK_INTERVAL_SECONDS,
) -> None:
    del session_factory, timezone
    logger.info("Subscription expiration check: every %s s", interval_seconds)

    while True:
        try:
            expired = await asyncio.to_thread(billing.expire_due_subscriptions)
            if expired:
                logger.info("Expired %s subscription(s)", expired)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Subscription expiration check failed")

        await asyncio.sleep(interval_seconds)
