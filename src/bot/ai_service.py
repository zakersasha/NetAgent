from collections.abc import Callable
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from netagent_common.openai_client import OpenAIChatClient, OpenAIClientError
from netagent_db.models import AiDailyUsage, Plan, Subscription, User


class AiQuotaExceededError(ValueError):
    """Free daily AI message limit reached."""


class AiChatService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        openai_client: OpenAIChatClient,
        timezone: str = "Europe/Moscow",
        free_daily_limit: int = 3,
    ) -> None:
        self._session_factory = session_factory
        self._openai = openai_client
        self._timezone = ZoneInfo(timezone)
        self._free_daily_limit = max(1, free_daily_limit)

    def has_ai_subscription(self, telegram_id: int) -> bool:
        with self._session_factory() as session:
            return self._get_active_ai_subscription(session, telegram_id) is not None

    def remaining_free_messages(self, telegram_id: int) -> int:
        if self.has_ai_subscription(telegram_id):
            return -1
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
            if not user:
                return self._free_daily_limit
            used = self._usage_count(session, user.id, self._today())
            return max(0, self._free_daily_limit - used)

    def complete_message(self, telegram_id: int, text: str) -> str:
        with self._session_factory() as session:
            user = self._get_or_create_user(session, telegram_id)
            unlimited = self._get_active_ai_subscription(session, telegram_id) is not None
            today = self._today()

            if not unlimited:
                used = self._usage_count(session, user.id, today)
                if used >= self._free_daily_limit:
                    raise AiQuotaExceededError(
                        f"Лимит {self._free_daily_limit} сообщений в день. "
                        "Оформите AI Plus для безлимита."
                    )
                self._increment_usage(session, user.id, today)

            session.commit()

        try:
            return self._openai.complete(text)
        except OpenAIClientError as exc:
            raise RuntimeError(str(exc)) from exc

    def _today(self) -> date:
        return datetime.now(self._timezone).date()

    def _get_or_create_user(self, session: Session, telegram_id: int) -> User:
        user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            return user
        user = User(telegram_id=telegram_id, status="active")
        session.add(user)
        session.flush()
        return user

    def _get_active_ai_subscription(self, session: Session, telegram_id: int) -> Subscription | None:
        now = datetime.now(self._timezone)
        return session.scalar(
            select(Subscription)
            .join(User, Subscription.user_id == User.id)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                User.telegram_id == telegram_id,
                Subscription.status == "active",
                Plan.product_type == "ai",
                Subscription.expires_at.is_not(None),
                Subscription.expires_at > now,
            )
            .order_by(Subscription.expires_at.desc())
        )

    def _usage_count(self, session: Session, user_id: int, usage_date: date) -> int:
        row = session.scalar(
            select(AiDailyUsage).where(
                AiDailyUsage.user_id == user_id,
                AiDailyUsage.usage_date == usage_date,
            )
        )
        return row.message_count if row else 0

    def _increment_usage(self, session: Session, user_id: int, usage_date: date) -> None:
        row = session.scalar(
            select(AiDailyUsage).where(
                AiDailyUsage.user_id == user_id,
                AiDailyUsage.usage_date == usage_date,
            )
        )
        if row:
            row.message_count += 1
            return
        session.add(
            AiDailyUsage(
                user_id=user_id,
                usage_date=usage_date,
                message_count=1,
            )
        )
