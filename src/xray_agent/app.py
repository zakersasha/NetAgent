from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse

from xray_agent.config_service import XrayConfigService
from xray_agent.stats_service import XrayStatsService
from xray_agent.errors import (
    ConfigError,
    ReservedUserError,
    UserLimitReached,
    UserNotFound,
    XrayAgentError,
    XrayCommandError,
)
from xray_agent.models import AddUserRequest, HealthResponse, RemoveUserRequest, UserOnlineStats, UserResponse
from xray_agent.security import verify_agent_access
from xray_agent.settings import get_settings

settings = get_settings()
service = XrayConfigService(settings)
stats_service = XrayStatsService(settings)

app = FastAPI(title="NetAgent Xray Agent", version="0.1.0")
agent_auth = Depends(verify_agent_access(settings))


@app.exception_handler(XrayAgentError)
async def xray_agent_error_handler(_, exc: XrayAgentError):
    if isinstance(exc, UserLimitReached):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, UserNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ReservedUserError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, (ConfigError, XrayCommandError)):
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(status_code=code, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse, dependencies=[agent_auth])
async def health() -> HealthResponse:
    try:
        service.test_config()
        return HealthResponse(
            ok=True,
            config_path=str(settings.xray_config_path),
            xray_test_ok=True,
            users=service.count_users(),
        )
    except Exception as exc:
        return HealthResponse(
            ok=False,
            config_path=str(settings.xray_config_path),
            xray_test_ok=False,
            error=str(exc),
        )


@app.get("/users", response_model=list[UserResponse], dependencies=[agent_auth])
async def users() -> list[UserResponse]:
    return service.list_users()


@app.get("/users/count", dependencies=[agent_auth])
async def users_count():
    return service.count_users()


@app.get("/stats/users_online", response_model=list[UserOnlineStats], dependencies=[agent_auth])
async def users_online_stats() -> list[UserOnlineStats]:
    return stats_service.get_users_online()


@app.post("/add_user", response_model=UserResponse, dependencies=[agent_auth])
async def add_user(request: AddUserRequest) -> UserResponse:
    return service.add_user(request)


@app.post("/remove_user", response_model=UserResponse, dependencies=[agent_auth])
async def remove_user(request: RemoveUserRequest) -> UserResponse:
    return service.remove_user(request.uuid)
