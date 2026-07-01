GB = 1024**3


def bytes_to_gb(value: int) -> float:
    return round(value / GB, 2)


def format_traffic(used_bytes: int, limit_gb: int | None) -> str:
    used = bytes_to_gb(used_bytes)
    if limit_gb is None:
        return f"{used} ГБ"
    return f"{used} / {limit_gb} ГБ"
