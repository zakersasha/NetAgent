import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from bot.billing import BillingClient
from bot.keyboards import subscription_reminder_keyboard
from bot.messages import subscription_expiry_day_text, subscription_reminder_2d_text
from netagent_db.models import Plan, Subscription, User

logger = logging.getLogger(__name__)

REMINDER_CHECK_INTERVAL_SECONDS = 3600


def _due_reminders(session: Session, now: datetime) -> list[tuple[Subscription, str]]:
    rows = session.scalars(
        select(Subscription)
        .join(User, Subscription.user_id == User.id)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(
            Subscription.status == "active",
            Subscription.expires_at.is_not(None),
            Subscription.expires_at > now,
            User.telegram_id.is_not(None),
        )
        .options(joinedload(Subscription.plan), joinedload(Subscription.user))
    ).all()

    due: list[tuple[Subscription, str]] = []
    for subscription in rows:
        expires_at = subscription.expires_at
        if expires_at is None:
            continue
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        days_left = max(0, (expires_at - now).days)

        if days_left == 2 and not subscription.reminder_2d_sent:
            due.append((subscription, "2d"))
        elif days_left == 0 and not subscription.reminder_0d_sent:
            due.append((subscription, "0d"))

    return due


async def _send_reminder(
    bot: Bot,
    session_factory: Callable[[], Session],
    billing: BillingClient,
    subscription: Subscription,
    kind: str,
) -> None:
    telegram_id = subscription.user.telegram_id
    if not telegram_id:
        return

    plan = subscription.plan
    expires_at = subscription.expires_at
    if expires_at is None:
        return
    days_left = billing.days_left(expires_at)
    expires = expires_at.strftime("%d.%m.%Y")

    if kind == "2d":
        text = subscription_reminder_2d_text(plan.name, expires, days_left)
    else:
        text = subscription_expiry_day_text(plan.name, expires)

    markup = subscription_reminder_keyboard(plan.slug, plan.price_rub)
    try:
        await bot.send_message(telegram_id, text, reply_markup=markup)
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.warning("Reminder to %s failed: %s", telegram_id, exc)
        return

    with session_factory() as session:
        sub = session.get(Subscription, subscription.id)
        if not sub:
            return
        if kind == "2d":
            sub.reminder_2d_sent = True
        else:
            sub.reminder_0d_sent = True
        session.commit()


async def subscription_reminder_loop(
    bot: Bot,
    billing: BillingClient,
    session_factory: Callable[[], Session],
    timezone: str,
    interval_seconds: int = REMINDER_CHECK_INTERVAL_SECONDS,
) -> None:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone)
    logger.info("Subscription reminders: every %s s", interval_seconds)

    while True:
        try:
            now = datetime.now(tz)
            with session_factory() as session:
                due = _due_reminders(session, now)

            for subscription, kind in due:
                await _send_reminder(bot, session_factory, billing, subscription, kind)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Subscription reminder check failed")

        await asyncio.sleep(interval_seconds)
