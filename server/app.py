# server/app.py
# OpenEnv requires this entry point at server/app.py
# Re-exports the FastAPI app from main.py

from server.main import app  # noqa: F401

__all__ = ["app"]