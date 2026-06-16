from bot.billing import MockBillingClient

PUBLIC_KEY = "YTQ_dIa_739_d6x7OUAd3XjMbpX3UOnWBMkGVtEhi18"


def billing_client() -> MockBillingClient:
    return MockBillingClient(
        public_host="45.93.137.80",
        reality_public_key=PUBLIC_KEY,
        reality_short_id="6ba85179e30d4fc3",
    )


def test_mock_payment_activates_monthly_subscription() -> None:
    billing = billing_client()

    subscription = billing.activate_mock_payment(telegram_id=123, plan_slug="standard")

    assert subscription.plan.slug == "standard"
    assert subscription.plan.device_limit == 2
    assert subscription.xray_email == "user_tg_123@netagent.local"
    assert "pbk=" in subscription.connection_uri
    assert "45.93.137.80:443" in subscription.connection_uri


def test_repeated_payment_keeps_same_uuid_and_updates_plan() -> None:
    billing = billing_client()

    first = billing.activate_mock_payment(telegram_id=123, plan_slug="start")
    second = billing.activate_mock_payment(telegram_id=123, plan_slug="family")

    assert second.xray_uuid == first.xray_uuid
    assert second.plan.slug == "family"
    assert second.plan.device_limit == 3


def test_unknown_plan_is_rejected() -> None:
    billing = billing_client()

    try:
        billing.activate_mock_payment(telegram_id=123, plan_slug="unknown")
    except ValueError as exc:
        assert "Unknown plan" in str(exc)
    else:
        raise AssertionError("Unknown plan must fail")
