from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .config import Settings, assert_secure_binding, load_settings
from .routes import SoundbarBackend, create_router
from .samsung_client import SamsungSoundbarClient


def create_app(settings: Settings | None = None, client: SoundbarBackend | None = None) -> FastAPI:
    settings = settings or load_settings()
    assert_secure_binding(settings)
    client = client or SamsungSoundbarClient(settings)
    app = FastAPI(title="Samsung Soundbar Bridge", version=__version__)
    app.include_router(create_router(settings, client))
    return app


app = create_app()
