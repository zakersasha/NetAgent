from pydantic import BaseModel, Field


class OnlineIpEntry(BaseModel):
    ip: str
    last_seen: int = 0


class UserOnlineStats(BaseModel):
    email: str
    ips: list[OnlineIpEntry] = Field(default_factory=list)


class UserTrafficStats(BaseModel):
    email: str
    uplink_bytes: int = 0
    downlink_bytes: int = 0

    @property
    def total_bytes(self) -> int:
        return self.uplink_bytes + self.downlink_bytes


class AddUserRequest(BaseModel):
    uuid: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    limit: int = Field(..., ge=1, le=3)
    flow: str = "xtls-rprx-vision"


class RemoveUserRequest(BaseModel):
    uuid: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    uuid: str
    email: str | None = None
    limit: int | None = None
    flow: str | None = None
    reserved: bool = False
    connection_uri: str | None = None


class CountResponse(BaseModel):
    total: int
    paying: int
    reserved: int
    max_users: int


class HealthResponse(BaseModel):
    ok: bool
    config_path: str
    xray_test_ok: bool
    users: CountResponse | None = None
    error: str | None = None
