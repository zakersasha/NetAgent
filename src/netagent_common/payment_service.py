from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.billing import BillingClient, BillingError, SubscriptionView
from netagent_common.yookassa_client import YooKassaClient, YooKassaError
from netagent_db.models import Payment, Plan, User


@dataclass(frozen=True)
class CreatedPayment:
    payment_id: int
    confirmation_url: str
    external_id: str


@dataclass(frozen=True)
class FulfillResult:
    payment_id: int
    telegram_id: int | None
    subscription: SubscriptionView


class PaymentService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        billing: BillingClient,
        yookassa: YooKassaClient,
        *,
        service_name: str,
        return_url: str,
    ) -> None:
        self._session_factory = session_factory
        self._billing = billing
        self._yookassa = yookassa
        self._service_name = service_name
        self._return_url = return_url

    def create_bot_payment(self, telegram_id: int, plan_slug: str) -> CreatedPayment:
        with self._session_factory() as session:
            plan = self._get_active_plan(session, plan_slug)
            user = self._billing._get_or_create_user(session, telegram_id)  # noqa: SLF001
            allowed, reason = self._billing._can_purchase_plan(session, user.id, plan)  # noqa: SLF001
            if not allowed:
                raise BillingError(reason or "Оплата сейчас недоступна")
            return self._create_yookassa_payment(session, user, plan, source="bot")

    def create_web_payment(self, user_id: int, plan_slug: str) -> CreatedPayment:
        with self._session_factory() as session:
            plan = self._get_active_plan(session, plan_slug)
            user = session.get(User, user_id)
            if not user:
                raise BillingError("User not found")
            allowed, reason = self._billing._can_purchase_plan(session, user.id, plan)  # noqa: SLF001
            if not allowed:
                raise BillingError(reason or "Оплата сейчас недоступна")
            return self._create_yookassa_payment(session, user, plan, source="web")

    def handle_yookassa_webhook(self, payload: dict) -> FulfillResult | None:
        event = payload.get("event")
        payment_obj = payload.get("object") or {}
        external_id = payment_obj.get("id")
        if not external_id:
            return None

        if event == "payment.canceled":
            self._mark_canceled(external_id)
            return None

        if event != "payment.succeeded":
            return None

        metadata = payment_obj.get("metadata") or {}
        payment_id = int(metadata.get("payment_id") or 0)
        if payment_id:
            return self._fulfill(payment_id, external_id, payment_obj)

        return self._fulfill_by_external_id(external_id, payment_obj)

    def _create_yookassa_payment(
        self,
        session: Session,
        user: User,
        plan: Plan,
        *,
        source: str,
    ) -> CreatedPayment:
        payment = Payment(
            user_id=user.id,
            plan_id=plan.id,
            provider="yookassa",
            amount=plan.price_rub,
            currency="RUB",
            status="pending",
        )
        session.add(payment)
        session.flush()

        metadata = {
            "payment_id": str(payment.id),
            "plan_slug": plan.slug,
            "user_id": str(user.id),
            "source": source,
        }
        if user.telegram_id:
            metadata["telegram_id"] = str(user.telegram_id)

        try:
            yk_payment = self._yookassa.create_payment(
                amount_rub=Decimal(plan.price_rub),
                description=f"Подписка {self._service_name}: {plan.name}",
                return_url=self._return_url,
                metadata=metadata,
                idempotence_key=f"netagent-pay-{payment.id}",
            )
        except YooKassaError as exc:
            payment.status = "failed"
            session.commit()
            raise BillingError(str(exc)) from exc

        confirmation = yk_payment.get("confirmation") or {}
        confirmation_url = confirmation.get("confirmation_url")
        external_id = yk_payment.get("id")
        if not confirmation_url or not external_id:
            payment.status = "failed"
            session.commit()
            raise BillingError("ЮKassa не вернула ссылку на оплату")

        payment.external_id = external_id
        payment.confirmation_url = confirmation_url
        session.commit()

        return CreatedPayment(
            payment_id=payment.id,
            confirmation_url=confirmation_url,
            external_id=external_id,
        )

    def _fulfill(
        self,
        payment_id: int,
        external_id: str,
        payment_obj: dict,
    ) -> FulfillResult | None:
        with self._session_factory() as session:
            payment = session.get(Payment, payment_id)
            if not payment:
                return None
            if payment.status == "succeeded":
                return self._build_fulfill_result(session, payment)
            if payment.status != "pending":
                return None
            if payment.external_id and payment.external_id != external_id:
                return None

            plan = session.get(Plan, payment.plan_id)
            if not plan or not self._amount_matches(plan, payment_obj):
                return None

            payment.external_id = external_id
            session.commit()

        subscription = self._billing.fulfill_payment(payment_id)
        if not subscription:
            return None

        with self._session_factory() as session:
            payment = session.get(Payment, payment_id)
            if not payment:
                return None
            return self._build_fulfill_result(session, payment, subscription)

    def _fulfill_by_external_id(self, external_id: str, payment_obj: dict) -> FulfillResult | None:
        with self._session_factory() as session:
            payment = session.scalar(select(Payment).where(Payment.external_id == external_id))
            if not payment:
                return None
        return self._fulfill(payment.id, external_id, payment_obj)

    def _mark_canceled(self, external_id: str) -> None:
        with self._session_factory() as session:
            payment = session.scalar(select(Payment).where(Payment.external_id == external_id))
            if payment and payment.status == "pending":
                payment.status = "canceled"
                session.commit()

    def _build_fulfill_result(
        self,
        session: Session,
        payment: Payment,
        subscription: SubscriptionView | None = None,
    ) -> FulfillResult | None:
        user = session.get(User, payment.user_id)
        if not user:
            return None
        if subscription is None:
            plan = session.get(Plan, payment.plan_id)
            if not plan:
                return None
            line = "vpn" if plan.product_type in ("vpn", "bundle") else "ai"
            if user.telegram_id:
                subscription = self._billing._load_subscription_view(  # noqa: SLF001
                    session, user.telegram_id, line=line
                )
            else:
                subscription = self._billing._load_subscription_view_for_user(  # noqa: SLF001
                    session, user.id, line=line
                )
        if not subscription:
            return None
        return FulfillResult(
            payment_id=payment.id,
            telegram_id=user.telegram_id,
            subscription=subscription,
        )

    @staticmethod
    def _get_active_plan(session: Session, plan_slug: str) -> Plan:
        plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
        if not plan:
            raise BillingError(f"Unknown plan: {plan_slug}")
        return plan

    @staticmethod
    def _amount_matches(plan: Plan, payment_obj: dict) -> bool:
        amount = payment_obj.get("amount") or {}
        try:
            paid = Decimal(str(amount.get("value", "0"))).quantize(Decimal("0.01"))
            expected = Decimal(plan.price_rub).quantize(Decimal("0.01"))
        except Exception:
            return False
        return paid == expected and amount.get("currency") == "RUB"
