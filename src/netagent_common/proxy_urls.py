"""Список прокси из env с ротацией и fallback при ошибках."""


class ProxyRotator:
    def __init__(self, urls: tuple[str, ...]) -> None:
        cleaned = tuple(url.strip() for url in urls if url and url.strip())
        self._urls = cleaned
        self._index = 0

    @property
    def urls(self) -> tuple[str, ...]:
        return self._urls

    def next(self) -> str | None:
        if not self._urls:
            return None
        url = self._urls[self._index % len(self._urls)]
        self._index += 1
        return url

    def cycle(self) -> list[str | None]:
        if not self._urls:
            return [None]
        start = self._index % len(self._urls)
        ordered = self._urls[start:] + self._urls[:start]
        self._index += 1
        return list(ordered)


def parse_proxy_urls(*values: str) -> tuple[str, ...]:
    urls: list[str] = []
    for value in values:
        for part in value.split(","):
            stripped = part.strip()
            if stripped:
                urls.append(stripped)
    return tuple(urls)
