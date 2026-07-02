from fastapi import Request
from fastapi.templating import Jinja2Templates

from webapp.deps import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def ctx(request: Request, **extra):
    settings = request.app.state.settings
    bot_username = settings.telegram_bot_username.strip()
    bot_url = f"https://t.me/{bot_username}" if bot_username else ""
    data = {
        "request": request,
        "service_name": settings.service_name,
        "user_id": request.session.get("user_id"),
        "admin_id": request.session.get("admin_id"),
        "bot_url": bot_url,
        "support_contact": settings.support_contact,
        "company_email": settings.company_email,
        "ai_free_daily_limit": settings.ai_free_daily_limit,
    }
    data.update(extra)
    return data
