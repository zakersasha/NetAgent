import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from bot.ai_service import AiChatService, AiQuotaExceededError
from netagent_db.base import Base
from netagent_db.seed import seed_plans


@pytest.fixture
def ai_service() -> AiChatService:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as session:
        seed_plans(session)

    openai = MagicMock()
    openai.complete.return_value = "AI reply"
    return AiChatService(
        session_factory=session_factory,
        openai_client=openai,
        free_daily_limit=3,
    )


def test_free_quota_blocks_after_limit(ai_service: AiChatService) -> None:
    for _ in range(3):
        assert ai_service.complete_message(42, "hi") == "AI reply"

    with pytest.raises(AiQuotaExceededError):
        ai_service.complete_message(42, "again")


def test_ai_subscription_unlimited(ai_service: AiChatService) -> None:
    from bot.billing import BillingClient

    session_factory = ai_service._session_factory
    billing = BillingClient(session_factory=session_factory, public_host="1.2.3.4")
    billing.activate_mock_payment(99, "ai_plus")

    for _ in range(5):
        assert ai_service.complete_message(99, "msg") == "AI reply"

    assert ai_service.remaining_free_messages(99) == -1
