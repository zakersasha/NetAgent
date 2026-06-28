import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.billing import (
    BillingClient,
    DeviceAlreadyExistsError,
    DeviceLimitExceededError,
)
from netagent_db.base import Base
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


def test_mock_payment_activates_plan_without_devices(billing_client: BillingClient) -> None:
    subscription = billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")

    assert subscription.plan.slug == "connect_plus"
    assert subscription.plan.device_limit == 2
    assert subscription.devices == ()


def test_add_device_creates_unique_uuid_and_email(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")

    phone = billing_client.add_device(telegram_id=123, preset_slug="iphone")
    macbook = billing_client.add_device(telegram_id=123, preset_slug="macbook")

    assert phone.xray_email == "123_phone"
    assert macbook.xray_email == "123_macbook"
    assert phone.xray_uuid != macbook.xray_uuid
    assert "pbk=" in phone.connection_uri
    assert "45.93.137.80:443" in phone.connection_uri


def test_device_limit_is_enforced(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")
    billing_client.add_device(telegram_id=123, preset_slug="iphone")

    with pytest.raises(DeviceLimitExceededError, match="Лимит устройств"):
        billing_client.add_device(telegram_id=123, preset_slug="android")


def test_duplicate_device_preset_is_rejected(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="combo_max")
    billing_client.add_device(telegram_id=123, preset_slug="iphone")

    with pytest.raises(DeviceAlreadyExistsError):
        billing_client.add_device(telegram_id=123, preset_slug="iphone")


def test_repeated_payment_updates_plan_and_keeps_devices(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect")
    device = billing_client.add_device(telegram_id=123, preset_slug="iphone")

    subscription = billing_client.activate_mock_payment(telegram_id=123, plan_slug="combo_max")

    assert subscription.plan.slug == "combo_max"
    assert len(subscription.devices) == 1
    assert subscription.devices[0].xray_uuid == device.xray_uuid


def test_remove_device_deletes_from_subscription(billing_client: BillingClient) -> None:
    billing_client.activate_mock_payment(telegram_id=123, plan_slug="connect_plus")
    device = billing_client.add_device(telegram_id=123, preset_slug="iphone")

    billing_client.remove_device(telegram_id=123, device_id=device.id)
    subscription = billing_client.get_subscription(telegram_id=123)

    assert subscription is not None
    assert subscription.devices == ()


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
