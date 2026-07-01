import uvicorn

from webapp.app import create_app
from webapp.settings import get_web_settings


def main() -> None:
    settings = get_web_settings()
    app = create_app()
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
