from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from bot.billing import BillingClient
from netagent_common.payment_service import PaymentService
from netagent_common.yookassa_client import YooKassaClient
from netagent_db.base import Base
from netagent_db.models import Payment, User
from netagent_db.seed import seed_plans

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


def test_yookassa_create_payment_stores_pending_record(
    session_factory,
    billing_client: BillingClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yookassa = YooKassaClient("shop", "secret")
    service = PaymentService(
        session_factory=session_factory,
        billing=billing_client,
        yookassa=yookassa,
        service_name="NetAgent",
        return_url="https://example.com/cabinet?paid=1",
    )

    monkeypatch.setattr(
        yookassa,
        "create_payment",
        lambda **kwargs: {
            "id": "yk-123",
            "confirmation": {"confirmation_url": "https://pay.example/123"},
        },
    )

    created = service.create_bot_payment(telegram_id=777, plan_slug="connect")

    assert created.confirmation_url == "https://pay.example/123"
    assert created.external_id == "yk-123"

    with session_factory() as session:
        payment = session.get(Payment, created.payment_id)
        assert payment is not None
        assert payment.status == "pending"
        assert payment.provider == "yookassa"
        assert payment.external_id == "yk-123"


def test_yookassa_webhook_fulfills_subscription(
    session_factory,
    billing_client: BillingClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yookassa = YooKassaClient("shop", "secret")
    service = PaymentService(
        session_factory=session_factory,
        billing=billing_client,
        yookassa=yookassa,
        service_name="NetAgent",
        return_url="https://example.com/cabinet?paid=1",
    )

    monkeypatch.setattr(
        yookassa,
        "create_payment",
        lambda **kwargs: {
            "id": "yk-456",
            "confirmation": {"confirmation_url": "https://pay.example/456"},
        },
    )

    created = service.create_bot_payment(telegram_id=888, plan_slug="connect")

    payload = {
        "event": "payment.succeeded",
        "object": {
            "id": "yk-456",
            "status": "succeeded",
            "amount": {"value": "149.00", "currency": "RUB"},
            "metadata": {"payment_id": str(created.payment_id)},
        },
    }

    result = service.handle_yookassa_webhook(payload)

    assert result is not None
    assert result.telegram_id == 888
    assert result.subscription.plan.slug == "connect"

    with session_factory() as session:
        payment = session.get(Payment, created.payment_id)
        assert payment is not None
        assert payment.status == "succeeded"
        assert payment.subscription_id is not None


def test_yookassa_webhook_is_idempotent(
    session_factory,
    billing_client: BillingClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yookassa = YooKassaClient("shop", "secret")
    service = PaymentService(
        session_factory=session_factory,
        billing=billing_client,
        yookassa=yookassa,
        service_name="NetAgent",
        return_url="https://example.com/cabinet?paid=1",
    )

    monkeypatch.setattr(
        yookassa,
        "create_payment",
        lambda **kwargs: {
            "id": "yk-789",
            "confirmation": {"confirmation_url": "https://pay.example/789"},
        },
    )

    created = service.create_bot_payment(telegram_id=999, plan_slug="lite_ai")
    payload = {
        "event": "payment.succeeded",
        "object": {
            "id": "yk-789",
            "status": "succeeded",
            "amount": {"value": "99.00", "currency": "RUB"},
            "metadata": {"payment_id": str(created.payment_id)},
        },
    }

    first = service.handle_yookassa_webhook(payload)
    second = service.handle_yookassa_webhook(payload)

    assert first is not None
    assert second is not None
    assert first.payment_id == second.payment_id

    with session_factory() as session:
        user = session.scalar(select(User).where(User.telegram_id == 999))
        assert user is not None
        payments = session.scalars(select(Payment).where(Payment.user_id == user.id)).all()
        assert len(payments) == 1
        assert payments[0].status == "succeeded"


def test_yookassa_format_amount() -> None:
    assert YooKassaClient._format_amount(Decimal("149")) == "149.00"
