from bot.billing import MockBillingClient


def test_mock_payment_activates_monthly_subscription() -> None:
    billing = MockBillingClient(public_host="45.93.137.80")

    subscription = billing.activate_mock_payment(telegram_id=123, plan_slug="standard")

    assert subscription.plan.slug == "standard"
    assert subscription.plan.device_limit == 2
    assert subscription.xray_email == "user_tg_123@netagent.local"
    assert "45.93.137.80:443" in subscription.connection_uri


def test_repeated_payment_keeps_same_uuid_and_updates_plan() -> None:
    billing = MockBillingClient(public_host="45.93.137.80")

    first = billing.activate_mock_payment(telegram_id=123, plan_slug="start")
    second = billing.activate_mock_payment(telegram_id=123, plan_slug="family")

    assert second.xray_uuid == first.xray_uuid
    assert second.plan.slug == "family"
    assert second.plan.device_limit == 3


def test_unknown_plan_is_rejected() -> None:
    billing = MockBillingClient(public_host="45.93.137.80")

    try:
        billing.activate_mock_payment(telegram_id=123, plan_slug="unknown")
    except ValueError as exc:
        assert "Unknown plan" in str(exc)
    else:
        raise AssertionError("Unknown plan must fail")
