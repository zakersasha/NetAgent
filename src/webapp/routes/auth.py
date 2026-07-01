from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from netagent_db.session import create_session_factory
from webapp.auth import verify_password
from webapp.stats import AdminStatsService
from webapp.templating import ctx, templates
from webapp.users import AuthError, authenticate_user, register_user

router = APIRouter()


def _session_factory(request: Request):
    return create_session_factory(request.app.state.settings.database_url)


@router.get("/register")
async def register_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/cabinet", status_code=303)
    return templates.TemplateResponse("register.html", ctx(request))


@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    session_factory = _session_factory(request)
    with session_factory() as session:
        try:
            user = register_user(session, email, password)
        except AuthError as exc:
            return templates.TemplateResponse(
                "register.html",
                ctx(request, error=str(exc), email=email),
                status_code=400,
            )
    request.session["user_id"] = user.id
    return RedirectResponse("/cabinet", status_code=303)


@router.get("/login")
async def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/cabinet", status_code=303)
    return templates.TemplateResponse("login.html", ctx(request))


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    session_factory = _session_factory(request)
    with session_factory() as session:
        user = authenticate_user(session, email, password)
        if not user:
            return templates.TemplateResponse(
                "login.html",
                ctx(request, error="Неверный email или пароль", email=email),
                status_code=401,
            )
    request.session["user_id"] = user.id
    request.session.pop("admin_id", None)
    return RedirectResponse("/cabinet", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse("/", status_code=303)


@router.get("/admin/login")
async def admin_login_form(request: Request):
    if request.session.get("admin_id"):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", ctx(request))


@router.post("/admin/login")
async def admin_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    stats: AdminStatsService = request.app.state.stats
    admin = stats.get_admin_by_email(email.strip().lower())
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            ctx(request, error="Неверный логин или пароль", email=email),
            status_code=401,
        )
    request.session["admin_id"] = admin.id
    request.session.pop("user_id", None)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/logout")
async def admin_logout(request: Request):
    request.session.pop("admin_id", None)
    return RedirectResponse("/admin/login", status_code=303)
