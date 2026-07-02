from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from netagent_db.models import (
    AdminUser,
    Device,
    Payment,
    Plan,
    Subscription,
    SupportTicket,
    User,
)


@dataclass(slots=True)
class SupportTicketRow:
    id: int
    user_id: int
    user_email: str | None
    telegram_id: int | None
    category: str | None
    message: str
    admin_reply: str | None
    status: str
    created_at: datetime
    replied_at: datetime | None


@dataclass(slots=True)
class DashboardStats:
    users_total: int
    users_with_telegram: int
    subscriptions_active: int
    subscriptions_vpn: int
    subscriptions_ai: int
    subscriptions_bundle: int
    devices_active: int
    devices_suspended: int
    payments_total: int
    revenue_rub: float
    support_open: int
    plans_active: int


@dataclass(slots=True)
class UserRow:
    id: int
    email: str | None
    telegram_id: int | None
    status: str
    created_at: datetime
    active_plan: str | None


@dataclass(slots=True)
class PaymentRow:
    id: int
    user_email: str | None
    plan_name: str
    amount: float
    status: str
    provider: str
    created_at: datetime


class AdminStatsService:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def dashboard(self) -> DashboardStats:
        with self._session_factory() as session:
            now = datetime.now().astimezone()
            users_total = session.scalar(select(func.count()).select_from(User)) or 0
            users_with_telegram = session.scalar(
                select(func.count()).select_from(User).where(User.telegram_id.is_not(None))
            ) or 0
            subscriptions_active = session.scalar(
                select(func.count())
                .select_from(Subscription)
                .where(
                    Subscription.status == "active",
                    Subscription.expires_at.is_not(None),
                    Subscription.expires_at > now,
                )
            ) or 0
            subscriptions_vpn = self._count_subs_by_type(session, "vpn", now)
            subscriptions_ai = self._count_subs_by_type(session, "ai", now)
            subscriptions_bundle = self._count_subs_by_type(session, "bundle", now)
            devices_active = session.scalar(
                select(func.count()).select_from(Device).where(Device.status == "active")
            ) or 0
            devices_suspended = session.scalar(
                select(func.count()).select_from(Device).where(Device.status == "suspended")
            ) or 0
            payments_total = session.scalar(select(func.count()).select_from(Payment)) or 0
            revenue = session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "succeeded")
            )
            support_open = session.scalar(
                select(func.count()).select_from(SupportTicket).where(SupportTicket.status == "open")
            ) or 0
            plans_active = session.scalar(
                select(func.count()).select_from(Plan).where(Plan.is_active.is_(True))
            ) or 0
            return DashboardStats(
                users_total=users_total,
                users_with_telegram=users_with_telegram,
                subscriptions_active=subscriptions_active,
                subscriptions_vpn=subscriptions_vpn,
                subscriptions_ai=subscriptions_ai,
                subscriptions_bundle=subscriptions_bundle,
                devices_active=devices_active,
                devices_suspended=devices_suspended,
                payments_total=payments_total,
                revenue_rub=float(revenue or 0),
                support_open=support_open,
                plans_active=plans_active,
            )

    def list_users(self, limit: int = 100) -> list[UserRow]:
        with self._session_factory() as session:
            users = session.scalars(select(User).order_by(User.created_at.desc()).limit(limit)).all()
            rows: list[UserRow] = []
            for user in users:
                sub = session.scalar(
                    select(Subscription)
                    .join(Plan, Subscription.plan_id == Plan.id)
                    .where(Subscription.user_id == user.id, Subscription.status == "active")
                    .order_by(Subscription.expires_at.desc())
                )
                plan_name = None
                if sub:
                    plan = session.get(Plan, sub.plan_id)
                    plan_name = plan.name if plan else None
                rows.append(
                    UserRow(
                        id=user.id,
                        email=user.email,
                        telegram_id=user.telegram_id,
                        status=user.status,
                        created_at=user.created_at,
                        active_plan=plan_name,
                    )
                )
            return rows

    def list_payments(self, limit: int = 50) -> list[PaymentRow]:
        with self._session_factory() as session:
            payments = session.scalars(
                select(Payment).order_by(Payment.created_at.desc()).limit(limit)
            ).all()
            rows: list[PaymentRow] = []
            for payment in payments:
                user = session.get(User, payment.user_id)
                plan = session.get(Plan, payment.plan_id)
                rows.append(
                    PaymentRow(
                        id=payment.id,
                        user_email=user.email if user else None,
                        plan_name=plan.name if plan else "?",
                        amount=float(payment.amount or 0),
                        status=payment.status,
                        provider=payment.provider,
                        created_at=payment.created_at,
                    )
                )
            return rows

    def list_support_tickets(self, limit: int = 50) -> list[SupportTicketRow]:
        with self._session_factory() as session:
            rows = session.execute(
                select(SupportTicket, User.email)
                .join(User, SupportTicket.user_id == User.id)
                .order_by(SupportTicket.created_at.desc())
                .limit(limit)
            ).all()
            return [
                SupportTicketRow(
                    id=t.id,
                    user_id=t.user_id,
                    user_email=email,
                    telegram_id=t.telegram_id,
                    category=t.category,
                    message=t.message,
                    admin_reply=t.admin_reply,
                    status=t.status,
                    created_at=t.created_at,
                    replied_at=t.replied_at,
                )
                for t, email in rows
            ]

    def get_support_ticket_row(self, ticket_id: int) -> SupportTicketRow | None:
        with self._session_factory() as session:
            row = session.execute(
                select(SupportTicket, User.email)
                .join(User, SupportTicket.user_id == User.id)
                .where(SupportTicket.id == ticket_id)
            ).first()
            if not row:
                return None
            t, email = row
            return SupportTicketRow(
                id=t.id,
                user_id=t.user_id,
                user_email=email,
                telegram_id=t.telegram_id,
                category=t.category,
                message=t.message,
                admin_reply=t.admin_reply,
                status=t.status,
                created_at=t.created_at,
                replied_at=t.replied_at,
            )

    def list_plans(self) -> list[Plan]:
        with self._session_factory() as session:
            return list(session.scalars(select(Plan).order_by(Plan.sort_order)).all())

    def _count_subs_by_type(self, session: Session, product_type: str, now: datetime) -> int:
        return (
            session.scalar(
                select(func.count())
                .select_from(Subscription)
                .join(Plan, Subscription.plan_id == Plan.id)
                .where(
                    Subscription.status == "active",
                    Plan.product_type == product_type,
                    Subscription.expires_at.is_not(None),
                    Subscription.expires_at > now,
                )
            )
            or 0
        )

    def get_admin_by_email(self, email: str) -> AdminUser | None:
        with self._session_factory() as session:
            return session.scalar(select(AdminUser).where(AdminUser.email == email))
