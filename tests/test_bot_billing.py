from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from bot.billing import BillingClient, BillingError
from netagent_db.base import Base
from netagent_db.models import Subscription, User
from netagent_db.seed import seed_plans

PUBLIC_KEY = "YTQ_dIa_739_d6x7OUAd3XjMbpX6UOnWBMkGVtEhi18"


@pytest.fixture
def billing_client() -> BillingClient:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as session:
        seed_plans(session)
    return BillingClient(
        session_factory=session_factory,
        public_host="45.93.137.80",
        reality_public_key=PUBLIC_KEY,
        reality_short_id="6ba85179e30d4fc3",
    )


def test_mock_payment_creates_subscription_and_key(billing_client: BillingClient) -> None:
    subscription = billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")

    assert subscription.plan.slug == "connect_plus"
    assert subscription.plan.traffic_limit_gb == 80
    assert len(subscription.devices) == 1
    assert subscription.devices[0].xray_email == "123_vpn"


def test_ensure_vpn_key_creates_single_key(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")

    key = billing_client.ensure_vpn_key(telegram_id=123)
    again = billing_client.ensure_vpn_key(telegram_id=123)

    assert key.xray_email == "123_vpn"
    assert key.xray_uuid == again.xray_uuid
    assert "pbk=" in key.connection_uri


def test_regenerate_vpn_key_changes_uuid(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")
    first = billing_client.ensure_vpn_key(telegram_id=123)
    second = billing_client.regenerate_vpn_key(telegram_id=123)

    assert first.xray_uuid != second.xray_uuid
    assert second.xray_email == "123_vpn"


def test_repeated_payment_updates_plan_and_keeps_key(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")
    device = billing_client.ensure_vpn_key(telegram_id=123)

    _set_subscription_days_left(billing_client, telegram_id=123, days_left=3)

    subscription = billing_client.activate_mock_payment(telegram_id=123, plan_slug="combo_max")

    assert subscription.plan.slug == "combo_max"
    assert len(subscription.devices) == 1
    assert subscription.devices[0].xray_uuid == device.xray_uuid
    assert subscription.traffic_limit_gb == 150


def _set_subscription_days_left(billing_client: BillingClient, telegram_id: int, days_left: int) -> None:
    with billing_client._session_factory() as session:  # noqa: SLF001
        user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        assert user is not None
        sub = session.scalar(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
        )
        assert sub is not None
        sub.expires_at = datetime.now(billing_client.timezone) + timedelta(days=days_left)
        session.commit()


def test_early_renewal_blocked_when_more_than_5_days_left(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")

    can_pay, reason = billing_client.can_purchase_plan(123, "connect_plus")
    assert not can_pay
    assert reason is not None
    assert "5" in reason

    with pytest.raises(BillingError, match="5"):
        billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")


def test_early_renewal_allowed_within_5_days(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")
    _set_subscription_days_left(billing_client, telegram_id=123, days_left=4)

    can_pay, reason = billing_client.can_purchase_plan(123, "connect_plus")
    assert can_pay
    assert reason is None

    subscription = billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")
    assert subscription.plan.slug == "connect_plus"


def test_unknown_plan_is_rejected(billing_client: BillingClient) -> None:
    with pytest.raises(Exception, match="Unknown plan"):
        billing_client.activate_mock_payment(telegram_id=123, plan_slug="unknown")


def test_combo_grants_ai_and_vpn(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="combo")

    assert billing_client.get_subscription(123) is not None
    assert billing_client.get_ai_subscription(123) is not None

    status = billing_client.get_account_status(123)
    assert status.has_ai_unlimited
    assert status.vpn_subscription is not None
