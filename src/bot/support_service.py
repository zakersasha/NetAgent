from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from netagent_db.models import SupportTicket, User


class SupportService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def create_ticket(
        self,
        telegram_id: int,
        message: str,
        category: str | None = None,
    ) -> SupportTicket:
        text = message.strip()
        if not text:
            raise ValueError("Пустое сообщение")

        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
            if user is None:
                user = User(telegram_id=telegram_id, status="active")
                session.add(user)
                session.flush()

            ticket = SupportTicket(
                user_id=user.id,
                telegram_id=telegram_id,
                category=category,
                message=text,
                status="open",
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            return ticket

    def create_ticket_for_user_id(
        self,
        user_id: int,
        message: str,
        category: str | None = None,
    ) -> SupportTicket:
        text = message.strip()
        if not text:
            raise ValueError("Пустое сообщение")

        with self._session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            ticket = SupportTicket(
                user_id=user.id,
                telegram_id=user.telegram_id,
                category=category,
                message=text,
                status="open",
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            return ticket

    def list_tickets_for_user(self, user_id: int, limit: int = 20) -> list[SupportTicket]:
        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(SupportTicket)
                    .where(SupportTicket.user_id == user_id)
                    .order_by(SupportTicket.created_at.desc())
                    .limit(limit)
                ).all()
            )

    def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        with self._session_factory() as session:
            return session.get(SupportTicket, ticket_id)

    def reply_to_ticket(self, ticket_id: int, reply: str) -> SupportTicket:
        text = reply.strip()
        if not text:
            raise ValueError("Пустой ответ")

        with self._session_factory() as session:
            ticket = session.get(SupportTicket, ticket_id)
            if ticket is None:
                raise ValueError("Обращение не найдено")

            ticket.admin_reply = text
            ticket.replied_at = datetime.now(UTC)
            ticket.status = "closed"
            session.commit()
            session.refresh(ticket)
            return ticket
