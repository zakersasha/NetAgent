"""Web user registration and mock payment."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.billing import BillingClient
from netagent_db.base import Base
from netagent_db.seed import seed_plans
from webapp.users import AuthError, register_user

PUBLIC_KEY = "YTQ_dIa_739_d6x7OUAd3XjMbpX6UOnWBMkGVtEhi18"


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with factory() as session:
        seed_plans(session)
    return factory


@pytest.fixture
def billing_client(session_factory) -> BillingClient:
    return BillingClient(
        session_factory=session_factory,
        public_host="45.93.137.80",
        reality_public_key=PUBLIC_KEY,
        reality_short_id="6ba85179e30d4fc3",
    )


def test_register_user(session_factory) -> None:
    with session_factory() as session:
        user = register_user(session, "test@example.com", "password123")
        assert user.email == "test@example.com"
        assert user.password_hash


def test_register_duplicate_email(session_factory) -> None:
    with session_factory() as session:
        register_user(session, "dup@example.com", "password123")
    with session_factory() as session:
        with pytest.raises(AuthError, match="зарегистрирован"):
            register_user(session, "dup@example.com", "otherpass99")


def test_web_mock_payment_creates_key(billing_client: BillingClient, session_factory) -> None:
    with session_factory() as session:
        user = register_user(session, "web@example.com", "password123")

    sub = billing_client.activate_mock_payment_for_user(user.id, "connect")
    assert sub.plan.slug == "connect"
    assert len(sub.devices) == 1
    assert sub.devices[0].xray_email == f"u{user.id}_vpn"
