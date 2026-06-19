from pathlib import Path


class GeoCountryResolver:
    def __init__(self, database_path: str) -> None:
        self._reader = None
        path = database_path.strip()
        if path and Path(path).is_file():
            import geoip2.database

            self._reader = geoip2.database.Reader(path)

    def country_code(self, ip: str) -> str | None:
        if not self._reader:
            return None
        try:
            response = self._reader.country(ip)
            code = response.country.iso_code
            return code.upper() if code else None
        except Exception:
            return None

    def close(self) -> None:
        if self._reader:
            self._reader.close()
