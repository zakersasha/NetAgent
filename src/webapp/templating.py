from fastapi import Request
from fastapi.templating import Jinja2Templates

from netagent_common.plans_display import marketing_for, plan_feature_lines
from webapp.deps import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["marketing_for"] = marketing_for
templates.env.globals["plan_feature_lines"] = plan_feature_lines


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
        "company_email": settings.company_email,
        "ai_free_daily_limit": settings.ai_free_daily_limit,
    }
    data.update(extra)
    return data
