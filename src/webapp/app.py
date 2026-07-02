from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from webapp.deps import STATIC_DIR, build_billing, build_stats, build_support
from webapp.routes import admin, auth, cabinet, public
from webapp.settings import get_web_settings


def create_app() -> FastAPI:
    settings = get_web_settings()
    app = FastAPI(title=f"{settings.service_name} Web", docs_url=None, redoc_url=None)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="netagent_session",
        max_age=60 * 60 * 24 * 14,
        same_site="lax",
    )

    app.state.settings = settings
    app.state.billing = build_billing(settings)
    app.state.stats = build_stats(settings)
    app.state.support = build_support(settings)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.middleware("http")
    async def inject_globals(request: Request, call_next):
        request.state.settings = settings
        response = await call_next(request)
        return response

    app.include_router(public.router)
    app.include_router(auth.router)
    app.include_router(cabinet.router)
    app.include_router(admin.router)

    return app
