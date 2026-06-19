import hashlib


def make_device_id(user_id: int, device_slug: str, uuid: str) -> str:
    payload = f"netagent:v1:{user_id}:{device_slug}:{uuid}"
    return hashlib.sha256(payload.encode()).hexdigest()
