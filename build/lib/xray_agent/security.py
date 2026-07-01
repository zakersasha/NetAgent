from fastapi import Header, HTTPException, Request, status

from xray_agent.settings import AgentSettings


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return None


def verify_agent_access(settings: AgentSettings):
    async def dependency(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        authorization: str | None = Header(default=None),
    ) -> None:
        token = x_api_key
        if not token and authorization and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()

        if token != settings.agent_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        client_ip = _client_ip(request)
        allowed_ips = settings.allowed_ips()
        if allowed_ips and client_ip not in allowed_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"IP is not allowed: {client_ip}",
            )

    return dependency
