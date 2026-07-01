from fastapi import Request
from fastapi.templating import Jinja2Templates

from webapp.deps import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def ctx(request: Request, **extra):
    settings = request.app.state.settings
    data = {
        "request": request,
        "service_name": settings.service_name,
        "user_id": request.session.get("user_id"),
        "admin_id": request.session.get("admin_id"),
    }
    data.update(extra)
    return data
