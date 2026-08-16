import uvicorn

from .app.config import settings


uvicorn.run("server.app.main:app", host=settings.host, port=settings.port, reload=False)
