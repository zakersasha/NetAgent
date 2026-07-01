from collections.abc import Callable

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
